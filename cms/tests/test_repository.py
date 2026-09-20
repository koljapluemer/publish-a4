import pytest

from cms.repository import CollageConflict, Conflict, InvalidName, NotFound, Repository


def test_create_collage(settings):
    repository = Repository(settings)

    repository.create_collage("new-collage")

    assert repository.list_collages() == ["new-collage", "weekly"]
    assert repository.list_cards("new-collage") == []
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

    assert created.source == '<img src="../assets/photo.png" alt="">\n'
    assert (settings.data_dir / "weekly" / "assets" / "photo.png").read_bytes() == b"image bytes"
