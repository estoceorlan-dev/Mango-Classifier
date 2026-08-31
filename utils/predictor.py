from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np


BASE_DIR = Path(__file__).resolve().parent.parent
# Preferred model filenames for deployment.
MODEL_FILENAMES = [
    "mango_classifier.keras",
    "best_mango_classifier.keras",
]

# Update this if your model expects a different input size.
DEFAULT_IMAGE_SIZE = (224, 224)

# Update this placeholder list if you do not want to load class names from JSON files.
CLASS_NAMES = [
    "Amrapali",
    "Fazlee",
    "Harivanga",
    "Mollika",
    "Nilambori",
]


class PredictionError(Exception):
    pass


def _import_keras_modules():
    try:
        from tensorflow.keras.models import load_model
        from tensorflow.keras.preprocessing import image
        from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
    except ModuleNotFoundError as exc:
        raise PredictionError(
            "TensorFlow is not installed. Run `pip install -r requirements.txt` before using predictions."
        ) from exc

    return load_model, image, preprocess_input


def _load_class_names() -> list[str]:
    candidates = [
        BASE_DIR / "notebooks" / "class_indices.json",
        BASE_DIR / "notebooks" / "mango_classifier_labels.json",
    ]

    for candidate in candidates:
        if candidate.exists():
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return [label for label, _ in sorted(data.items(), key=lambda item: item[1])]
                if isinstance(data, list) and data:
                    return [str(item) for item in data]
            except (json.JSONDecodeError, OSError, TypeError, ValueError):
                continue

    return CLASS_NAMES


def _resolve_model_path() -> Path:
    models_dir = BASE_DIR / "models"

    for filename in MODEL_FILENAMES:
        candidate = models_dir / filename
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        "No model file was found in `models/`. Expected one of: "
        + ", ".join(MODEL_FILENAMES)
    )


@lru_cache(maxsize=1)
def get_model():
    load_model, _, _ = _import_keras_modules()
    model_path = _resolve_model_path()
    return load_model(model_path)


@lru_cache(maxsize=1)
def get_image_size() -> tuple[int, int]:
    model = get_model()
    input_shape = getattr(model, "input_shape", None)

    if isinstance(input_shape, list) and input_shape:
        input_shape = input_shape[0]

    if input_shape and len(input_shape) >= 3 and input_shape[1] and input_shape[2]:
        return int(input_shape[1]), int(input_shape[2])

    return DEFAULT_IMAGE_SIZE


def preprocess_image(image_path: str | Path) -> np.ndarray:
    _, image, preprocess_input = _import_keras_modules()
    target_size = get_image_size()
    img = image.load_img(image_path, target_size=target_size)
    img_array = image.img_to_array(img)
    img_array = preprocess_input(img_array)
    return np.expand_dims(img_array, axis=0)


def predict_image(image_path: str | Path) -> dict[str, float | str]:
    try:
        model = get_model()
        class_names = _load_class_names()
        processed_image = preprocess_image(image_path)
        predictions = model.predict(processed_image, verbose=0)

        if predictions.ndim != 2 or predictions.shape[0] == 0:
            raise PredictionError("The model returned an unexpected prediction format.")

        scores = predictions[0]
        predicted_index = int(np.argmax(scores))
        confidence = float(np.max(scores))

        if predicted_index >= len(class_names):
            predicted_class = f"Class {predicted_index}"
        else:
            predicted_class = class_names[predicted_index]

        return {
            "predicted_class": predicted_class,
            "confidence": confidence,
            "confidence_percent": round(confidence * 100, 2),
        }
    except FileNotFoundError:
        raise
    except PredictionError:
        raise
    except Exception as exc:
        raise PredictionError(f"Prediction failed: {exc}") from exc
