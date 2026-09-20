from cms.builder import Builder


def test_standalone_build(settings):
    output = Builder(settings).build_collage("weekly")
    html = output.read_text()

    assert ">First</article>" in html
    assert '<article data-card="first" style="top: 10mm; left: 20mm;">' in html
    assert '<div class="card"' not in html
    assert "a4-preview" not in html
    assert (output.parent / "normalize.css").is_file()


def test_editor_build_contains_bridge(settings):
    output = Builder(settings).build_collage("weekly", edit=True)
    assert "a4-preview" in output.read_text()


def test_card_metadata_is_added_to_root_after_embedded_styles(settings):
    cards = settings.data_dir / "weekly" / "cards"
    (cards / "first.html").write_text("<style>.note { color: red; }</style>\n<div>Note</div>\n")

    html = Builder(settings).build_collage("weekly").read_text()

    assert '<style>.note { color: red; }</style>' in html
    assert '<div data-card="first" style="top: 10mm; left: 20mm;">Note</div>' in html


def test_card_placement_is_merged_into_existing_root_style(settings):
    cards = settings.data_dir / "weekly" / "cards"
    (cards / "first.html").write_text('<article style="background: pink">Note</article>\n')

    html = Builder(settings).build_collage("weekly").read_text()

    assert '<article style="top: 10mm; left: 20mm; background: pink" data-card="first">' in html
