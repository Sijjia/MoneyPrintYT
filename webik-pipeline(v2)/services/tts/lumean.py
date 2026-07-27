"""
services/tts/lumean.py
TTS через Lumean (api.lumean.app) — хостовая обёртка над ElevenLabs.

Поток: POST /orders {template_id, input_text} → poll GET /orders/{id} →
POST /storage/url {path} → скачать mp3. Auth: заголовок X-API-KEY.

Отличие от voicer.py: НЕ режем текст руками. Ручная нарезка + склейка pydub
давала швы и дрейф голоса («голос часто меняется» — Айдар). Lumean сам чанкует
(~5000 симв.) и сшивает на сервере с request-stitching → голос стабильнее.
Паузы: [пауза Nс] → SSML <break> (multilingual_v2) или [pause]/… (eleven_v3).
Бонус: alignment-JSON с таймкодами берём из service_files (заменяет whisper).
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Optional

import httpx

from core.config import get_settings
from core.exceptions import APIError, ConfigError
from core.logger import setup_logger

log = setup_logger("lumean-tts")

POLL_INTERVAL_SEC = 3.0
POLL_TIMEOUT_SEC = 1200.0  # длинный ролик может генериться минуты
DONE_STATUSES = {"completed", "partially_completed"}
FAIL_STATUSES = {"failed", "cancelled", "canceled"}

# дефолтные настройки голоса для повествования (стабильность важнее «живости»)
DEFAULT_VOICE_SETTINGS = {
    "stability": 0.55,
    "similarity_boost": 0.8,
    "use_speaker_boost": True,
    "speed": 1.0,
}


class LumeanTTS:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        template_uuid: Optional[str] = None,
        model_id: Optional[str] = None,
        voice_id: Optional[str] = None,
        voice_settings: Optional[dict] = None,
    ):
        s = get_settings()
        self.api_key = api_key or s.lumean_api_key
        if not self.api_key:
            raise ConfigError("LUMEAN_API_KEY не задан в .env")
        self.base_url = (base_url or s.lumean_base_url).rstrip("/")
        self.template_uuid = template_uuid or s.lumean_template_uuid
        self.model_id = model_id or s.lumean_model_id
        self.voice_id = voice_id or s.lumean_voice_id
        self.voice_settings = voice_settings or dict(DEFAULT_VOICE_SETTINGS)
        self.client = httpx.Client(
            timeout=120.0,
            headers={"X-API-KEY": self.api_key, "Content-Type": "application/json"},
        )

    # ── публичное API ────────────────────────────────────────────────
    def synthesize(self, text: str, out_path: Path, save_alignment: bool = True) -> Path:
        """Синтезирует ВЕСЬ текст одним заказом (Lumean чанкует сам). mp3 → out_path."""
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        prepared = self._convert_pauses(text)

        template_id = self._ensure_template()
        order_id = self._create_order(template_id, prepared)
        log.info(f"Lumean заказ {order_id} создан, жду завершения…")
        status, result, items = self._wait(order_id)
        flagged = [it for it in items if it.get("status") in ("policy_flagged", "failed")]
        if flagged:
            log.warning(f"⚠ {len(flagged)} чанк(ов) заблокированы/упали "
                        f"(ElevenLabs модерация?): {[it.get('status') for it in flagged]}")
        self.assemble(result, out_path, save_alignment=save_alignment)
        return out_path

    def generate_sfx(
        self,
        text: str,
        out_path: Path,
        duration_seconds: Optional[float] = None,
        prompt_influence: float = 0.5,
        loop: bool = False,
        output_format: str = "mp3_44100_192",
    ) -> Path:
        """Генерит звуковой эффект по текстовому описанию (ElevenLabs SFX через Lumean).
        Template-less: POST /orders {task_type:sfx, task_data:{...}} → 1 файл.
        text — англ. описание звука; duration 0.5-30с; prompt_influence 0-1.
        """
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        task_data = {
            "text": text,
            "prompt_influence": max(0.0, min(1.0, prompt_influence)),
            "loop": loop,
            "output_format": output_format,
        }
        if duration_seconds:
            task_data["duration_seconds"] = max(0.5, min(30.0, float(duration_seconds)))
        r = self._post("/orders", {"task_type": "sfx", "task_data": task_data})
        oid = (r.get("data") or {}).get("id") or r.get("id")
        if not oid:
            raise APIError("Lumean", f"нет order id для SFX: {r}")
        log.info(f"Lumean SFX заказ {oid}: «{text[:50]}» ({duration_seconds}с)")
        status, result, items = self._wait(oid)
        files = [f for f in ((result or {}).get("files") or [])
                 if str(f).lower().endswith((".mp3", ".wav", ".m4a", ".opus"))]
        if not files:
            raise APIError("Lumean", f"SFX без аудио: status={status} {result}")
        self._download(files[0], out_path)
        log.info(f"SFX готов: {out_path.name} ({out_path.stat().st_size // 1024} KB)")
        return out_path

    def generate_music(
        self,
        prompt: str,
        out_path: Path,
        length_ms: int = 180000,
        force_instrumental: bool = True,
        n_variants: int = 1,
        model_id: str = "music_v2",
    ) -> list[Path]:
        """Генерит музыку по описанию (Lumean music_v2). task_type:music, template-less.
        length_ms 10000-300000 (до 5 мин). Возвращает список путей (по варианту).
        Один вариант → out_path; несколько → out_path с суффиксом _v1/_v2/…
        """
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        task_data = {
            "prompt": prompt,
            "music_length_ms": int(max(10000, min(300000, length_ms))),
            "force_instrumental": force_instrumental,
            "n_variants": max(1, min(4, n_variants)),
            "model_id": model_id,
        }
        r = self._post("/orders", {"task_type": "music", "task_data": task_data})
        oid = (r.get("data") or {}).get("id") or r.get("id")
        if not oid:
            raise APIError("Lumean", f"нет order id для music: {r}")
        log.info(f"Lumean music заказ {oid}: «{prompt[:50]}» ({length_ms/1000:.0f}с ×{n_variants})")
        status, result, items = self._wait(oid)
        files = sorted([f for f in ((result or {}).get("files") or [])
                        if str(f).lower().endswith((".mp3", ".wav", ".m4a", ".opus"))],
                       key=self._chunk_idx)
        if not files:
            raise APIError("Lumean", f"music без аудио: status={status} {result}")
        outs = []
        for i, f in enumerate(files):
            dst = out_path if len(files) == 1 else out_path.with_name(f"{out_path.stem}_v{i+1}{out_path.suffix}")
            self._download(f, dst)
            log.info(f"music готов: {dst.name} ({dst.stat().st_size // 1024} KB)")
            outs.append(dst)
        return outs

    def assemble(self, result: dict, out_path: Path, save_alignment: bool = True) -> Path:
        """Собирает финальный mp3 из результата заказа.
        Lumean отдаёт per-chunk файлы (output/chunks/N/result.mp3) ИЛИ единый
        output/final/result.mp3 при полном успехе. Склеиваем все чанки по порядку.
        """
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        files = [f for f in ((result or {}).get("files") or [])
                 if str(f).lower().endswith((".mp3", ".wav", ".m4a"))]
        if not files:
            raise APIError("Lumean", f"в результате нет аудио: {result}")

        final = [f for f in files if "/final/" in str(f)]
        if final:
            self._download(final[0], out_path)
        else:
            chunks = sorted(files, key=self._chunk_idx)
            log.info(f"склеиваю {len(chunks)} чанков…")
            from pydub import AudioSegment
            import tempfile
            combined = None
            for i, f in enumerate(chunks):
                tmp = Path(tempfile.gettempdir()) / f"_lm_{self._chunk_idx(f)}.mp3"
                self._download(f, tmp)
                seg = AudioSegment.from_file(tmp)
                combined = seg if combined is None else combined.append(seg, crossfade=0)
                tmp.unlink(missing_ok=True)
            combined.export(out_path, format="mp3", bitrate="192k")
        log.info(f"Готово: {out_path.name} ({out_path.stat().st_size // 1024} KB)")

        if save_alignment:
            svc = [f for f in ((result or {}).get("service_files") or [])
                   if str(f).lower().endswith(".json")]
            svc = sorted(svc, key=self._chunk_idx)
            if svc:
                try:
                    self._assemble_alignment(svc, out_path.with_suffix(".align.json"))
                except Exception as e:
                    log.warning(f"alignment не собрался: {e}")
        return out_path

    @staticmethod
    def _chunk_idx(path: str) -> int:
        m = re.search(r"/chunks/(\d+)/", str(path))
        return int(m.group(1)) if m else 0

    def _assemble_alignment(self, json_paths: list[str], out: Path) -> None:
        """Склеивает пословный alignment из per-chunk result.json со сдвигом времени."""
        import tempfile
        words = []
        offset = 0.0
        for f in json_paths:
            tmp = Path(tempfile.gettempdir()) / "_lm_algn.json"
            self._download(f, tmp)
            d = json.loads(tmp.read_text(encoding="utf-8"))
            dur = float(d.get("duration_seconds") or 0.0)
            for w in d.get("words", []):
                words.append({"word": w.get("word"),
                              "start": round(float(w.get("start", 0)) + offset, 3),
                              "end": round(float(w.get("end", 0)) + offset, 3)})
            offset += dur
        out.write_text(json.dumps({"duration_seconds": round(offset, 3), "words": words},
                                  ensure_ascii=False), encoding="utf-8")
        log.info(f"alignment собран: {len(words)} слов, {offset:.1f}с")

    def list_voices(self, search: str = "", page: int = 0, page_size: int = 20) -> list[dict]:
        r = self._get(f"/voices/elevenlabs/library?page={page}&page_size={page_size}"
                      + (f"&search={search}" if search else ""))
        data = r.get("data", r)
        return data.get("voices", []) if isinstance(data, dict) else []

    def get_balance(self) -> dict:
        try:
            return self._get("/usage").get("data", {})
        except Exception:
            return {}

    # ── шаблон ───────────────────────────────────────────────────────
    def _ensure_template(self) -> str:
        if self.template_uuid:
            return self.template_uuid
        if not self.voice_id:
            raise ConfigError("нет LUMEAN_TEMPLATE_UUID и нет LUMEAN_VOICE_ID для создания шаблона")
        tts = {
            "mode": "mode_v1",
            "model_id": self.model_id,
            "voice_id": self.voice_id,
            "language_code": "ru",
            "voice_settings": dict(self.voice_settings),
        }
        if self.model_id == "eleven_v3":
            tts["voice_settings"].pop("similarity_boost", None)
        body = {"service_key": "elevenlabs", "name": "Webik-Lumean-RU",
                "config": {"tts_settings": tts}}
        r = self._post("/templates", body)
        tid = (r.get("data") or {}).get("id") or r.get("id")
        if not tid:
            raise APIError("Lumean", f"не удалось создать шаблон: {r}")
        self.template_uuid = tid
        log.info(f"создан TTS-шаблон {tid} (voice={self.voice_id}, model={self.model_id})")
        # подсказка: сохранить в .env, чтобы не плодить шаблоны
        print(f"[LUMEAN] сохрани в .env → LUMEAN_TEMPLATE_UUID={tid}")
        return tid

    # ── заказ ────────────────────────────────────────────────────────
    def _create_order(self, template_id: str, text: str) -> str:
        r = self._post("/orders", {"template_id": template_id, "input_text": text})
        oid = (r.get("data") or {}).get("id") or r.get("id")
        if not oid:
            raise APIError("Lumean", f"нет order id: {r}")
        return oid

    def _wait(self, order_id: str):
        """→ (status, result_dict, items_list)."""
        t0 = time.monotonic()
        while time.monotonic() - t0 < POLL_TIMEOUT_SEC:
            r = self._get(f"/orders/{order_id}")
            d = r.get("data", r)
            st = (d or {}).get("status", "")
            if st in DONE_STATUSES:
                return st, (d or {}).get("result") or {}, (d or {}).get("items") or []
            if st in FAIL_STATUSES:
                raise APIError("Lumean", f"заказ {order_id} упал: status={st} {d}")
            time.sleep(POLL_INTERVAL_SEC)
        raise APIError("Lumean", f"заказ {order_id} не завершился за {POLL_TIMEOUT_SEC:.0f}с")

    def fetch_order(self, order_id: str):
        """Достаёт готовый заказ (status, result, items) без создания нового."""
        r = self._get(f"/orders/{order_id}")
        d = r.get("data", r)
        return (d or {}).get("status", ""), (d or {}).get("result") or {}, (d or {}).get("items") or []

    def _download(self, storage_path: str, out_path: Path) -> None:
        r = self._post("/storage/url", {"path": storage_path})
        url = (r.get("data") or {}).get("url") or r.get("url")
        if not url:
            raise APIError("Lumean", f"нет signed url для {storage_path}: {r}")
        with self.client.stream("GET", url) as resp:
            resp.raise_for_status()
            with open(out_path, "wb") as f:
                for chunk in resp.iter_bytes(64 * 1024):
                    f.write(chunk)

    # ── паузы ────────────────────────────────────────────────────────
    def _convert_pauses(self, text: str) -> str:
        """[пауза Nс] → нужный синтаксис под модель.
        multilingual_v2/turbo/flash: SSML <break time="Ns"/>.
        eleven_v3: длинная пауза = многоточие/[pause] (SSML break v3 не поддерживает).
        """
        pat = re.compile(r"\[пауза\s+([0-9]+(?:[.,][0-9]+)?)\s*с\]", re.IGNORECASE)
        if self.model_id == "eleven_v3":
            def rep_v3(m):
                sec = float(m.group(1).replace(",", "."))
                # v3: чем длиннее — тем сильнее тег
                return " [long pause] " if sec >= 1.5 else " [pause] "
            return pat.sub(rep_v3, text)

        def rep_v2(m):
            sec = m.group(1).replace(",", ".")
            return f'<break time="{sec}s"/>'
        return pat.sub(rep_v2, text)

    # ── http ─────────────────────────────────────────────────────────
    def _get(self, path: str) -> dict:
        return self._req("GET", path)

    def _post(self, path: str, body: dict) -> dict:
        return self._req("POST", path, body)

    def _req(self, method: str, path: str, body: Optional[dict] = None, attempts: int = 4) -> dict:
        url = f"{self.base_url}{path}"
        last = None
        for i in range(attempts):
            try:
                resp = self.client.request(method, url, json=body)
                if resp.status_code == 429:
                    retry = float(resp.headers.get("Retry-After", 5 * (i + 1)))
                    log.warning(f"429 rate limit, пауза {retry:.0f}с")
                    time.sleep(retry)
                    continue
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as e:
                last = e
                detail = ""
                try:
                    detail = json.dumps(e.response.json(), ensure_ascii=False)[:300]
                except Exception:
                    detail = (e.response.text or "")[:200]
                # 4xx (кроме 429) — не ретраим
                if 400 <= e.response.status_code < 500:
                    raise APIError("Lumean", f"{method} {path} → {e.response.status_code}: {detail}")
                log.warning(f"{method} {path} → {e.response.status_code}, ретрай {i+1}: {detail}")
                time.sleep(2 * (i + 1))
            except httpx.HTTPError as e:
                last = e
                log.warning(f"{method} {path} сеть: {str(e)[:120]}, ретрай {i+1}")
                time.sleep(2 * (i + 1))
        raise APIError("Lumean", f"{method} {path} не удался: {last}")
