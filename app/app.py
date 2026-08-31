from pathlib import Path
import uuid

from flask import Flask, abort, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename
import os

from utils.predictor import PredictionError, predict_image


APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent
UPLOAD_FOLDER = APP_DIR / "static" / "uploads"
ASSETS_FOLDER = BASE_DIR / "assets"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

MANGO_VARIETIES = [
    {
        "slug": "amrapali",
        "name": "Amrapali",
        "image": "Amrapali.jpg",
        "tagline": "A well-known hybrid mango prized for deep orange flesh and sweetness.",
        "guide": "Small to medium fruit with fibreless flesh, rich color, and a noticeably sweet finish.",
        "description": "Amrapali was developed by the Indian Agricultural Research Institute and is widely recognized as a dwarf, high-density planting mango. Horticulture references describe it as a small to medium fruit with deep orange-red flesh, very good eating quality, and a fibreless texture that makes it memorable on the table as well as in processed mango products.",
        "origin": "IARI hybrid of Dashehari x Neelum",
        "season": "Late July",
        "taste": "Very sweet, rich, and aromatic",
        "best_for": "Fresh eating, juice, nectar, and pulp-rich preparations",
        "source_name": "ICAR-IARI mango variety page",
        "source_url": "https://ztmbpd.iari.res.in/technologies/varietieshybrids/fruits/mango/",
    },
    {
        "slug": "fazlee",
        "name": "Fazlee",
        "image": "Fazlee.webp",
        "tagline": "A famously large late-season mango associated with Malda and the Bengal mango trade.",
        "guide": "Big, generous fruit that stands out for size first, then for its mellow sweetness.",
        "description": "Fazlee, more commonly referenced in horticulture sources as Fazli, is one of the large mangoes of the Bengal region and carries a registered GI identity as Malda Fazli Mango in West Bengal. Recent BARI reporting on Fazli also highlights its heavy fruit weight and solid keeping quality, which helps explain why it remains such a recognizable market mango.",
        "origin": "Bengal region, especially Malda",
        "season": "Late season",
        "taste": "Mildly sweet, smooth, and mellow",
        "best_for": "Sharing, slicing, and late-season market fruit",
        "source_name": "APEDA GI listing for Malda Fazli Mango",
        "source_url": "https://apeda.gov.in/West_Bengal",
    },
    {
        "slug": "harivanga",
        "name": "Harivanga",
        "image": "Harivanga.jpg",
        "tagline": "Rangpur's celebrated mango, loved for its fleshiness, sweetness, and small seed.",
        "guide": "A juicy, fibreless mango known for a thin skin, soft bite, and strong local reputation.",
        "description": "Harivanga appears to correspond to the better-known Haribhanga mango of Rangpur, Bangladesh. Reporting that cites Bangladesh's Department of Agricultural Extension describes Haribhanga as fibreless, fleshy, sweet, and thin-skinned, with a smaller seed inside, and the variety has become one of the signature mangoes of northern Bangladesh.",
        "origin": "Rangpur region, Bangladesh",
        "season": "Mid-June through July",
        "taste": "Sweet, juicy, and fragrant",
        "best_for": "Fresh eating and enjoying a classic northern Bangladesh mango",
        "source_name": "BSS report citing the Department of Agricultural Extension",
        "source_url": "https://www.bssnews.net/business/61700",
    },
    {
        "slug": "mollika",
        "name": "Mollika",
        "image": "Mollika.jpg",
        "tagline": "A handsome hybrid mango with apricot-yellow skin and a refined sweet-acid balance.",
        "guide": "Large, fibreless fruit with a smooth bite and the kind of flavor people remember.",
        "description": "Mollika most likely corresponds to the cultivar usually spelled Mallika in Indian horticulture references. ICAR-IARI describes Mallika as a large, fibreless mango with apricot-yellow peel, excellent fruit quality, a distinctive sugar-acid balance, and notably good keeping quality, making it one of the more polished dessert-style mangoes in this set.",
        "origin": "IARI hybrid of Neelum x Dashehari",
        "season": "Late July",
        "taste": "Sweet, balanced, and full flavored",
        "best_for": "Fresh eating, gifting, and table fruit",
        "source_name": "ICAR-IARI mango variety page",
        "source_url": "https://ztmbpd.iari.res.in/technologies/varietieshybrids/fruits/mango/",
    },
    {
        "slug": "nilambori",
        "name": "Nilambori",
        "image": "Nilambori.jpg",
        "tagline": "A bright yellow, flesh-forward mango with a generous edible portion.",
        "guide": "Medium to large fruit that ripens yellow and is remembered for juicy, fibreless flesh.",
        "description": "Nilambori appears in recent Bangladeshi mango reference work as a distinct market variety, where it is described as a medium to large mango with bright yellow ripe skin, deep yellow fibreless flesh, and a sweet edge with a light tang. A Jamalpur genotype study also reported Nilambori among the highest edible-portion cultivars in its trial, which supports its reputation as a rewarding eating mango.",
        "origin": "Bangladeshi market and orchard variety",
        "season": "June to July",
        "taste": "Sweet with a slight tang",
        "best_for": "Fresh eating and comparing color-rich ripe fruit",
        "source_name": "ScienceDirect mango dataset article",
        "source_url": "https://www.sciencedirect.com/science/article/pii/S2352340925002926",
    },
]

VARIETY_LOOKUP = {item["slug"]: item for item in MANGO_VARIETIES}
CLASS_TO_SLUG = {item["name"]: item["slug"] for item in MANGO_VARIETIES}


app = Flask(
    __name__,
    template_folder=str(APP_DIR / "templates"),
    static_folder=str(APP_DIR / "static"),
)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def build_prediction_guidance(confidence_percent: float) -> str:
    if confidence_percent >= 90:
        return "This looks like a strong match. Open the mango guide below and compare the fruit's look, color, and shape."
    if confidence_percent >= 70:
        return "This looks like a good match. A quick comparison with the mango guide can help you confirm it."
    return "This is a possible match. Use the mango guide below to compare the fruit carefully before deciding."


def handle_prediction_request(template_name: str):
    result = None
    error = None

    if request.method == "POST":
        # Support two submission methods:
        # 1) standard multipart file upload (request.files['image'])
        # 2) base64 data URI in form field 'capture_data' (useful for camera captures)

        image_file = None
        saved_path = None

        if "image" in request.files:
            image_file = request.files["image"]

            if not image_file or image_file.filename == "":
                error = "No file was selected. Please choose an image first."
                return render_template(template_name, error=error, result=result)

            if not allowed_file(image_file.filename):
                error = "Invalid file type. Please upload a PNG, JPG, JPEG, or WEBP image."
                return render_template(template_name, error=error, result=result)

            safe_name = secure_filename(image_file.filename)
            unique_name = f"{uuid.uuid4().hex}_{safe_name}"
            saved_path = UPLOAD_FOLDER / unique_name

        elif request.form.get("capture_data"):
            # data URI: "data:image/png;base64,..."
            data_uri = request.form.get("capture_data")
            try:
                header, encoded = data_uri.split(",", 1)
            except Exception:
                header = None
                encoded = None

            if not encoded:
                error = "Invalid captured image data. Please try again."
                return render_template(template_name, error=error, result=result)

            import base64

            try:
                decoded = base64.b64decode(encoded)
            except Exception:
                error = "Captured image data is corrupted. Please try again."
                return render_template(template_name, error=error, result=result)

            unique_name = f"{uuid.uuid4().hex}_capture.png"
            saved_path = UPLOAD_FOLDER / unique_name
            # write file bytes
            with open(saved_path, "wb") as fh:
                fh.write(decoded)

            # construct a safe_name for result display
            safe_name = "capture.png"

        else:
            error = "No file was uploaded. Please choose an image or use the camera and try again."
            return render_template(template_name, error=error, result=result)

        try:
            if image_file:
                image_file.save(saved_path)
            prediction = predict_image(saved_path)
            predicted_class = prediction["predicted_class"]
            variety_slug = CLASS_TO_SLUG.get(predicted_class)
            confidence_percent = prediction["confidence_percent"]
            guide_text = build_prediction_guidance(confidence_percent)

            result = {
                "filename": safe_name,
                "image_url": f"uploads/{unique_name}",
                "predicted_class": predicted_class,
                "confidence": prediction["confidence"],
                "confidence_percent": confidence_percent,
                "guide_text": guide_text,
                "variety_slug": variety_slug,
                "variety_url": url_for("variety_detail", slug=variety_slug) if variety_slug else None,
            }
        except FileNotFoundError:
            error = (
                "Model file not found. Place your Keras model in `models/` as "
                "`mango_classifier.keras` or `best_mango_classifier.keras` and try again."
            )
        except PredictionError as exc:
            error = str(exc)
        except Exception:
            error = "Prediction failed due to an unexpected error. Please try again."

    return render_template(template_name, error=error, result=result)


@app.context_processor
def inject_site_data():
    return {
        "varieties_nav": MANGO_VARIETIES,
        "variety_count": len(MANGO_VARIETIES),
    }


@app.route("/")
def index():
    highlights = MANGO_VARIETIES[:4]
    return render_template("index.html", highlights=highlights)


@app.route("/welcome")
def welcome():
    return render_template("welcome.html")


@app.route("/mango-varieties")
def mango_section():
    return render_template("mango_section.html", varieties=MANGO_VARIETIES)


@app.route("/classify", methods=["GET", "POST"])
def classify_mango():
    return handle_prediction_request("classify_mango.html")


@app.route("/variety/<slug>")
def variety_detail(slug: str):
    variety = VARIETY_LOOKUP.get(slug)
    if not variety:
        abort(404)
    related = [item for item in MANGO_VARIETIES if item["slug"] != slug][:4]
    return render_template("variety_detail.html", variety=variety, related=related)


@app.route("/assets/<path:filename>")
def assets(filename: str):
    return send_from_directory(ASSETS_FOLDER, filename)


if __name__ == "__main__":
    app.run(debug=True)
