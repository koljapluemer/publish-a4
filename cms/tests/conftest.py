import json
from pathlib import Path

import pytest

from cms.config import Settings


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    data = tmp_path / "data"
    site = tmp_path / "site"
    collage = data / "weekly"
    (collage / "cards").mkdir(parents=True)
    (collage / "cards" / "first.html").write_text("<article>First</article>\n")
    (collage / "index.jsonl").write_text(
        json.dumps({"card": "first", "top": 10, "left": 20}) + "\n"
    )
    return Settings(data, site)


@pytest.fixture
def config_path(settings: Settings, tmp_path: Path) -> Path:
    path = tmp_path / "config.yml"
    path.write_text(f"data_dir: {settings.data_dir}\nsite_dir: {settings.site_dir}\n")
    return path
