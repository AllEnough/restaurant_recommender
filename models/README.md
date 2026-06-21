# OpenCV model assets

這些 ONNX 模型由 FastAPI 的 `/api/emotion/analyze` 使用；React 相機只上傳使用者主動拍攝的單張影像，伺服器不會保存照片。部署 Docker 映像時必須一併包含本目錄。

表情結果只作為外食推薦的情境輸入；餐廳與食譜的 Dashboard、模型評估及分數拆解由推薦 API 計算，不是由這兩個影像模型產生。

The React/FastAPI interface uses YuNet face detection with the FER+ emotion model supplied by the project team:

| File | Source | License | SHA-256 |
|---|---|---|---|
| `face_detection_yunet_2023mar.onnx` | `opencv/face_detection_yunet` on Hugging Face | MIT | `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4` |
| `emotion-ferplus-8.onnx` | ONNX Model Zoo Emotion FER+ | Apache-2.0 | `a2a2ba6a335a3b29c21acb6272f962bd3d47f84952aaffa03b60986e04efa61c` |

YuNet provides the face box and five landmarks. The aligned face is converted to 64 × 64 grayscale input for FER+, which classifies neutral, happiness, surprise, sadness, anger, disgust, fear, and contempt. Its output is used only as an optional recommendation signal and is not a psychological or medical assessment.
