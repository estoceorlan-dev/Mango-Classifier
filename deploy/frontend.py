"""Build the Vercel static frontend from the same routes used by local Flask."""
import os
from pathlib import Path
import shutil
from urllib.parse import urlsplit

from app.app import app, MANGO_VARIETIES


def build():
    origin = os.environ["RENDER_API_ORIGIN"].rstrip("/")
    url = urlsplit(origin)
    if url.scheme != "https" or not url.hostname or url.path or url.query or url.fragment or url.username:
        raise ValueError("Set RENDER_API_ORIGIN to the public HTTPS origin of the Render service.")
    app.config["PREDICTION_ENDPOINT"] = origin + "/predict"
    destination = Path("dist")
    pages = ["/", "/welcome", "/classify", "/mango-varieties"]
    pages.extend("/variety/" + item["slug"] for item in MANGO_VARIETIES)
    with app.test_client() as client:
        for route in pages:
            response = client.get(route)
            if response.status_code != 200:
                raise RuntimeError(f"Could not build {route}")
            page = destination / (route.strip("/") + ".html" if route != "/" else "index.html")
            page.parent.mkdir(parents=True, exist_ok=True)
            page.write_bytes(response.data)
    for folder in ("css", "js", "images"):
        shutil.copytree(Path("app/static") / folder, destination / "static" / folder, dirs_exist_ok=True)
    (destination / "assets/images").mkdir(parents=True, exist_ok=True)
    shutil.copy2("assets/images/background.png", destination / "assets/images")


if __name__ == "__main__":
    build()
