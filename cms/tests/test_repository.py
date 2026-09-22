import pytest

from cms.repository import (
    CollageConflict,
    Conflict,
    InvalidName,
    Metadata,
    NotFound,
    Repository,
    Timestamps,
)


def test_rename_collage(settings):
    repository = Repository(settings)

    assert repository.rename_collage("weekly", "monthly") == "monthly"
    assert repository.list_collages() == ["monthly"]
    assert not (settings.data_dir / "weekly").exists()
    assert repository.get_card("monthly", "first").source == "<article>First</article>\n"

    repository.create_collage("other")
    with pytest.raises(CollageConflict):
        repository.rename_collage("monthly", "other")
    with pytest.raises(InvalidName):
        repository.rename_collage("monthly", "../escape")
    with pytest.raises(NotFound):
        repository.rename_collage("missing", "anything")


def test_create_collage(settings, monkeypatch):
    repository = Repository(settings)
    monkeypatch.setattr(repository, "_timestamp", lambda: "2026-09-22T10:15:30Z")

    repository.create_collage("new-collage")

    assert repository.list_collages() == ["new-collage", "weekly"]
    assert repository.list_cards("new-collage") == []
    assert repository.get_timestamps("new-collage") == Timestamps(
        "2026-09-22T10:15:30Z", "2026-09-22T10:15:30Z"
    )
    assert (settings.data_dir / "new-collage" / "cards").is_dir()

    with pytest.raises(CollageConflict):
        repository.create_collage("new-collage")


def test_card_lifecycle(settings):
    repository = Repository(settings)

    created = repository.create_card(
        "weekly", "second", "<style>.x{}</style><div class=x>Second</div>", 4, 5
    )
    assert created.name == "second"
    assert [card.name for card in repository.list_cards("weekly")] == ["first", "second"]

    updated = repository.update_card("weekly", "second", "<article>Changed</article>")
    assert updated.source == "<article>Changed</article>"
    assert (updated.top, updated.left) == (4, 5)

    moved = repository.update_position("weekly", "second", 12, 13)
    assert (moved.top, moved.left) == (12, 13)
    assert repository.get_card("weekly", "second").source == "<article>Changed</article>"

    repository.delete_card("weekly", "second")
    with pytest.raises(NotFound):
        repository.get_card("weekly", "second")


def test_rejects_duplicate_and_unsafe_names(settings):
    repository = Repository(settings)
    with pytest.raises(Conflict):
        repository.create_card("weekly", "first", "duplicate", 0, 0)
    with pytest.raises(InvalidName):
        repository.get_card("weekly", "../config")


def test_create_image_card(settings):
    repository = Repository(settings)
    created = repository.create_image_card(
        "weekly", "photo", b"image bytes", "png", 3, 4
    )

    assert created.source == '<article><img src="../assets/photo.png" alt=""></article>\n'
    assert (settings.data_dir / "weekly" / "assets" / "photo.png").read_bytes() == b"image bytes"


def test_metadata_persists_alongside_placements(settings):
    repository = Repository(settings)
    index = settings.data_dir / "weekly" / "index.jsonl"
    assert repository.get_metadata("weekly") == Metadata()

    repository.update_metadata("weekly", Metadata("Week 12", True, ("a", "b")))
    assert index.read_text().splitlines()[1] == (
        '{"meta":{"displayTitle":"Week 12","publish":true,"tags":["a","b"]}}'
    )
    assert repository.get_metadata("weekly") == Metadata("Week 12", True, ("a", "b"))

    repository.create_card("weekly", "second", "<div>x</div>", 1, 2)
    repository.update_position("weekly", "first", 3, 4)
    repository.delete_card("weekly", "second")
    assert repository.get_metadata("weekly") == Metadata("Week 12", True, ("a", "b"))
    assert [(c.name, c.top, c.left) for c in repository.list_cards("weekly")] == [("first", 3, 4)]

    repository.update_metadata("weekly", Metadata())
    assert '"meta"' not in index.read_text()


def test_mutations_preserve_created_and_advance_updated(settings, monkeypatch):
    repository = Repository(settings)
    times = iter(
        [
            "2026-09-22T10:00:00Z",
            "2026-09-22T10:01:00Z",
            "2026-09-22T10:02:00Z",
            "2026-09-22T10:03:00Z",
        ]
    )
    monkeypatch.setattr(repository, "_timestamp", lambda: next(times))

    # The fixture represents a legacy collage without timestamps.
    repository.create_card("weekly", "second", "<div>Second</div>", 1, 2)
    assert repository.get_timestamps("weekly") == Timestamps(
        "2026-09-22T10:00:00Z", "2026-09-22T10:00:00Z"
    )

    repository.update_card("weekly", "second", "<div>Updated</div>")
    assert repository.get_timestamps("weekly") == Timestamps(
        "2026-09-22T10:00:00Z", "2026-09-22T10:01:00Z"
    )

    repository.update_metadata("weekly", Metadata("Weekly", False))
    assert repository.get_timestamps("weekly") == Timestamps(
        "2026-09-22T10:00:00Z", "2026-09-22T10:02:00Z"
    )

    repository.rename_collage("weekly", "monthly")
    assert repository.get_timestamps("monthly") == Timestamps(
        "2026-09-22T10:00:00Z", "2026-09-22T10:03:00Z"
    )
