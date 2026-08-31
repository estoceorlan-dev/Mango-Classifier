import os
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras import layers, models
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

CONFIG = {
    "dataset_path"  : "dataset/",        
    "model_name"    : "my_classifier",   
    "img_size"      : (128, 128),         
    "batch_size"    : 16,                
    "epochs"        : 20,               
    "learning_rate" : 0.001,            
    "dense_units"   : 128,              
    "dropout_rate"  : 0.3,              
    "fine_tune"     : False,             
    "fine_tune_at"  : 100,               
}

def validate_dataset(path):
    print("\n Validating dataset structure...")

    train_path = os.path.join(path, "train")
    test_path  = os.path.join(path, "test")

    if not os.path.exists(train_path):
        raise FileNotFoundError(f"train folder not found at: {train_path}")
    if not os.path.exists(test_path):
        raise FileNotFoundError(f" test folder not found at: {test_path}")

    train_classes = sorted(os.listdir(train_path))
    test_classes  = sorted(os.listdir(test_path))

    print(f"Train classes found: {train_classes}")
    print(f" Test classes found : {test_classes}")

    if train_classes != test_classes:
        print(" Warning: Train and test class folders don't match!")

    for cls in train_classes:
        count = len(os.listdir(os.path.join(train_path, cls)))
        print(f"   {cls}: {count} images")

    return len(train_classes)

def load_data(config):
    print("\n Loading dataset...")

    train_datagen = ImageDataGenerator(
        rescale=1./255,
        horizontal_flip=True,
        rotation_range=15,         
        zoom_range=0.1,             
        width_shift_range=0.1,     
        height_shift_range=0.1,     
        brightness_range=[0.8, 1.2] 
    )

    test_datagen = ImageDataGenerator(rescale=1./255)

    train_data = train_datagen.flow_from_directory(
        os.path.join(config["dataset_path"], "train"),
        target_size=config["img_size"],
        batch_size=config["batch_size"],
        class_mode="categorical",
        shuffle=True
    )

    test_data = test_datagen.flow_from_directory(
        os.path.join(config["dataset_path"], "test"),
        target_size=config["img_size"],
        batch_size=config["batch_size"],
        class_mode="categorical",
        shuffle=False
    )


    labels_path = f"{config['model_name']}_labels.json"
    with open(labels_path, "w") as f:
        json.dump(train_data.class_indices, f, indent=2)
    print(f"Labels saved to {labels_path}")
    print(f"   Classes: {train_data.class_indices}")

    return train_data, test_data

def build_model(num_classes, config):
    print("\nBuilding model...")

    base_model = tf.keras.applications.MobileNetV2(
        input_shape=(*config["img_size"], 3),
        include_top=False,
        weights="imagenet"
    )

   
    base_model.trainable = False


    if config["fine_tune"]:
        base_model.trainable = True
        for layer in base_model.layers[:config["fine_tune_at"]]:
            layer.trainable = False
        print(f" Fine-tuning enabled from layer {config['fine_tune_at']}")

    model = models.Sequential([
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.Dense(config["dense_units"], activation="relu"),
        layers.Dropout(config["dropout_rate"]),     
        layers.Dense(num_classes, activation="softmax")
    ])

    model.compile(
        optimizer=tf.keras.optimizers.Adam(config["learning_rate"]),
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )

    model.summary()
    return model

def get_callbacks(config):
    return [
        EarlyStopping(
            monitor="val_accuracy",
            patience=5,
            restore_best_weights=True,
            verbose=1
        ),
      
        ModelCheckpoint(
            filepath=f"{config['model_name']}_best.h5",
            monitor="val_accuracy",
            save_best_only=True,
            verbose=1
        ),
        ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=3,
            verbose=1
        )
    ]


def train_model(model, train_data, test_data, config):
    print("\n Training started...")

    history = model.fit(
        train_data,
        epochs=config["epochs"],
        validation_data=test_data,
        callbacks=get_callbacks(config)
    )

    return history

def evaluate_model(model, test_data):
    print("\nEvaluating model...")
    loss, accuracy = model.evaluate(test_data)
    print(f" Test Accuracy : {accuracy * 100:.2f}%")
    print(f"   Test Loss     : {loss:.4f}")

def save_model(model, config):
    print("\nSaving model...")

    h5_path = f"{config['model_name']}.h5"
    model.save(h5_path)
    print(f"Saved H5         → {h5_path}")

  
    saved_path = f"{config['model_name']}_saved"
    model.save(saved_path)
    print(f" Saved SavedModel → {saved_path}/")

    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()
    tflite_path = f"{config['model_name']}.tflite"
    with open(tflite_path, "wb") as f:
        f.write(tflite_model)
    print(f"Saved TFLite     → {tflite_path}")

def predict_image(image_path, model_path, labels_path):

    model = load_model(model_path)
    with open(labels_path, "r") as f:
        class_indices = json.load(f)

    labels = {v: k for k, v in class_indices.items()}

    img = image.load_img(image_path, target_size=(128, 128))
    img_array = image.img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    predictions = model.predict(img_array)[0]
    predicted_class = labels[np.argmax(predictions)]
    confidence = np.max(predictions) * 100

    print(f"\nPrediction: {predicted_class} ({confidence:.2f}% confident)")


    print("\nAll probabilities:")
    for idx, prob in enumerate(predictions):
        print(f"   {labels[idx]}: {prob * 100:.2f}%")

    return predicted_class, confidence

if _name_ == "_main_":
    print("=" * 55)
    print("   Universal Image Classifier — Transfer Learning")
    print("=" * 55)

    num_classes = validate_dataset(CONFIG["dataset_path"])

    train_data, test_data = load_data(CONFIG)

    model = build_model(num_classes, CONFIG)

    history = train_model(model, train_data, test_data, CONFIG)

    evaluate_model(model, test_data)

    save_model(model, CONFIG)

    print("\nDone! Your model is ready.")
    print(f"   Model : {CONFIG['model_name']}.h5")
    print(f"   Labels: {CONFIG['model_name']}_labels.json")