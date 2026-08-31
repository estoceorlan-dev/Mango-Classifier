# Mango Classifier

This project is a computer vision case study that combines a deep learning image classifier with a small educational web application. Its goal is to identify a mango fruit image as one of five known varieties and then help the user compare that prediction against short profile pages for each class.

## Summary

The project started as a transfer learning experiment and evolved into a deployable Flask app. Instead of stopping at notebook-level model training, the implementation connects three practical pieces:

1. A labeled mango image dataset organized into `train/` and `test/` folders.
2. A TensorFlow/Keras classifier trained with MobileNetV2 transfer learning.
3. A Flask front end where users can upload a fruit image, receive a prediction, and browse variety reference pages.

That makes the project more than a pure modeling exercise. It demonstrates an end-to-end workflow from dataset preparation to model packaging to a user-facing inference experience.

## Problem

Mango varieties can look similar to non-experts, especially when images vary in lighting, angle, size, or ripeness. The project addresses a simple but useful question:

**Can a lightweight image classification pipeline distinguish between a small set of mango fruit varieties accurately enough to support an educational or prototype identification tool?**

The five target classes in the current system are:

- `Amrapali`
- `Fazlee`
- `Harivanga`
- `Mollika`
- `Nilambori`

## Dataset

The repository includes a folder-based dataset under [`dataset`](C:/Fruit Mango Classifier/dataset) with separate training and test splits.

Observed class distribution from the project files:

| Split | Classes | Images |
| --- | --- | ---: |
| Train | 5 | 2,469 |
| Test | 5 | 700 |
| Total | 5 | 3,169 |

Per-class counts:

| Class | Train | Test |
| --- | ---: | ---: |
| Amrapali | 492 | 140 |
| Fazlee | 492 | 140 |
| Harivanga | 487 | 140 |
| Mollika | 499 | 140 |
| Nilambori | 499 | 140 |

The data is relatively balanced, which is a good fit for a multi-class classifier and helps reduce bias toward any single class.

## Technical Approach

### 1. Model development

The primary training workflow is documented in [`notebooks/mango_classifier.ipynb`](C:/Fruit Mango Classifier/notebooks/mango_classifier.ipynb). The notebook uses:

- `MobileNetV2` with ImageNet weights as the feature extractor
- Input size of `224 x 224`
- Data augmentation through `ImageDataGenerator`
- A two-stage process:
  - feature extraction with the backbone frozen
  - fine-tuning the last portion of the network

Key notebook settings recovered from the project:

- Batch size: `16`
- Validation split: `0.2`
- Head training epochs: `15`
- Fine-tuning epochs: `10`
- Initial learning rate: `1e-3`
- Fine-tuning learning rate: `1e-5`
- Dropout: `0.3`

The model artifacts in the repository include:

- [`models/mango_classifier.keras`](C:/Fruit Mango Classifier/models/mango_classifier.keras)
- [`notebooks/best_mango_classifier.keras`](C:/Fruit Mango Classifier/notebooks/best_mango_classifier.keras)
- [`notebooks/class_indices.json`](C:/Fruit Mango Classifier/notebooks/class_indices.json)

### 2. Inference pipeline

Prediction logic lives in [`utils/predictor.py`](C:/Fruit Mango Classifier/utils/predictor.py). The predictor:

- lazily loads the Keras model
- reads class labels from JSON when available
- infers the required image input size from the saved model
- preprocesses uploaded images
- returns the predicted class and confidence score

This is a practical design choice because it keeps deployment code separate from training code and avoids loading the model repeatedly on every request.

### 3. Web application

The application layer is defined in [`app/app.py`](C:/Fruit Mango Classifier/app/app.py), with a small launcher in [`app.py`](C:/Fruit Mango Classifier/app.py).

The Flask app provides:

- a landing page
- a mango varieties overview page
- individual variety detail pages
- an image upload and classification page
- file validation for `png`, `jpg`, `jpeg`, and `webp`
- upload size limiting
- user-friendly error handling when the model or TensorFlow is missing

An important project detail is that the app does not just output a label. It also links the prediction to a curated profile page for the predicted mango variety, making the experience more explainable and educational.

## Results

The notebook output records the following final test performance:

- Test accuracy: `96.86%`
- Test loss: `0.0846`

The saved classification report in the notebook shows:

| Class | Precision | Recall | F1-score |
| --- | ---: | ---: | ---: |
| Amrapali | 1.00 | 1.00 | 1.00 |
| Fazlee | 1.00 | 0.95 | 0.97 |
| Harivanga | 0.92 | 1.00 | 0.96 |
| Mollika | 0.96 | 0.99 | 0.97 |
| Nilambori | 0.98 | 0.91 | 0.94 |

These results suggest the model is strong enough for a prototype or demo deployment on the current dataset. The weakest recall appears on `Nilambori`, which may indicate overlap with visually similar classes or sensitivity to image conditions.

## Product Design Choices

One of the more interesting aspects of this project is that it mixes classification with content design.

Instead of presenting a raw model score alone, the application:

- shows prediction confidence
- gives short guidance based on confidence level
- lets users inspect a profile page for the predicted class
- provides curated descriptions, origin, season, taste, and references for each variety

This turns the model into a guided classification experience rather than a black-box output.

## Strengths

- End-to-end implementation from training to deployment
- Balanced 5-class dataset
- Transfer learning keeps the model practical for a relatively small dataset
- Clear separation between app, predictor, model artifacts, and templates
- User-facing design adds explainability through class profile pages
- Defensive handling of missing models and unsupported file types

## Limitations

- The classifier is limited to only five mango varieties
- Generalization to real-world field images is still uncertain without external validation
- Uploaded files are stored in `static/uploads`, so cleanup and retention policy are not yet addressed
- There are no automated tests for the Flask app or inference utilities
- Confidence is displayed, but no calibrated uncertainty or top-k alternatives are shown
- The repository contains both notebook and script training flows, and they are not fully aligned

That last point matters: the notebook appears to be the most up-to-date training pipeline, while [`src/transfer_learning.py`](C:/Fruit Mango Classifier/src/transfer_learning.py) looks like an earlier experimental script with different defaults and an invalid `if _name_ == "_main_"` guard. For future maintenance, the project would benefit from consolidating training into one reliable entry point.

## Lessons From The Project

This repository shows a few practical machine learning lessons clearly:

1. Transfer learning is a strong baseline for small and medium-sized image datasets.
2. Dataset organization matters as much as model choice for smooth training and deployment.
3. A usable ML project needs interface design, validation, and error handling in addition to model accuracy.
4. Explainability can be improved with simple UX choices such as class guides and source-backed descriptions.

## How To Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the application:

```bash
python app.py
```

Then open the local Flask server in your browser and visit the classifier page to upload a mango image.

## Project Structure

```text
Fruit Mango Classifier/
|-- app/
|   `-- app.py                 Flask routes and page logic
|-- models/
|   `-- mango_classifier.keras Deployment model
|-- notebooks/
|   |-- mango_classifier.ipynb Main training workflow and evaluation
|   `-- class_indices.json     Label mapping
|-- src/
|   `-- transfer_learning.py   Earlier training script
|-- templates/                 HTML pages
|-- static/                    CSS, JS, and uploaded files
|-- utils/
|   `-- predictor.py           Prediction utilities
|-- requirements.txt
`-- app.py
```

## Conclusion

This project is best understood as an applied machine learning case study: a focused classifier for five mango fruit varieties, wrapped in a simple educational product. The technical core is solid for a prototype, especially given the recorded `96.86%` test accuracy, and the app design shows a thoughtful attempt to make predictions interpretable for users.

The next best improvements would be dataset expansion, better evaluation on truly unseen images, upload cleanup, automated tests, and a single production-ready training pipeline.

