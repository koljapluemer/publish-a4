from io import BytesIO

from cms.app import create_app


def test_crud_api(config_path):
    client = create_app(config_path).test_client()

    response = client.get("/api/collages")
    assert response.status_code == 200
    assert response.json["collages"][0]["name"] == "weekly"

    response = client.post("/api/collages", json={"name": "new-collage"})
    assert response.status_code == 201
    assert response.json == {
        "name": "new-collage",
        "metadata": {"displayTitle": "", "publish": False},
        "cards": [],
    }
    assert client.get("/preview/new-collage/").status_code == 200

    response = client.post(
        "/api/collages/weekly/cards",
        json={"name": "new", "source": "<div>New</div>", "top": 1, "left": 2},
    )
    assert response.status_code == 201
    assert response.json["name"] == "new"

    response = client.put(
        "/api/collages/weekly/cards/new", json={"source": "<div>Updated</div>"}
    )
    assert response.status_code == 200
    assert response.json["source"] == "<div>Updated</div>"

    response = client.patch(
        "/api/collages/weekly/cards/new/position", json={"top": 7, "left": 8}
    )
    assert response.status_code == 200
    assert response.json["top"] == 7

    assert client.delete("/api/collages/weekly/cards/new").status_code == 204
    assert client.get("/api/collages/weekly/cards/new").status_code == 404


def test_api_validation_is_json(config_path):
    client = create_app(config_path).test_client()
    response = client.post(
        "/api/collages/weekly/cards",
        json={"name": "../bad", "source": "x", "top": 0, "left": 0},
    )
    assert response.status_code == 400
    assert response.json["error"]["code"] == "invalid_name"

    response = client.patch(
        "/api/collages/weekly/cards/first/position",
        json={"top": "bad", "left": 0},
    )
    assert response.status_code == 400
    assert response.json["error"]["code"] == "bad_request"


def test_create_image_card_api(config_path, settings):
    client = create_app(config_path).test_client()
    response = client.post(
        "/api/collages/weekly/image-cards",
        data={
            "name": "clipboard-image",
            "top": "15",
            "left": "20",
            "image": (BytesIO(b"png bytes"), "clipboard.png", "image/png"),
        },
    )

    assert response.status_code == 201
    assert response.json["source"] == (
        '<article><img src="../assets/clipboard-image.png" alt=""></article>\n'
    )
    assert (settings.data_dir / "weekly" / "assets" / "clipboard-image.png").read_bytes() == b"png bytes"
    assert (settings.site_dir / "weekly" / "assets" / "clipboard-image.png").read_bytes() == b"png bytes"


def test_metadata_api(config_path, settings):
    client = create_app(config_path).test_client()
    assert client.get("/api/collages").json["collages"][0]["metadata"] == {
        "displayTitle": "",
        "publish": False,
    }

    response = client.put(
        "/api/collages/weekly/metadata",
        json={"displayTitle": "Week 12", "publish": True},
    )
    assert response.status_code == 200
    assert response.json == {"displayTitle": "Week 12", "publish": True}
    assert client.get("/api/collages").json["collages"][0]["metadata"] == response.json

    response = client.put(
        "/api/collages/weekly/metadata", json={"displayTitle": "x", "publish": "yes"}
    )
    assert response.status_code == 400
    assert client.put(
        "/api/collages/missing/metadata", json={"displayTitle": "", "publish": False}
    ).status_code == 404
