# MentorX — AI Fitness Coaching System

> Real-time exercise form analysis using computer vision and AI-generated coaching feedback.

---

## English Version

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [How It Works](#how-it-works)
- [Exercises](#exercises)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)

---

## Overview

MentorX captures your exercise movements through a webcam, detects body joint positions using MediaPipe Pose Landmarker, evaluates movement quality rep-by-rep, and delivers personalized coaching feedback via Google Gemini after each session.

**Supported exercises:** Squat · Pushup · Plank · Bicep Curl · Situp

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Vue 3, Vite, Tailwind CSS, HTML5 Camera API, Canvas |
| Backend | Python, FastAPI, WebSockets |
| Pose Detection | MediaPipe Pose Landmarker Lite |
| Image Processing | OpenCV, NumPy |
| AI Feedback | Google Gemini 2.5 Flash |

---

## Prerequisites

Make sure the following are installed before starting:

- Python 3.11+
- Node.js (LTS)
- A Gemini API key — get one at [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

---

## Setup

### Step 1 — Backend (ai-service)

Open a terminal in the project root.

```bash
cd ai-service
```

**Create and activate a virtual environment:**

macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

Windows:
```bash
python -m venv venv
.\venv\Scripts\activate
```

**Install dependencies:**
```bash
pip install fastapi "uvicorn[standard]" mediapipe opencv-python websockets numpy google-genai python-dotenv
```

**Get your Gemini API key:**

1. Go to [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **Create API key** and copy it

**Create a `.env` file inside `ai-service/`:**
```
GEMINI_API_KEY=your_key_here
```

> ⚠️ Without a valid API key in `.env`, the backend will start but AI coaching feedback will not work.

**Start the backend server:**
```bash
uvicorn main:app --reload --port 8000
```

You should see: `INFO: Application startup complete.`

---

### Step 2 — Frontend

Open a **new** terminal window.

```bash
cd frontend
npm install
npm run dev
```

Open your browser at: `http://localhost:5173`

---

## How It Works

```
User Camera (~7.7 FPS)
       │
       ▼
Frontend (Vue 3)
  - Captures and encodes frames as Base64 JPEG
  - Streams frames via WebSocket to backend
  - Draws real-time skeleton overlay on Canvas
  - Tracks rep count, error count, and per-rep quality
       │  WebSocket /ws/pose  (per frame, real-time)
       ▼
Backend (FastAPI)
  - MediaPipe detects 33 body joint landmarks
  - PoseEngine calculates joint angles
  - State machine counts reps and flags errors
  - 3-frame angle smoothing to reduce noise
  - 3-frame DOWN confirmation to prevent false counts
  - Per-rep quality tracked: min angle, error flag, quality grade
       │  Returns per-frame: angle, status, count,
       │  side_view, error_type, landmarks, last_rep
       ▼
After session ends:
  Frontend POST /session/feedback
  { exercise, rep_count, error_count, rep_history, user_profile }
       │
       ▼
  Gemini 2.5 Flash
  Receives per-rep quality breakdown → returns coaching advice
```

**Session data collected per rep:**
```json
{
  "rep": 2,
  "min_angle": 115.6,
  "has_error": true,
  "quality": "shallow"
}
```

---

## Exercises

| Exercise | Camera | Key Measurement | Quality Grades |
|---|---|---|---|
| Squat | **Side view** | Hip→Knee→Ankle angle | Good <90°, OK 90–110°, Shallow >110° |
| Pushup | **Side view** | Shoulder→Elbow→Wrist angle | Good <75°, OK 75–90°, Shallow >90° |
| Plank | **Side view** | Shoulder→Hip→Ankle angle | Hold timer, resets on form break |
| Bicep Curl | **Front facing** | Shoulder→Elbow→Wrist angle | Good <45°, OK 45–55° |
| Situp | **Side view** | Shoulder→Hip→Knee angle | Good <75°, OK 75–90°, Shallow >90° |

> **Camera setup tip:** For side-view exercises, position the camera at waist height directly to your side, 2–3 meters away so your full body is visible. Bicep curl is the only exercise that works with a front-facing camera (normal laptop/phone position).

---

## Project Structure

```
CanadaH/
├── ai-service/                        # Backend — FastAPI + AI engine
│   ├── engine/
│   │   ├── pose_engine.py             # MediaPipe, angle calculation, rep counting, quality tracking
│   │   └── llm_feedback.py            # Gemini AI coaching feedback generation
│   ├── main.py                        # FastAPI app: WebSocket + REST endpoints
│   ├── test_client.py                 # Offline test tool (no frontend needed)
│   ├── pose_landmarker.task           # MediaPipe model file (must be present)
│   └── .env                           # API key (never commit this)
│
├── frontend/                          # Frontend — Vue 3
│   └── src/
│       ├── components/                # Reusable Vue components
│       ├── views/                     # Page-level views
│       ├── stores/                    # Pinia state stores
│       ├── router/                    # Vue Router config
│       └── App.vue                    # Main entry: camera, skeleton, session logic
│
└── README.md
```

---

## API Reference

### `WS /ws/pose` — Real-time frame analysis

Frontend sends a JSON object per frame:
```json
{
  "image": "<base64 JPEG string>",
  "mode": "squat",
  "target_reps": 10
}
```

Backend returns per frame:
```json
{
  "angle": 95.3,
  "status": "正在下蹲",
  "count": 2,
  "side_view": true,
  "error_type": null,
  "last_rep": {
    "rep": 2,
    "min_angle": 88.4,
    "has_error": false,
    "quality": "good"
  },
  "landmarks": [
    { "x": 0.51, "y": 0.72, "visibility": 0.98 },
    "..."
  ]
}
```

---

### `POST /session/feedback` — AI coaching after session

Called once when the user ends a session.

**Request body:**
```json
{
  "exercise": "squat",
  "rep_count": 5,
  "error_count": 1,
  "rep_history": [
    { "rep": 1, "min_angle": 88.2, "has_error": false, "quality": "good" },
    { "rep": 2, "min_angle": 115.6, "has_error": true, "quality": "shallow" }
  ],
  "user_profile": {
    "height": 175,
    "weight": 70,
    "age": 25
  }
}
```

**Response:**
```json
{
  "feedback": "你的第一次深蹲深度很好，但第二次稍微淺了一點。試著讓大腿與地面平行，下次每一下都保持這個深度。"
}
```


## 繁體中文版

- [系統簡介](#系統簡介)
- [技術堆疊](#技術堆疊)
- [開發環境準備](#開發環境準備)
- [啟動步驟](#啟動步驟)
- [系統運作方式](#系統運作方式)
- [支援動作](#支援動作)
- [專案結構](#專案結構)
- [API 說明](#api-說明)


---

## 系統簡介

MentorX 透過網路攝影機擷取你的運動動作，使用 MediaPipe Pose Landmarker 偵測人體關節位置，逐次評估動作品質，並在每次訓練結束後透過 Google Gemini 產出個人化教練建議。

**支援動作：** 深蹲 · 伏地挺身 · 棒式 · 二頭肌彎舉 · 仰臥起坐

---

## 技術堆疊

| 層級 | 技術 |
|---|---|
| 前端 | Vue 3、Vite、Tailwind CSS、HTML5 Camera API、Canvas |
| 後端 | Python、FastAPI、WebSockets |
| 姿勢偵測 | MediaPipe Pose Landmarker Lite |
| 影像處理 | OpenCV、NumPy |
| AI 回饋 | Google Gemini 2.5 Flash |

---

## 開發環境準備

開始之前，請確認你的電腦已安裝以下工具：

- Python 3.11 以上版本
- Node.js（LTS 版）
- Gemini API 金鑰 — 申請網址：[https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

---

## 啟動步驟

### 第一步 — 啟動後端（ai-service）

在專案根目錄開啟終端機。

```bash
cd ai-service
```

**建立並啟動虛擬環境：**

macOS / Linux：
```bash
python3 -m venv venv
source venv/bin/activate
```

Windows：
```bash
python -m venv venv
.\venv\Scripts\activate
```

**安裝必要套件：**
```bash
pip install fastapi "uvicorn[standard]" mediapipe opencv-python websockets numpy google-genai python-dotenv
```

**取得你的 Gemini API 金鑰：**

1. 前往 [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. 用 Google 帳號登入
3. 點選 **Create API key**，複製金鑰

**在 `ai-service/` 資料夾內建立 `.env` 檔案：**
```
GEMINI_API_KEY=你的金鑰填在這裡
```

> ⚠️ 沒有在 `.env` 填入有效的 API 金鑰，後端可以啟動，但 AI 教練回饋功能將無法運作。

**啟動後端伺服器：**
```bash
uvicorn main:app --reload --port 8000
```

出現 `INFO: Application startup complete.` 代表啟動成功。

---

### 第二步 — 啟動前端

**開啟新的終端機視窗：**

```bash
cd frontend
npm install
npm run dev
```

瀏覽器開啟：`http://localhost:5173`

---

## 系統運作方式

```
使用者鏡頭（約 7.7 FPS）
       │
       ▼
前端（Vue 3）
  - 擷取影格並編碼為 Base64 JPEG
  - 透過 WebSocket 串流傳送至後端
  - 在 Canvas 上即時繪製骨架疊層
  - 追蹤次數、錯誤次數、每次動作品質
       │  WebSocket /ws/pose（每幀即時分析）
       ▼
後端（FastAPI）
  - MediaPipe 偵測 33 個身體關節座標
  - PoseEngine 計算關節角度
  - 狀態機計算次數並標記錯誤
  - 3 幀角度平滑處理（降低抖動）
  - 3 幀連續確認 DOWN 狀態（防止誤計）
  - 逐次追蹤動作品質：最深角度、錯誤旗標、品質等級
       │  每幀回傳：angle, status, count,
       │  side_view, error_type, landmarks, last_rep
       ▼
訓練結束後：
  前端 POST /session/feedback
  { exercise, rep_count, error_count, rep_history, user_profile }
       │
       ▼
  Gemini 2.5 Flash
  接收每次動作的品質細節 → 回傳教練建議
```

**每次動作記錄的資料範例：**
```json
{
  "rep": 2,
  "min_angle": 115.6,
  "has_error": true,
  "quality": "shallow"
}
```

---

## 支援動作

| 動作 | 鏡頭方向 | 主要量測 | 品質分類 |
|---|---|---|---|
| 深蹲 | **側面** | 髖→膝→踝 角度 | 良好 <90°、尚可 90–110°、深度不足 >110° |
| 伏地挺身 | **側面** | 肩→肘→腕 角度 | 良好 <75°、尚可 75–90°、深度不足 >90° |
| 棒式 | **側面** | 肩→髖→踝 角度 | 計時模式，姿勢崩掉即歸零 |
| 二頭肌彎舉 | **正面** | 肩→肘→腕 角度 | 良好 <45°、尚可 45–55° |
| 仰臥起坐 | **側面** | 肩→髖→膝 角度 | 良好 <75°、尚可 75–90°、幅度不足 >90° |

> **鏡頭設定建議：** 側面動作請將鏡頭架在你的正側面，腰部高度，距離約 2–3 公尺，確保全身入鏡。二頭肌彎舉是唯一適合正面（一般筆電/手機位置）的動作。

---

## 專案結構

```
CanadaH/
├── ai-service/                        # 【後端】FastAPI + AI 引擎
│   ├── engine/
│   │   ├── pose_engine.py             # MediaPipe 初始化、角度計算、計次、品質追蹤
│   │   └── llm_feedback.py            # Gemini AI 教練回饋文字生成
│   ├── main.py                        # FastAPI 主程式：WebSocket + REST 端點
│   ├── test_client.py                 # 離線測試工具（不需前端）
│   ├── pose_landmarker.task           # MediaPipe 模型檔案（必須存在）
│   └── .env                           # API 金鑰（請勿提交至 Git）
│
├── frontend/                          # 【前端】Vue 3
│   └── src/
│       ├── components/                # 可複用的 Vue 元件
│       ├── views/                     # 頁面級別 View
│       ├── stores/                    # Pinia 狀態管理
│       ├── router/                    # Vue Router 設定
│       └── App.vue                    # 主介面：鏡頭啟動、骨架繪製、Session 邏輯
│
└── README.md
```

---

## API 說明

### `WS /ws/pose` — 即時逐幀分析

前端每幀傳送 JSON 物件：
```json
{
  "image": "<Base64 JPEG 字串>",
  "mode": "squat",
  "target_reps": 10
}
```

後端每幀回傳：
```json
{
  "angle": 95.3,
  "status": "正在下蹲",
  "count": 2,
  "side_view": true,
  "error_type": null,
  "last_rep": {
    "rep": 2,
    "min_angle": 88.4,
    "has_error": false,
    "quality": "good"
  },
  "landmarks": [
    { "x": 0.51, "y": 0.72, "visibility": 0.98 },
    "..."
  ]
}
```

---

### `POST /session/feedback` — 訓練結束後的 AI 教練建議

使用者結束訓練後呼叫一次。

**Request body：**
```json
{
  "exercise": "squat",
  "rep_count": 5,
  "error_count": 1,
  "rep_history": [
    { "rep": 1, "min_angle": 88.2, "has_error": false, "quality": "good" },
    { "rep": 2, "min_angle": 115.6, "has_error": true, "quality": "shallow" }
  ],
  "user_profile": {
    "height": 175,
    "weight": 70,
    "age": 25
  }
}
```

**Response：**
```json
{
  "feedback": "你的第一次深蹲深度很好，但第二次稍微淺了一點。試著讓大腿與地面平行，下次每一下都保持這個深度。"
}
```

---

## 注意事項

- **鏡頭權限：** 首次使用請在瀏覽器點選「允許」使用攝影機
- **API 金鑰安全：** `.env` 已列入 `.gitignore`，請勿手動提交至 Git
- **模型檔案：** `pose_landmarker.task` 必須存在於 `ai-service/` 資料夾內，伺服器才能啟動
- **CORS 設定：** 目前開放所有來源，正式部署前請記得限制
