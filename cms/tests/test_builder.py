from cms.builder import Builder


def test_standalone_build(settings):
    output = Builder(settings).build_collage("weekly")
    html = output.read_text()

    assert "<article>First</article>" in html
    assert "a4-preview" not in html
    assert (output.parent / "normalize.css").is_file()


def test_editor_build_contains_bridge(settings):
    output = Builder(settings).build_collage("weekly", edit=True)
    assert "a4-preview" in output.read_text()
