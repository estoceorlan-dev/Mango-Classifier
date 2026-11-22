"""Regenerate the Render inference artifact after changing the Keras model."""
from pathlib import Path

import tensorflow as tf
from tensorflow.python.framework.convert_to_constants import convert_variables_to_constants_v2


if __name__ == "__main__":
    folder = Path(__file__).resolve().parents[1] / "models"
    model = tf.keras.models.load_model(folder / "mango_classifier.keras", compile=False)
    signature = tf.TensorSpec([1, *model.input_shape[1:]], tf.float32)

    @tf.function(input_signature=[signature])
    def classify(image):
        return model(image, training=False)

    frozen = convert_variables_to_constants_v2(classify.get_concrete_function())
    converter = tf.lite.TFLiteConverter.from_concrete_functions([frozen])
    (folder / "mango_classifier.tflite").write_bytes(converter.convert())
