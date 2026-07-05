"""
webik.py - главный CLI пайплайна.

Использование:
    python webik.py new "Айсберг Эпштейна"
    python webik.py status
    python webik.py run-stage 4 --project epstein
    python webik.py approve --project epstein
    python webik.py revise --project epstein --feedback "Усиль хук"
    python webik.py doctor
"""
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from core.config import get_settings
from core.logger import setup_logger
from core.state import Stage, StateManager, StageStatus

app = typer.Typer(help="Webik Pipeline — автоматизация YouTube-айсбергов")
console = Console()
log = setup_logger("webik-cli")


def _slugify(text: str) -> str:
    """Превращает русский текст в slug для project_id."""
    import re
    translit = {
        'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z',
        'и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r',
        'с':'s','т':'t','у':'u','ф':'f','х':'h','ц':'ts','ч':'ch','ш':'sh','щ':'sch',
        'ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya',
    }
    text = text.lower()
    result = ''.join(translit.get(c, c) for c in text)
    result = re.sub(r'[^a-z0-9]+', '-', result).strip('-')
    return result[:60]


@app.command()
def new(
    idea: str = typer.Argument(..., help="Идея для айсберга"),
    duration: int = typer.Option(15, help="Целевая длительность в минутах"),
    levels: int = typer.Option(4, help="Сколько уровней айсберга (2-4)"),
    preset: Optional[str] = typer.Option(None, help="Принудительный пресет"),
    auto_run: bool = typer.Option(False, help="Запустить Stage 1 сразу"),
):
    """Создать новый проект."""
    settings = get_settings()

    # Project ID
    timestamp = datetime.now().strftime("%Y-%m-%d")
    project_id = f"{timestamp}_{_slugify(idea)}"

    project_dir = settings.projects_dir / project_id

    if project_dir.exists():
        console.print(f"[red]Проект {project_id} уже существует[/]")
        raise typer.Exit(1)

    # Создаём
    manager = StateManager.create_new(settings.projects_dir, project_id, idea)
    state = manager.load()
    state.target_duration_min = duration
    state.levels_count = levels
    if preset:
        state.preset = preset
    manager.save(state)

    # Сохраняем входные параметры
    (project_dir / "input.txt").write_text(
        f"idea: {idea}\nduration: {duration}\nlevels: {levels}\npreset: {preset or 'auto'}\n",
        encoding="utf-8"
    )

    console.print(f"[green]✓[/] Создан проект: [bold]{project_id}[/]")
    console.print(f"  Папка: {project_dir}")

    if auto_run:
        from stages import stage_01_concept
        stage_01_concept.run(project_dir, idea, duration, preset, levels=levels)


@app.command()
def status():
    """Статус всех проектов."""
    settings = get_settings()
    projects_dir = settings.projects_dir

    if not projects_dir.exists():
        console.print("[yellow]Нет проектов[/]")
        return

    table = Table(title="Webik Projects")
    table.add_column("Project ID", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Stage", justify="center")
    table.add_column("Status", style="yellow")
    table.add_column("Cost", justify="right", style="green")

    for project_dir in sorted(projects_dir.iterdir(), reverse=True):
        if not project_dir.is_dir():
            continue
        try:
            manager = StateManager(project_dir)
            if not manager.exists():
                continue
            state = manager.load()
            stage_name = Stage(state.current_stage).name
            stage_status = state.stages_status.get(state.current_stage.value, "—")
            table.add_row(
                state.project_id,
                state.title[:40],
                f"{state.current_stage.value}/7 ({stage_name})",
                str(stage_status),
                f"${state.total_cost_usd:.2f}",
            )
        except Exception as e:
            log.warning(f"Ошибка чтения {project_dir}: {e}")

    console.print(table)


@app.command(name="run-stage")
def run_stage(
    stage_num: int = typer.Argument(..., help="Номер этапа (1-7)"),
    project: str = typer.Option(..., help="Project ID"),
    feedback: Optional[str] = typer.Option(None, help="Фидбек на переделку"),
):
    """Запустить конкретный этап."""
    settings = get_settings()
    project_dir = settings.projects_dir / project

    if not project_dir.exists():
        console.print(f"[red]Проект не найден: {project}[/]")
        raise typer.Exit(1)

    manager = StateManager(project_dir)
    state = manager.load()

    if stage_num == 1:
        from stages import stage_01_concept
        stage_01_concept.run(
            project_dir,
            state.title,
            state.target_duration_min,
            state.preset,
            feedback,
            levels=state.levels_count,
        )
    elif stage_num == 2:
        from stages import stage_02_script
        stage_02_script.run(project_dir, feedback)
    elif stage_num == 3:
        from stages import stage_03_scenes
        stage_03_scenes.run(project_dir, feedback)
    elif stage_num == 4:
        from stages import stage_04_assets
        stage_04_assets.run(project_dir, feedback)
    elif stage_num == 5:
        # ⛔ ПРОЦЕДУРНЫЙ stage_05_assemble — ТУПИКОВЫЙ ПУТЬ (строит таймлайн с нуля,
        # старые Impact-карточки, дох на ~40 клипах). НЕ использовать для сборки!
        # ЕДИНСТВЕННЫЙ рабочий путь сборки = TEMPLATE-BASED:
        #   tests/assemble_religioznyj.py  (копия шаблона Апокалипсиса + подмена медиа)
        console.print("[red]⛔ Stage 5 через webik.py ОТКЛЮЧЁН (процедурный путь — тупик).[/]")
        console.print("[yellow]Сборка = template-based. Запусти:[/]")
        console.print("  PYTHONUTF8=1 MINI_LIMIT_LEVEL=1 <venv>/python.exe tests/assemble_religioznyj.py")
        console.print("  (MINI_LIMIT_LEVEL=1 — мини интро+L1; =-1 — полный ролик)")
        raise typer.Exit(1)
    elif stage_num == 6:
        console.print("[yellow]Stage 6 (экспорт) ещё в разработке[/]")
    elif stage_num == 7:
        console.print("[yellow]Stage 7 (загрузка) ещё в разработке[/]")
    else:
        console.print(f"[red]Неверный номер этапа: {stage_num}. Должен быть 1-7[/]")
        raise typer.Exit(1)


@app.command()
def approve(project: str = typer.Option(..., help="Project ID")):
    """Одобрить текущий этап и перейти к следующему."""
    settings = get_settings()
    project_dir = settings.projects_dir / project

    manager = StateManager(project_dir)
    state = manager.load()
    current = state.current_stage
    state.mark_approved(current)
    manager.save(state)

    console.print(f"[green]✓[/] Stage {current.value} одобрен")
    console.print(f"  Следующий: Stage {current.value + 1 if current.value < 7 else '— готово'}")


@app.command()
def revise(
    project: str = typer.Option(..., help="Project ID"),
    feedback: str = typer.Option(..., help="Фидбек для переделки"),
):
    """Переделать текущий этап с фидбеком."""
    settings = get_settings()
    project_dir = settings.projects_dir / project

    manager = StateManager(project_dir)
    state = manager.load()
    current = state.current_stage
    state.add_feedback(current, feedback)
    manager.save(state)

    console.print(f"[yellow]🔄 Перезапускаю Stage {current.value} с фидбеком[/]")

    # Перезапускаем
    run_stage(current.value, project=project, feedback=feedback)


@app.command(name="resume")
def resume_cmd(project: str = typer.Option(..., help="Project ID")):
    """Продолжить с следующего pending этапа."""
    settings = get_settings()
    project_dir = settings.projects_dir / project

    manager = StateManager(project_dir)
    state = manager.load()

    next_stage = state.next_pending_stage()
    if not next_stage:
        console.print("[green]Все этапы завершены[/]")
        return

    console.print(f"Продолжаю с Stage {next_stage.value}")
    run_stage(next_stage.value, project=project)


@app.command()
def doctor():
    """Проверка готовности системы."""
    console.print("[bold cyan]🩺 Webik Doctor[/]\n")

    checks = []

    # 1. Anthropic key
    try:
        settings = get_settings()
        if settings.anthropic_api_key and settings.anthropic_api_key.startswith("sk-ant-"):
            checks.append(("Anthropic API key", True, ""))
        else:
            checks.append(("Anthropic API key", False, "Невалидный или пустой"))
    except Exception as e:
        checks.append(("Anthropic API key", False, str(e)))

    # 2. Voicer (TTS)
    if settings.voicer_api_key and settings.voicer_template_uuid:
        checks.append(("Voicer API key + template", True, ""))
    elif settings.voicer_api_key:
        checks.append(("Voicer API key", True, "Но не задан VOICER_TEMPLATE_UUID"))
    else:
        checks.append(("Voicer API key", False, "Не задан (нужен для stage 4)"))

    # 3. Папки
    for name, path in [
        ("presets/", settings.presets_dir),
        ("templates/", settings.templates_dir),
        ("luts/", settings.luts_dir),
        ("prompts/", settings.prompts_dir),
    ]:
        exists = Path(path).exists()
        checks.append((f"Folder {name}", exists, "" if exists else f"Не найдена: {path}"))

    # 4. Промт-шаблоны
    for prompt in ["concept.txt", "script.txt", "scenes.txt"]:
        p = settings.prompts_dir / prompt
        checks.append((f"Prompt {prompt}", p.exists(), ""))

    # 5. Пресеты
    for preset in ["mystic.json", "archive.json", "cipher.json", "cosmic.json", "shadow.json"]:
        p = settings.presets_dir / preset
        checks.append((f"Preset {preset}", p.exists(), ""))

    # 6. FFmpeg
    import shutil
    ffmpeg = shutil.which("ffmpeg")
    checks.append(("FFmpeg в PATH", ffmpeg is not None, "" if ffmpeg else "Установи ffmpeg"))

    # Вывод
    table = Table()
    table.add_column("Проверка")
    table.add_column("Статус", justify="center")
    table.add_column("Примечание")

    for name, ok, note in checks:
        icon = "[green]✓[/]" if ok else "[red]✗[/]"
        table.add_row(name, icon, note)

    console.print(table)

    failed = sum(1 for _, ok, _ in checks if not ok)
    if failed:
        console.print(f"\n[yellow]⚠ Не пройдено: {failed} проверок[/]")
    else:
        console.print("\n[green]✓ Все проверки пройдены![/]")


@app.command()
def list_projects():
    """Список всех проектов (псевдоним для status)."""
    status()


@app.command()
def index(
    root: str = typer.Option(
        r"E:\YouTube Webik",
        help="Корневая папка для сканирования (рекурсивно)",
    ),
    subdir_filter: str = typer.Option(
        "медиа",
        help="Индексировать только файлы внутри подпапок с этим именем. Пустая строка → все файлы.",
    ),
):
    """Индексировать старую медиатеку через CLIP (один раз ~5 минут на CPU)."""
    from services.media_kit.indexer import MediaIndexer

    settings = get_settings()
    index_dir = Path(__file__).parent / ".media_index"
    indexer = MediaIndexer(index_dir=index_dir)

    root_path = Path(root)
    if not root_path.exists():
        console.print(f"[red]Не найдена папка: {root_path}[/]")
        raise typer.Exit(1)

    new, skipped = indexer.index_root(
        root_path,
        subdir_filter=subdir_filter or None,
    )
    console.print(
        f"[green]✓[/] Индексирование готово: новых {new}, пропущено {skipped}, "
        f"всего в индексе {len(indexer.embeds)}"
    )
    indexer.close()


@app.command()
def search(
    query: str = typer.Argument(..., help="Текстовый запрос на английском"),
    k: int = typer.Option(5, help="Сколько top-K результатов"),
    min_score: float = typer.Option(0.20, help="Минимальная cosine similarity"),
    kind: str = typer.Option("any", help="any | image | video"),
):
    """Семантический поиск по CLIP-индексу старой медиатеки."""
    from services.media_kit.search import MediaSearch

    index_dir = Path(__file__).parent / ".media_index"
    s = MediaSearch(index_dir=index_dir)
    results = s.search(query, k=k, min_score=min_score, kind_filter=kind)
    if not results:
        console.print(f"[yellow]По '{query}' ничего не найдено (min_score={min_score})[/]")
        return

    table = Table(title=f"CLIP search: '{query}'")
    table.add_column("#", justify="right", style="dim")
    table.add_column("Score", justify="right", style="green")
    table.add_column("Kind", style="cyan")
    table.add_column("Path", style="white", overflow="fold")
    for i, (path, score, k_kind) in enumerate(results, 1):
        table.add_row(str(i), f"{score:.3f}", k_kind, path)
    console.print(table)


@app.command()
def demo(
    skip_assets: bool = typer.Option(False, "--skip-assets", help="Не пере-генерировать ассеты"),
    skip_assemble: bool = typer.Option(False, "--skip-assemble", help="Не открывать Premiere"),
):
    """Вертикальный срез: stages 4+5 на 3 готовых сценах.

    Использует tests/fixtures/demo_scenes.json (без stages 1-3, без Anthropic).
    Требует ELEVENLABS_API_KEY + ELEVENLABS_VOICE_ID + PEXELS_API_KEY в .env.

    Premiere должен быть запущен ДО запуска команды.
    """
    import shutil
    settings = get_settings()
    fixture = Path(__file__).parent / "tests" / "fixtures" / "demo_scenes.json"
    if not fixture.exists():
        console.print(f"[red]Не найден фикстура: {fixture}[/]")
        raise typer.Exit(1)

    project_id = "demo-vertical-slice"
    project_dir = settings.projects_dir / project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    manager = StateManager(project_dir)
    if not manager.exists():
        manager = StateManager.create_new(settings.projects_dir, project_id, "Demo: вертикальный срез C")

    # Копируем фикстуру как scenes.json
    scenes_dst = project_dir / "scenes.json"
    shutil.copy2(fixture, scenes_dst)
    console.print(f"[cyan]Demo project: {project_dir}[/]")

    if not skip_assets:
        console.print("\n[bold]── Stage 4 ─────────────────[/]")
        from stages import stage_04_assets
        stage_04_assets.run(project_dir)
    else:
        console.print("[yellow]Stage 4 пропущен (--skip-assets)[/]")

    if not skip_assemble:
        console.print("\n[bold]── Stage 5 ─────────────────[/]")
        # Сборка = template-based (tests/assemble_religioznyj.py), НЕ процедурный stage_05.
        console.print("[yellow]Сборка вручную: tests/assemble_religioznyj.py (template-based).[/]")
    else:
        console.print("[yellow]Stage 5 пропущен (--skip-assemble)[/]")

    console.print(f"\n[green]✓ Demo завершён[/]")
    console.print(f"  Проект: {project_dir}")
    console.print("  Открой Premiere и посмотри таймлайн 'Webik — demo-vertical-slice'.")


if __name__ == "__main__":
    app()
