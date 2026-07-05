"""
services/tts/voicer.py
Обёртка над Voicer API (voiceapi.csv666.ru) — асинхронный TTS поверх ElevenLabs.

Поток: POST /tasks → polling /tasks/{id}/status → GET /tasks/{id}/result.
Авторизация — заголовок X-API-Key.

Использование:
    tts = VoicerTTS()
    tts.synthesize("Привет, мир", out_path=Path("voice.mp3"))
"""
import re
import time
from pathlib import Path
from typing import Optional

import requests

from core.config import get_settings
from core.exceptions import APIError, ConfigError
from core.logger import setup_logger

log = setup_logger("voicer")

POLL_INTERVAL_SEC = 2.0
POLL_TIMEOUT_SEC = 600
SUCCESS_STATUSES = {"ending_processed", "ending"}
FAILURE_STATUSES = {"error", "error_handled"}
DEFAULT_USER_AGENT = "webik-pipeline/0.1 (+https://youtube.com/@WebikStudio)"
# Микро-кроссфейд на шве между кусками — убирает щелчок, не съедает согласные.
SEAM_CROSSFADE_MS = 40
# Маркер «структурного шва» (граница уровня/крупной паузы). Если он есть в тексте,
# чанкер режет ТОЛЬКО по нему — так шов между TTS-кусками (и неизбежный микро-дрейф
# тембра между запросами ElevenLabs) попадает на вставляемую паузу и не слышен.
SEAM_MARKER = "[[SEAM]]"


class VoicerTTS:
    """Высокоуровневая обёртка для генерации голоса через Voicer.

    Использует заранее сохранённый template (voicer_template_uuid из .env).
    Все параметры голоса (voice_id, stability, style, speed) — внутри template.
    """

    def __init__(
        self,
        template_uuid: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        settings = get_settings()
        self.api_key = api_key or settings.voicer_api_key
        if not self.api_key:
            raise ConfigError("VOICER_API_KEY не задан в .env")
        self.template_uuid = template_uuid or settings.voicer_template_uuid
        if not self.template_uuid:
            raise ConfigError("VOICER_TEMPLATE_UUID не задан в .env")
        self.max_chunk_chars = settings.voicer_max_chunk_chars
        self.base_url = (base_url or settings.voicer_base_url).rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": self.api_key,
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "application/json",
        })

    def synthesize(self, text: str, out_path: Path) -> Path:
        """Сгенерировать mp3 из текста. Возвращает путь к файлу.

        Параметры голоса берутся из шаблона на стороне Voicer.
        Маркеры `[пауза N.Nс]` конвертируются в SSML <break/>.

        Длинный текст (> max_chunk_chars) ElevenLabs дрейфит, а Voicer режет его
        на своей стороне вслепую — шов с резкой сменой тембра попадает посреди фразы.
        Поэтому бьём сами по границам предложений и склеиваем: швы ложатся на паузы
        между фразами, голос (шаблон) тот же.
        """
        out_path.parent.mkdir(parents=True, exist_ok=True)

        chunks = self._split_into_chunks(text, self.max_chunk_chars)

        # Пред-проверка баланса: не начинаем синтез, если средств не хватит на весь
        # текст — иначе сожжём часть кусков и упадём на середине (Voicer при нуле
        # баланса отдаёт битый mp3). Падаем сразу с понятным сообщением.
        need = sum(len(c) for c in chunks)
        try:
            bal = self.get_balance().get("balance")
        except Exception as e:
            bal = None
            log.warning(f"Voicer: не смог проверить баланс ({str(e)[:120]}) — продолжаю")
        if bal is not None and bal < need:
            raise APIError(
                "Voicer",
                f"недостаточно баланса: нужно ~{need} символов, на счету {bal}. "
                f"Пополни баланс Voicer ({self.base_url}) и перезапусти Stage 4."
            )

        if len(chunks) <= 1:
            # chunks[0] уже очищен от SEAM_MARKER; text — нет, поэтому берём chunk.
            return self._synthesize_one(chunks[0] if chunks else text, out_path)

        log.info(
            f"Voicer: текст {len(text)} символов > {self.max_chunk_chars} → "
            f"режу на {len(chunks)} кусков по границам предложений"
        )
        seg_paths = []
        try:
            for i, chunk in enumerate(chunks):
                seg_path = out_path.parent / f"{out_path.stem}_chunk{i:02d}.mp3"
                log.info(f"Voicer: кусок {i + 1}/{len(chunks)} ({len(chunk)} символов)")
                self._synthesize_one(chunk, seg_path)
                seg_paths.append(seg_path)
            self._concat_segments(seg_paths, out_path)
        finally:
            for seg_path in seg_paths:
                seg_path.unlink(missing_ok=True)

        log.info(f"TTS → {out_path} ({out_path.stat().st_size // 1024} KB, {len(chunks)} склеено)")
        return out_path

    def _synthesize_one(self, text: str, out_path: Path, attempts: int = 3) -> Path:
        """Один запрос к Voicer (текст должен влезать в лимит провайдера).

        Скачанный mp3 валидируем: Voicer иногда отдаёт битый/неполный файл, который
        потом роняет склейку (pydub CouldntDecodeError). При невалидном файле —
        перезапрашиваем задачу заново (до `attempts` раз)."""
        prepared_text = self._convert_pause_markers(text)
        last_err = None
        for attempt in range(attempts):
            task_id = self._create_task(prepared_text)
            log.info(f"Voicer: задача {task_id} создана, опрос статуса...")
            self._wait_until_ready(task_id)
            self._download_result(task_id, out_path)
            # Voicer на крупных запросах отдаёт ZIP (0.mp3,1.mp3,…,result.mp3), а не
            # единый mp3. Разворачиваем в result.mp3; если внутри есть .txt — это
            # ошибка политики ElevenLabs (сегмент забанен) → падаем сразу с текстом.
            self._resolve_zip_response(out_path)
            if self._is_valid_mp3(out_path):
                return out_path
            last_err = f"скачанный mp3 не читается (задача {task_id})"
            log.warning(f"Voicer: {last_err} — перезапрашиваю ({attempt + 1}/{attempts})")
        raise APIError("Voicer", f"валидный mp3 не получен за {attempts} попыток: {last_err}")

    @staticmethod
    def _resolve_zip_response(out_path: Path) -> None:
        """Если Voicer вернул ZIP вместо mp3 — развернуть.

        Крупный запрос Voicer дробит на части (0.mp3, 1.mp3, …) и кладёт готовый
        `result.mp3` в ZIP. Если какой-то сегмент забанен политикой ElevenLabs, вместо
        `N.mp3` лежит `N.txt` с текстом ошибки — тогда `result.mp3` НЕПОЛНЫЙ, и мы
        падаем сразу с понятным сообщением (ретрай бесполезен — блок детерминирован).
        """
        try:
            with open(out_path, "rb") as f:
                if f.read(2) != b"PK":
                    return  # обычный mp3, не архив
        except OSError:
            return

        import zipfile

        with zipfile.ZipFile(out_path) as z:
            names = z.namelist()
            txt_errors = [n for n in names if n.lower().endswith(".txt")]
            if txt_errors:
                blocked = z.read(txt_errors[0]).decode("utf-8", "ignore").strip()
                raise APIError(
                    "Voicer",
                    "ElevenLabs заблокировал сегмент по политике контента. "
                    f"Исправь текст этого места в сценарии:\n{blocked[:500]}"
                )
            if "result.mp3" not in names:
                raise APIError("Voicer", f"ZIP без result.mp3 и без ошибки: {names}")
            data = z.read("result.mp3")

        with open(out_path, "wb") as f:
            f.write(data)

    @staticmethod
    def _is_valid_mp3(path: Path) -> bool:
        """Быстрая проверка, что файл — читаемый mp3 (заголовок ID3 или frame-sync)."""
        try:
            if path.stat().st_size < 2000:
                return False
            with open(path, "rb") as f:
                head = f.read(3)
            return head[:3] == b"ID3" or head[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2")
        except OSError:
            return False

    @classmethod
    def _split_into_chunks(cls, text: str, max_chars: int) -> list:
        """Разбить текст на куски ≤ max_chars для отдельных запросов к Voicer.

        Приоритет — СТРУКТУРНЫЕ швы (SEAM_MARKER, границы уровней): режем только по
        ним, жадно пакуя блоки, пока влезает. Тогда каждый шов между кусками ложится
        на вставляемую структурную паузу, и микро-дрейф тембра между запросами ElevenLabs
        не слышен. Если маркеров нет — откат на разбивку по границам предложений.
        Блок, который сам крупнее лимита, дорезаем по предложениям (край. случай).
        """
        text = text.strip()
        if not text:
            return []

        if SEAM_MARKER in text:
            blocks = [b.strip() for b in text.split(SEAM_MARKER) if b.strip()]
            chunks = []
            current = ""
            for b in blocks:
                if len(b) > max_chars:
                    # блок уровня сам больше лимита — редкий случай, режем по фразам
                    if current:
                        chunks.append(current)
                        current = ""
                    chunks.extend(cls._sentence_pack(b, max_chars))
                elif current and len(current) + 1 + len(b) > max_chars:
                    chunks.append(current)
                    current = b
                else:
                    current = f"{current} {b}".strip()
            if current:
                chunks.append(current)
            return chunks

        if len(text) <= max_chars:
            return [text]
        return cls._sentence_pack(text, max_chars)

    @staticmethod
    def _sentence_pack(text: str, max_chars: int) -> list:
        """Жадно пакует целые предложения (граница — . ! ? …) в куски ≤ max_chars.
        Швы совпадают с концом фразы → естественная пауза."""
        sentences = re.split(r"(?<=[.!?…])\s+", text.strip())
        chunks = []
        current = ""
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            if current and len(current) + 1 + len(sent) > max_chars:
                chunks.append(current)
                current = sent
            else:
                current = f"{current} {sent}".strip()
        if current:
            chunks.append(current)
        return chunks

    @staticmethod
    def _concat_segments(seg_paths: list, out_path: Path) -> None:
        """Склеить mp3-куски в один файл с микро-кроссфейдом на швах."""
        try:
            from pydub import AudioSegment
        except ImportError as e:
            raise APIError("Voicer", f"pydub нужен для склейки кусков TTS: {e}")

        combined = None
        for seg_path in seg_paths:
            seg = AudioSegment.from_file(seg_path)
            if combined is None:
                combined = seg
            else:
                xfade = min(SEAM_CROSSFADE_MS, len(combined), len(seg))
                combined = combined.append(seg, crossfade=xfade)
        combined.export(out_path, format="mp3", bitrate="128k")

    def _create_task(self, text: str) -> int:
        body = {"text": text, "template_uuid": self.template_uuid}
        try:
            r = self.session.post(f"{self.base_url}/tasks", json=body, timeout=30)
        except requests.RequestException as e:
            raise APIError("Voicer", f"POST /tasks failed: {e}")
        if r.status_code != 200:
            raise APIError("Voicer", f"POST /tasks → {r.status_code}: {r.text[:500]}")
        data = r.json()
        task_id = data.get("task_id")
        if task_id is None:
            raise APIError("Voicer", f"POST /tasks: нет task_id в ответе: {data}")
        return int(task_id)

    def _wait_until_ready(self, task_id: int) -> None:
        deadline = time.monotonic() + POLL_TIMEOUT_SEC
        last_status = None
        while time.monotonic() < deadline:
            try:
                r = self.session.get(f"{self.base_url}/tasks/{task_id}/status", timeout=15)
            except requests.RequestException as e:
                raise APIError("Voicer", f"GET status failed: {e}")
            if r.status_code != 200:
                raise APIError("Voicer", f"GET status → {r.status_code}: {r.text[:500]}")
            data = r.json()
            status = data.get("status")
            if status != last_status:
                log.info(f"Voicer task {task_id}: {status} ({data.get('status_label', '')})")
                last_status = status
            if status in SUCCESS_STATUSES:
                return
            if status in FAILURE_STATUSES:
                raise APIError("Voicer", f"task {task_id} failed: {data}")
            time.sleep(POLL_INTERVAL_SEC)
        raise APIError("Voicer", f"task {task_id} не завершилась за {POLL_TIMEOUT_SEC}s")

    def _download_result(self, task_id: int, out_path: Path) -> None:
        try:
            r = self.session.get(
                f"{self.base_url}/tasks/{task_id}/result", timeout=120, stream=True
            )
        except requests.RequestException as e:
            raise APIError("Voicer", f"GET result failed: {e}")
        if r.status_code == 202:
            raise APIError("Voicer", f"task {task_id} ещё не готова (202)")
        if r.status_code != 200:
            raise APIError("Voicer", f"GET result → {r.status_code}: {r.text[:500]}")
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=64 * 1024):
                if chunk:
                    f.write(chunk)

    def get_balance(self) -> dict:
        """Полезно для doctor — проверить ключ + остаток символов."""
        r = self.session.get(f"{self.base_url}/balance", timeout=15)
        if r.status_code != 200:
            raise APIError("Voicer", f"GET /balance → {r.status_code}: {r.text[:300]}")
        return r.json()

    @staticmethod
    def _convert_pause_markers(text: str) -> str:
        """[пауза 1.5с] → <break time="1.5s"/> (eleven_multilingual_v2 SSML)."""
        def replace(match):
            seconds = match.group(1).replace(",", ".")
            return f'<break time="{seconds}s"/>'

        return re.sub(r"\[пауза\s+([0-9.,]+)\s*с\]", replace, text)
