import math
from pathlib import Path
from typing import Any

from flask import Flask, Response, jsonify, request, send_from_directory
from werkzeug.exceptions import BadRequest, HTTPException

from .builder import Builder
from .config import DEFAULT_CONFIG, load_settings
from .repository import Repository, RepositoryError


FRONTEND_DIST = Path(__file__).resolve().parent / "frontend" / "dist"
IMAGE_EXTENSIONS = {
    "image/gif": "gif",
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


def _json_body() -> dict[str, Any]:
    value = request.get_json(silent=True)
    if not isinstance(value, dict):
        raise BadRequest("Expected a JSON object.")
    return value


def _string(value: dict[str, Any], key: str) -> str:
    result = value.get(key)
    if not isinstance(result, str):
        raise BadRequest(f"'{key}' must be a string.")
    return result


def _number(value: dict[str, Any], key: str) -> int | float:
    result = value.get(key)
    if isinstance(result, bool) or not isinstance(result, (int, float)):
        raise BadRequest(f"'{key}' must be a number.")
    if not math.isfinite(result):
        raise BadRequest(f"'{key}' must be finite.")
    return result


def _form_number(key: str) -> int | float:
    try:
        result = float(request.form[key])
    except (KeyError, TypeError, ValueError):
        raise BadRequest(f"'{key}' must be a number.") from None
    if not math.isfinite(result):
        raise BadRequest(f"'{key}' must be finite.")
    return result


def create_app(config_path: str | Path = DEFAULT_CONFIG) -> Flask:
    settings = load_settings(Path(config_path))
    repository = Repository(settings)
    builder = Builder(settings, repository)
    app = Flask(__name__, static_folder=None)
    builder.build_all(edit=True)

    @app.errorhandler(RepositoryError)
    def repository_error(error: RepositoryError):
        return jsonify(error={"code": error.code, "message": str(error)}), error.status

    @app.errorhandler(HTTPException)
    def http_error(error: HTTPException):
        return (
            jsonify(
                error={
                    "code": error.name.lower().replace(" ", "_"),
                    "message": error.description,
                }
            ),
            error.code,
        )

    @app.get("/api/collages")
    def list_collages():
        return jsonify(
            collages=[
                {
                    "name": collage,
                    "cards": [card.as_json() for card in repository.list_cards(collage)],
                }
                for collage in repository.list_collages()
            ]
        )

    @app.post("/api/collages")
    def create_collage():
        name = _string(_json_body(), "name")
        repository.create_collage(name)
        builder.build_collage(name, edit=True)
        return jsonify(name=name, cards=[]), 201

    @app.get("/api/collages/<collage>/cards/<card>")
    def get_card(collage: str, card: str):
        return jsonify(repository.get_card(collage, card).as_json())

    @app.post("/api/collages/<collage>/cards")
    def create_card(collage: str):
        body = _json_body()
        card = repository.create_card(
            collage,
            _string(body, "name"),
            _string(body, "source"),
            _number(body, "top"),
            _number(body, "left"),
        )
        builder.build_collage(collage, edit=True)
        return jsonify(card.as_json()), 201

    @app.post("/api/collages/<collage>/image-cards")
    def create_image_card(collage: str):
        image = request.files.get("image")
        if image is None:
            raise BadRequest("'image' must be an uploaded image.")
        extension = IMAGE_EXTENSIONS.get(image.mimetype)
        if extension is None:
            raise BadRequest("Image must be PNG, JPEG, GIF, or WebP.")
        content = image.read()
        if not content:
            raise BadRequest("Image is empty.")

        card = repository.create_image_card(
            collage,
            request.form.get("name", ""),
            content,
            extension,
            _form_number("top"),
            _form_number("left"),
        )
        builder.build_collage(collage, edit=True)
        return jsonify(card.as_json()), 201

    @app.put("/api/collages/<collage>/cards/<card>")
    def update_card(collage: str, card: str):
        updated = repository.update_card(
            collage, card, _string(_json_body(), "source")
        )
        builder.build_collage(collage, edit=True)
        return jsonify(updated.as_json())

    @app.patch("/api/collages/<collage>/cards/<card>/position")
    def update_position(collage: str, card: str):
        body = _json_body()
        updated = repository.update_position(
            collage, card, _number(body, "top"), _number(body, "left")
        )
        builder.build_collage(collage, edit=True)
        return jsonify(updated.as_json())

    @app.delete("/api/collages/<collage>/cards/<card>")
    def delete_card(collage: str, card: str):
        repository.delete_card(collage, card)
        builder.build_collage(collage, edit=True)
        return Response(status=204)

    @app.get("/preview/<collage>/")
    @app.get("/preview/<collage>/<path:filename>")
    def preview(collage: str, filename: str = "index.html"):
        repository.list_cards(collage)
        output_dir = settings.site_dir / collage
        if not (output_dir / "index.html").is_file():
            builder.build_collage(collage, edit=True)
        return send_from_directory(output_dir, filename)

    @app.get("/assets/<path:filename>")
    def frontend_asset(filename: str):
        return send_from_directory(FRONTEND_DIST / "assets", filename)

    @app.get("/")
    def editor():
        index = FRONTEND_DIST / "index.html"
        if not index.is_file():
            return Response(
                "Editor frontend is not built.\n"
                "Run: npm --prefix cms/frontend run build\n",
                status=503,
                content_type="text/plain; charset=utf-8",
            )
        return send_from_directory(FRONTEND_DIST, "index.html")

    return app


def main() -> None:
    app = create_app()
    app.run(port=8000)


if __name__ == "__main__":
    main()
