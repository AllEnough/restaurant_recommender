from __future__ import annotations

import threading
from pathlib import Path

import cv2
import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile


ROOT = Path(__file__).resolve().parent.parent
FACE_MODEL = ROOT / "models" / "face_detection_yunet_2023mar.onnx"
EMOTION_MODEL = ROOT / "models" / "facial_expression_recognition_mobilefacenet_2022july.onnx"
EXPRESSIONS = ["angry", "disgust", "fearful", "happy", "neutral", "sad", "surprised"]
EXPRESSION_LABELS = {
    "angry": "生氣",
    "disgust": "厭惡",
    "fearful": "緊張",
    "happy": "開心",
    "neutral": "平靜",
    "sad": "難過",
    "surprised": "驚訝",
}
MOOD_MAPPING = {
    "angry": "心情不好",
    "disgust": "心情不好",
    "fearful": "疲累",
    "happy": "開心",
    "neutral": "選擇困難",
    "sad": "心情不好",
    "surprised": "開心",
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
        emotion_network = cv2.dnn.readNet(str(EMOTION_MODEL))
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
    rgb = cv2.cvtColor(aligned, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    normalized = (rgb - 0.5) / 0.5
    blob = cv2.dnn.blobFromImage(normalized)
    network.setInput(blob, "data")
    output = network.forward(["label"])[0]
    logits = np.asarray(output).reshape(-1)
    probabilities = softmax(logits)
    index = int(np.argmax(probabilities))
    expression = EXPRESSIONS[index]
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
        "confidence": round(float(probabilities[index]), 4),
        "face_box": box,
        "model": "OpenCV Zoo Progressive Teacher MobileFaceNet",
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
