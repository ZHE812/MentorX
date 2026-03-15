"""
後端小模型 - 喂深蹲的短影片給他分析
Offline prototype — simulates the frontend sending a squat video to the backend.

Usage (from ai-service/):
    source venv/bin/activate
    python test_client.py

Make sure the server is running first:
    uvicorn main:app --reload --port 8000

Or run fully offline (no WebSocket) with --offline flag:
    python test_client.py --offline
"""

import argparse
import asyncio
import base64
import json
import sys
import cv2
import websockets

VIDEO_PATH = "Squat_-_exercise_demonstration_video.webm"
WS_URL     = "ws://127.0.0.1:8000/ws/session"
SAMPLE_FPS = 10   # frames per second 


def extract_frames(video_path: str, target_fps: int = SAMPLE_FPS):
    """Read video and sample frames at target_fps."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[test_client] ERROR: Cannot open video: {video_path}")
        sys.exit(1)

    src_fps   = cap.get(cv2.CAP_PROP_FPS) or 30
    total     = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step      = max(1, int(src_fps / target_fps))

    print(f"[test_client] Video: {video_path}")
    print(f"[test_client] Source FPS: {src_fps:.1f} | Total frames: {total} | Sampling every {step} frames")

    frames, idx = [], 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if idx % step == 0:
            frames.append(frame)
        idx += 1
    cap.release()
    return frames


def encode_frame(frame) -> str:
    """Encode OpenCV frame as base64 JPEG (same as frontend does)."""
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
    return base64.b64encode(buf).decode("utf-8")


def print_result(data: dict):
    print("\n" + "=" * 50)
    print("  MENTORX SQUAT ANALYSIS RESULT")
    print("=" * 50)
    print(f"  Status:    {data.get('status', '-')}")
    print(f"  Exercise:  {data.get('exercise', '-')}")
    print(f"  Reps:      {data.get('rep_count', 0)}")
    print(f"  Score:     {data.get('score', 0)}/100")
    print(f"  Issues:    {data.get('issues', [])}")
    m = data.get("metrics", {})
    print(f"  Metrics:")
    print(f"    min_knee_angle:    {m.get('min_knee_angle')}°")
    print(f"    avg_rep_depth:     {m.get('avg_rep_depth')}°")
    print(f"    avg_torso_angle:   {m.get('avg_torso_angle')}°")
    print(f"    valid_frame_count: {m.get('valid_frame_count')}")
    print(f"\n  Coach Feedback:")
    print(f"  \"{data.get('feedback', 'N/A')}\"")
    print("=" * 50 + "\n")


# ── WebSocket mode (default)

async def run_websocket(frames):
    encoded = [encode_frame(f) for f in frames]
    print(f"[test_client] Sending {len(encoded)} frames over WebSocket → {WS_URL}\n")

    async with websockets.connect(WS_URL) as ws:
        # 1. Start signal
        await ws.send(json.dumps({"type": "start"}))
        resp = json.loads(await ws.recv())
        print(f"[test_client] Server: {resp}")

        # 2. Send frames
        for i, frame_b64 in enumerate(encoded):
            await ws.send(frame_b64)
            if (i + 1) % 10 == 0:
                print(f"[test_client]   Sent {i+1}/{len(encoded)} frames...")

        # 3. Stop signal
        await ws.send(json.dumps({"type": "stop"}))
        print("[test_client] Waiting for analysis result...")

        # 4. Final result
        result = json.loads(await ws.recv())
        print_result(result)


# ── Offline mode 

def run_offline(frames):
    """
    Run the full analysis pipeline locally without a running server.
    Useful for quick testing and demos.
    """
    from engine.pose_engine import PoseEngine
    from engine.llm_feedback import generate_feedback

    print(f"[test_client] Running offline analysis on {len(frames)} frames...\n")
    engine = PoseEngine()

    session_data = engine.process_session(frames)
    summary      = engine.summarize_session(session_data)
    summary["feedback"] = generate_feedback(summary)

    print_result(summary)


# ── Entry point 

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true",
                        help="Run locally without a running server")
    parser.add_argument("--video", default=VIDEO_PATH,
                        help=f"Path to video file (default: {VIDEO_PATH})")
    args = parser.parse_args()

    frames = extract_frames(args.video)
    print(f"[test_client] Sampled {len(frames)} frames\n")

    if args.offline:
        run_offline(frames)
    else:
        asyncio.run(run_websocket(frames))
