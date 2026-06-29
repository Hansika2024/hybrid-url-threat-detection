from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

import numpy as np
import onnxruntime as ort

from app.utils import preprocess_url


# ======================================
# BASE DIRECTORY
# ======================================

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "model" / "hybrid_model.onnx"


# ======================================
# FASTAPI APP
# ======================================

app = FastAPI(
    title="Hybrid URL Threat Detection API",
    description="MiniLM + Hybrid Deep Learning URL Classification System",
    version="1.0"
)


# ======================================
# CORS
# ======================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ======================================
# LOAD ONNX MODEL
# ======================================

print(f"Loading ONNX model from: {MODEL_PATH}")

session = ort.InferenceSession(
    str(MODEL_PATH)
)

print("\n===== ONNX INPUTS =====")

for inp in session.get_inputs():

    print(
        "NAME:", inp.name,
        "| SHAPE:", inp.shape,
        "| TYPE:", inp.type
    )

print("=======================\n")

print("\n===== MODEL INPUTS =====")

for inp in session.get_inputs():
    print(inp.name, inp.shape, inp.type)

print("========================\n")

print("ONNX model loaded successfully")


# ======================================
# CLASS LABELS
# MATCHING TRAINING NOTEBOOK
# ======================================

CLASS_LABELS = {
    0: "Benign",
    1: "Phishing",
    2: "Piracy",
    3: "Typosquatting"
}


# ======================================
# REQUEST MODEL
# ======================================

class URLRequest(BaseModel):
    url: str


# ======================================
# HOME ROUTE
# ======================================

@app.get("/")
def home():

    return {
        "message": "Hybrid URL Threat Detection API Running"
    }


# ======================================
# PREDICTION ROUTE
# ======================================

@app.post("/predict")
def predict(data: URLRequest):

    try:

        url = data.url
        if '.' not in url.split('/')[-1]:
            url = url + '.com' 

        # ==================================
        # PREPROCESS
        # ==================================

        tokens, features, embeddings = preprocess_url(
            url
        )

        # ==================================
        # DEBUGGING
        # ==================================

        print("\n========== DEBUG ==========")

        print("TOKENS SHAPE:", tokens.shape)
        print("TOKENS DTYPE:", tokens.dtype)
        print("TOKEN MIN:", tokens.min())
        print("TOKEN MAX:", tokens.max())

        print("FEATURES SHAPE:", features.shape)
        print("EMBEDDINGS SHAPE:", embeddings.shape)

        print("===========================\n")


        # ==================================
        # ONNX INFERENCE
        # ==================================

        outputs = session.run(
            None,
            {
                "tokens": tokens.astype(np.int64),
                "features": features.astype(np.float32),
                "minilm": embeddings.astype(np.float32)
            }
        )

        logits = outputs[0]


        # ==================================
        # SOFTMAX
        # ==================================

        exp_scores = np.exp(
            logits - np.max(logits)
        )

        probabilities = exp_scores / exp_scores.sum()


        # ==================================
        # TOP PREDICTION
        # ==================================

        predicted_class = int(
            np.argmax(probabilities)
        )

        confidence = float(
            probabilities[0][predicted_class]
        )

        prediction = CLASS_LABELS.get(
            predicted_class,
            "unknown"
        )


        # ==================================
        # ALL CLASS SCORES
        # ==================================

        all_scores = {}

        for idx, prob in enumerate(probabilities[0]):

            label = CLASS_LABELS[idx]

            all_scores[label] = (
                f"{prob * 100:.2f}%"
            )

        return {
            "url": url,
            "prediction": prediction,
            "confidence": f"{confidence * 100:.2f}%",
            "all_scores": all_scores
        }

    except Exception as e:

        return {
            "error": str(e)
        }