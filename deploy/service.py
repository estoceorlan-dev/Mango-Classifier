from functools import lru_cache
from pathlib import Path

import numpy as np
import psycopg
from ai_edge_litert.interpreter import Interpreter
from flask import Flask, request
from PIL import Image, UnidentifiedImageError

from app.app import CLASS_TO_SLUG, build_prediction_guidance
from deploy.database import connect
from utils.predictor import _load_class_names


api = Flask(__name__, static_folder=None)
api.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024 + 65536
MODEL = Path(__file__).resolve().parents[1] / "models" / "mango_classifier.tflite"


@lru_cache(maxsize=1)
def interpreter():
    model = Interpreter(model_path=str(MODEL), num_threads=1)
    model.allocate_tensors()
    return model


@api.after_request
def allow_public_frontend(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Cache-Control"] = "no-store"
    return response


@api.get("/health")
def health():
    return {"status": "ok"}


@api.errorhandler(413)
def too_large(_error):
    return {"error": "Choose an image under 10 MB."}, 413


@api.post("/predict")
def predict():
    upload = request.files.get("image")
    if not upload:
        return {"error": "Choose a mango photo."}, 400
    if upload.stream.seek(0, 2) > 10 * 1024 * 1024:
        return too_large(None)
    upload.stream.seek(0)
    model = interpreter()
    tensor = model.get_input_details()[0]
    _, height, width, _ = tensor["shape"]
    try:
        with Image.open(upload.stream, formats=["JPEG", "PNG", "WEBP"]) as photo:
            if photo.width * photo.height > 20_000_000:
                return {"error": "Resize this photo to 20 megapixels or less."}, 413
            pixels = photo.convert("RGB").resize((width, height), Image.Resampling.NEAREST)
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError):
        return {"error": "Choose a readable JPG, PNG, or WebP photo."}, 400
    batch = np.asarray(pixels, dtype=np.float32)[None, ...] / 127.5 - 1
    model.set_tensor(tensor["index"], batch)
    model.invoke()
    scores = model.get_tensor(model.get_output_details()[0]["index"])[0]
    index = int(np.argmax(scores))
    variety = _load_class_names()[index]
    confidence = float(scores[index])
    try:
        with connect() as conn:
            conn.execute("INSERT INTO mango_predictions (variety, confidence) VALUES (%s, %s)",
                         (variety, confidence))
    except psycopg.Error:
        return {"error": "The database is unavailable. Try again shortly."}, 503
    percent = round(confidence * 100, 2)
    return {"variety": variety, "slug": CLASS_TO_SLUG[variety], "confidence_percent": percent,
            "guidance": build_prediction_guidance(percent)}
