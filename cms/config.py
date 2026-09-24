from dataclasses import dataclass
from pathlib import Path

import yaml


DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config.yml"


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    site_dir: Path
    export_dir: Path


def load_settings(path: Path = DEFAULT_CONFIG) -> Settings:
    """Load paths, resolving relative values from the config file."""
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(
            f"missing {path}; copy config.example.yml to config.yml and edit it"
        )

    values = yaml.safe_load(path.read_text()) or {}
    missing = [key for key in ("data_dir", "site_dir", "export_dir") if key not in values]
    if missing:
        raise ValueError(f"missing config value: {', '.join(missing)}")

    def resolve(value: str) -> Path:
        candidate = Path(value).expanduser()
        if not candidate.is_absolute():
            candidate = path.parent / candidate
        return candidate.resolve()

    return Settings(
        resolve(values["data_dir"]),
        resolve(values["site_dir"]),
        resolve(values["export_dir"]),
    )
