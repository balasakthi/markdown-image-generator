from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TemplateConfig:
    name: str
    template_path: Path
    box_coords: tuple[int, int, int, int]
    font_size: int = 20
