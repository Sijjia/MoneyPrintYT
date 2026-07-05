"""
core/state.py
State Machine для управления прогрессом проекта по 7 этапам.
Сохраняет состояние в projects/<project_id>/state.json.
При сбое можно продолжить с последнего успешного этапа.
"""
import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field


class Stage(int, Enum):
    """Этапы пайплайна."""
    CONCEPT = 1     # Идея → outline.json
    SCRIPT = 2      # Outline → script.md
    SCENES = 3      # Script → scenes.json
    ASSETS = 4      # JSON → ассеты (озвучка, картинки, музыка)
    ASSEMBLE = 5    # Ассеты → .prproj в Premiere
    EXPORT = 6      # Premiere → final.mp4 + thumbnail + metadata
    UPLOAD = 7      # → YouTube unlisted


class StageStatus(str, Enum):
    """Статус этапа."""
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    FAILED = "failed"
    SKIPPED = "skipped"


class ProjectState(BaseModel):
    """Полное состояние проекта."""

    project_id: str
    title: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    current_stage: Stage = Stage.CONCEPT
    stages_status: Dict[int, StageStatus] = Field(default_factory=dict)

    # История фидбеков (на случай /revise)
    feedback_history: list[dict] = Field(default_factory=list)

    # Метаданные проекта
    preset: Optional[str] = None
    target_duration_min: int = 25
    levels_count: int = 4
    notion_page_id: Optional[str] = None  # id страницы сценария в Notion (для перезаписи)
    youtube_url: Optional[str] = None

    # Технические данные
    last_error: Optional[str] = None
    total_cost_usd: float = 0.0

    def mark_running(self, stage: Stage):
        self.current_stage = stage
        self.stages_status[stage.value] = StageStatus.RUNNING
        self.updated_at = datetime.now()
        self.last_error = None

    def mark_awaiting(self, stage: Stage):
        self.stages_status[stage.value] = StageStatus.AWAITING_APPROVAL
        self.updated_at = datetime.now()

    def mark_approved(self, stage: Stage):
        self.stages_status[stage.value] = StageStatus.APPROVED
        self.updated_at = datetime.now()

    def mark_failed(self, stage: Stage, error: str):
        self.stages_status[stage.value] = StageStatus.FAILED
        self.last_error = error
        self.updated_at = datetime.now()

    def add_feedback(self, stage: Stage, feedback: str):
        self.feedback_history.append({
            "stage": stage.value,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat(),
        })

    def get_last_feedback(self, stage: Stage) -> Optional[str]:
        for entry in reversed(self.feedback_history):
            if entry["stage"] == stage.value:
                return entry["feedback"]
        return None

    def is_stage_done(self, stage: Stage) -> bool:
        return self.stages_status.get(stage.value) == StageStatus.APPROVED

    def next_pending_stage(self) -> Optional[Stage]:
        for stage in Stage:
            if not self.is_stage_done(stage):
                return stage
        return None


class StateManager:
    """Управляет загрузкой/сохранением состояния проекта."""

    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.state_file = self.project_dir / "state.json"

    def load(self) -> ProjectState:
        if not self.state_file.exists():
            raise FileNotFoundError(f"State file not found: {self.state_file}")
        data = json.loads(self.state_file.read_text(encoding="utf-8"))
        return ProjectState.model_validate(data)

    def save(self, state: ProjectState):
        self.project_dir.mkdir(parents=True, exist_ok=True)
        state.updated_at = datetime.now()
        self.state_file.write_text(
            state.model_dump_json(indent=2),
            encoding="utf-8",
        )

    def exists(self) -> bool:
        return self.state_file.exists()

    @classmethod
    def create_new(cls, projects_dir: Path, project_id: str, title: str) -> "StateManager":
        project_dir = Path(projects_dir) / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        manager = cls(project_dir)
        if manager.exists():
            raise ValueError(f"Project already exists: {project_id}")

        state = ProjectState(project_id=project_id, title=title)
        manager.save(state)
        return manager
