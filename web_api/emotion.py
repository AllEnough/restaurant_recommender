from __future__ import annotations

import threading
from pathlib import Path

import cv2
import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile


ROOT = Path(__file__).resolve().parent.parent
FACE_MODEL = ROOT / "models" / "face_detection_yunet_2023mar.onnx"
EMOTION_MODEL = ROOT / "models" / "emotion-ferplus-8.onnx"
EXPRESSIONS = ["neutral", "happiness", "surprise", "sadness", "anger", "disgust", "fear", "contempt"]
EXPRESSION_LABELS = {
    "neutral": "平靜",
    "happiness": "開心",
    "surprise": "驚訝",
    "sadness": "難過",
    "anger": "生氣",
    "disgust": "厭惡",
    "fear": "緊張",
    "contempt": "輕蔑",
}
MOOD_MAPPING = {
    "neutral": "選擇困難",
    "happiness": "開心",
    "surprise": "開心",
    "sadness": "心情不好",
    "anger": "心情不好",
    "disgust": "心情不好",
    "fear": "疲累",
    "contempt": "心情不好",
}
STANDARD_POINTS = np.array(
    [[38.2946, 51.6963], [73.5318, 51.5014], [56.0252, 71.7366], [41.5493, 92.3655], [70.7299, 92.2041]],
    dtype=np.float32,
)

router = APIRouter(prefix="/api/emotion", tags=["emotion"])
model_lock = threading.Lock()
face_detector = None
emotion_network = None


def load_models():
    global face_detector, emotion_network
    if face_detector is None:
        if not FACE_MODEL.exists() or not EMOTION_MODEL.exists():
            raise RuntimeError("OpenCV 表情辨識模型尚未安裝")
        face_detector = cv2.FaceDetectorYN.create(str(FACE_MODEL), "", (320, 320), 0.8, 0.3, 5000)
        emotion_network = cv2.dnn.readNetFromONNX(str(EMOTION_MODEL))
    return face_detector, emotion_network


def align_face(image: np.ndarray, landmarks: np.ndarray) -> np.ndarray:
    transform, _ = cv2.estimateAffinePartial2D(landmarks, STANDARD_POINTS, method=cv2.LMEDS)
    if transform is None:
        raise ValueError("無法校正臉部角度")
    return cv2.warpAffine(image, transform, (112, 112))


def softmax(values: np.ndarray) -> np.ndarray:
    shifted = values - np.max(values)
    exponent = np.exp(shifted)
    return exponent / np.sum(exponent)


def predict_expression(network: cv2.dnn.Net, aligned_face: np.ndarray) -> tuple[str, float, dict[str, float]]:
    gray = cv2.cvtColor(aligned_face, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (64, 64), interpolation=cv2.INTER_AREA).astype(np.float32)
    network.setInput(resized.reshape(1, 1, 64, 64))
    probabilities = softmax(network.forward().reshape(-1))
    if len(probabilities) != len(EXPRESSIONS):
        raise RuntimeError(f"FER+ 模型輸出類別數不符：{len(probabilities)}")
    index = int(np.argmax(probabilities))
    scores = {label: round(float(probabilities[i]), 4) for i, label in enumerate(EXPRESSIONS)}
    return EXPRESSIONS[index], float(probabilities[index]), scores


def analyze_image(image: np.ndarray) -> dict:
    detector, network = load_models()
    height, width = image.shape[:2]
    if width < 80 or height < 80:
        raise ValueError("照片解析度太低")

    detector.setInputSize((width, height))
    _, faces = detector.detect(image)
    if faces is None or len(faces) == 0:
        raise ValueError("沒有偵測到清楚的人臉")

    face = max(faces, key=lambda item: float(item[2] * item[3]))
    aligned = align_face(image, face[4:14].reshape(5, 2).astype(np.float32))
    expression, confidence, scores = predict_expression(network, aligned)
    box = {
        "x": round(float(face[0]) / width, 4),
        "y": round(float(face[1]) / height, 4),
        "width": round(float(face[2]) / width, 4),
        "height": round(float(face[3]) / height, 4),
    }
    return {
        "expression": expression,
        "expression_label": EXPRESSION_LABELS[expression],
        "recommended_mood": MOOD_MAPPING[expression],
        "confidence": round(confidence, 4),
        "scores": scores,
        "face_box": box,
        "model": "YuNet + ONNX Model Zoo FER+ 8-class CNN",
        "notice": "表情辨識僅用於推薦情境推測，不代表心理狀態或醫療判斷。",
    }


@router.post("/analyze")
async def analyze_emotion(image: UploadFile = File(...)):
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="僅支援 JPEG、PNG 或 WebP 圖片")
    content = await image.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="圖片不可超過 5 MB")
    decoded = cv2.imdecode(np.frombuffer(content, dtype=np.uint8), cv2.IMREAD_COLOR)
    if decoded is None:
        raise HTTPException(status_code=422, detail="無法讀取圖片")
    try:
        with model_lock:
            return analyze_image(decoded)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except (cv2.error, RuntimeError) as error:
        raise HTTPException(status_code=503, detail=f"表情辨識暫時無法使用：{error}") from error
