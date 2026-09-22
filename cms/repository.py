import json
import os
import re
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .config import Settings


NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


class RepositoryError(Exception):
    code = "repository_error"
    status = 400


class InvalidName(RepositoryError):
    code = "invalid_name"


class NotFound(RepositoryError):
    code = "not_found"
    status = 404


class Conflict(RepositoryError):
    code = "card_exists"
    status = 409


class CollageConflict(Conflict):
    code = "collage_exists"


@dataclass(frozen=True)
class Placement:
    name: str
    top: float
    left: float

    def as_json(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Card(Placement):
    source: str


@dataclass(frozen=True)
class Metadata:
    display_title: str = ""
    publish: bool = False
    tags: tuple[str, ...] = ()

    def as_json(self) -> dict:
        return {
            "displayTitle": self.display_title,
            "publish": self.publish,
            "tags": list(self.tags),
        }


@dataclass(frozen=True)
class Timestamps:
    created_at: str
    updated_at: str

    def as_json(self) -> dict:
        return {"createdAt": self.created_at, "updatedAt": self.updated_at}


class Repository:
    def __init__(self, settings: Settings):
        self.settings = settings

    @staticmethod
    def _validate_name(value: str, kind: str) -> str:
        if not isinstance(value, str) or not NAME_PATTERN.fullmatch(value):
            raise InvalidName(
                f"Invalid {kind} name. Use letters, numbers, underscores, and hyphens."
            )
        return value

    def _collage_dir(self, collage: str) -> Path:
        collage = self._validate_name(collage, "collage")
        path = self.settings.data_dir / collage
        if not (path / "index.jsonl").is_file():
            raise NotFound(f"Collage '{collage}' does not exist.")
        return path

    def _card_path(self, collage_dir: Path, card: str) -> Path:
        card = self._validate_name(card, "card")
        return collage_dir / "cards" / f"{card}.html"

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
        try:
            with os.fdopen(fd, "w") as handle:
                handle.write(content)
            os.replace(temporary, path)
        except Exception:
            Path(temporary).unlink(missing_ok=True)
            raise

    @staticmethod
    def _atomic_write_bytes(path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(content)
            os.replace(temporary, path)
        except Exception:
            Path(temporary).unlink(missing_ok=True)
            raise

    def list_collages(self) -> list[str]:
        if not self.settings.data_dir.is_dir():
            return []
        return sorted(
            path.name
            for path in self.settings.data_dir.iterdir()
            if path.is_dir() and (path / "index.jsonl").is_file()
        )

    def create_collage(self, collage: str) -> None:
        collage = self._validate_name(collage, "collage")
        collage_dir = self.settings.data_dir / collage
        if collage_dir.exists():
            raise CollageConflict(f"Collage '{collage}' already exists.")

        collage_dir.mkdir(parents=True)
        try:
            (collage_dir / "cards").mkdir()
            now = self._timestamp()
            self._write_index(collage_dir, Timestamps(now, now), Metadata(), [])
        except Exception:
            (collage_dir / "index.jsonl").unlink(missing_ok=True)
            (collage_dir / "cards").rmdir()
            collage_dir.rmdir()
            raise

    def rename_collage(self, collage: str, new_name: str) -> str:
        collage_dir = self._collage_dir(collage)
        new_name = self._validate_name(new_name, "collage")
        if new_name == collage:
            return collage
        new_dir = self.settings.data_dir / new_name
        if new_dir.exists():
            raise CollageConflict(f"Collage '{new_name}' already exists.")
        self._touch(collage_dir)
        collage_dir.rename(new_dir)
        return new_name

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def _read_index(
        self, collage_dir: Path
    ) -> tuple[Timestamps | None, Metadata, list[Placement]]:
        timestamps = None
        metadata = Metadata()
        placements = []
        for number, line in enumerate(
            (collage_dir / "index.jsonl").read_text().splitlines(), start=1
        ):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
                if "timestamps" in value:
                    timestamps = Timestamps(
                        value["timestamps"]["createdAt"],
                        value["timestamps"]["updatedAt"],
                    )
                elif "meta" in value:
                    metadata = Metadata(
                        value["meta"]["displayTitle"],
                        value["meta"]["publish"],
                        tuple(value["meta"].get("tags", [])),
                    )
                else:
                    placements.append(
                        Placement(value["card"], value["top"], value["left"])
                    )
            except (json.JSONDecodeError, KeyError, TypeError) as error:
                raise ValueError(
                    f"Invalid line in {collage_dir.name}/index.jsonl line {number}"
                ) from error
        return timestamps, metadata, placements

    def _read_placements(self, collage_dir: Path) -> list[Placement]:
        return self._read_index(collage_dir)[2]

    def _write_index(
        self,
        collage_dir: Path,
        timestamps: Timestamps,
        metadata: Metadata,
        placements: list[Placement],
    ) -> None:
        lines = [{"timestamps": timestamps.as_json()}]
        if metadata != Metadata():
            lines.append({"meta": metadata.as_json()})
        lines += [
            {"card": item.name, "top": item.top, "left": item.left}
            for item in placements
        ]
        content = "".join(json.dumps(line, separators=(",", ":")) + "\n" for line in lines)
        self._atomic_write(collage_dir / "index.jsonl", content)

    def _write_placements(self, collage_dir: Path, placements: list[Placement]) -> None:
        timestamps, metadata, _ = self._read_index(collage_dir)
        self._write_index(
            collage_dir, self._updated_timestamps(timestamps), metadata, placements
        )

    def _updated_timestamps(self, timestamps: Timestamps | None) -> Timestamps:
        now = self._timestamp()
        return Timestamps(timestamps.created_at if timestamps else now, now)

    def _touch(self, collage_dir: Path) -> None:
        timestamps, metadata, placements = self._read_index(collage_dir)
        self._write_index(
            collage_dir, self._updated_timestamps(timestamps), metadata, placements
        )

    def get_timestamps(self, collage: str) -> Timestamps | None:
        return self._read_index(self._collage_dir(collage))[0]

    def get_metadata(self, collage: str) -> Metadata:
        return self._read_index(self._collage_dir(collage))[1]

    def update_metadata(self, collage: str, metadata: Metadata) -> Metadata:
        collage_dir = self._collage_dir(collage)
        timestamps, _, placements = self._read_index(collage_dir)
        self._write_index(
            collage_dir, self._updated_timestamps(timestamps), metadata, placements
        )
        return metadata

    def list_cards(self, collage: str) -> list[Placement]:
        return self._read_placements(self._collage_dir(collage))

    def get_card(self, collage: str, card: str) -> Card:
        collage_dir = self._collage_dir(collage)
        card_path = self._card_path(collage_dir, card)
        placement = next(
            (item for item in self._read_placements(collage_dir) if item.name == card),
            None,
        )
        if placement is None or not card_path.is_file():
            raise NotFound(f"Card '{card}' does not exist in '{collage}'.")
        return Card(placement.name, placement.top, placement.left, card_path.read_text())

    def create_card(
        self, collage: str, card: str, source: str, top: float, left: float
    ) -> Card:
        collage_dir = self._collage_dir(collage)
        card_path = self._card_path(collage_dir, card)
        placements = self._read_placements(collage_dir)
        if card_path.exists() or any(item.name == card for item in placements):
            raise Conflict(f"Card '{card}' already exists in '{collage}'.")

        self._atomic_write(card_path, source)
        try:
            placement = Placement(card, top, left)
            self._write_placements(collage_dir, [*placements, placement])
        except Exception:
            card_path.unlink(missing_ok=True)
            raise
        return Card(card, top, left, source)

    def create_image_card(
        self,
        collage: str,
        card: str,
        image: bytes,
        extension: str,
        top: float,
        left: float,
    ) -> Card:
        collage_dir = self._collage_dir(collage)
        card = self._validate_name(card, "card")
        asset_name = f"{card}.{extension}"
        asset_path = collage_dir / "assets" / asset_name
        if asset_path.exists():
            raise Conflict(f"Asset '{asset_name}' already exists in '{collage}'.")

        self._atomic_write_bytes(asset_path, image)
        try:
            return self.create_card(
                collage,
                card,
                f'<article><img src="../assets/{asset_name}" alt=""></article>\n',
                top,
                left,
            )
        except Exception:
            asset_path.unlink(missing_ok=True)
            raise

    def update_card(self, collage: str, card: str, source: str) -> Card:
        current = self.get_card(collage, card)
        collage_dir = self._collage_dir(collage)
        self._atomic_write(self._card_path(collage_dir, card), source)
        self._touch(collage_dir)
        return Card(card, current.top, current.left, source)

    def update_position(
        self, collage: str, card: str, top: float, left: float
    ) -> Placement:
        collage_dir = self._collage_dir(collage)
        self._validate_name(card, "card")
        placements = self._read_placements(collage_dir)
        updated = Placement(card, top, left)
        found = False
        result = []
        for placement in placements:
            if placement.name == card:
                result.append(updated)
                found = True
            else:
                result.append(placement)
        if not found:
            raise NotFound(f"Card '{card}' does not exist in '{collage}'.")
        self._write_placements(collage_dir, result)
        return updated

    def delete_card(self, collage: str, card: str) -> None:
        collage_dir = self._collage_dir(collage)
        card_path = self._card_path(collage_dir, card)
        placements = self._read_placements(collage_dir)
        remaining = [item for item in placements if item.name != card]
        if len(remaining) == len(placements) or not card_path.is_file():
            raise NotFound(f"Card '{card}' does not exist in '{collage}'.")

        original_source = card_path.read_text()
        card_path.unlink()
        try:
            self._write_placements(collage_dir, remaining)
        except Exception:
            self._atomic_write(card_path, original_source)
            raise
