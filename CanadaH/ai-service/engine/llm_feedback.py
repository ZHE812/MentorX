import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

_client = None

def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY not set")
        _client = genai.Client(api_key=api_key)
    return _client


def generate_session_feedback(session_data: dict) -> str:
    """
    Called by POST /session/feedback after a real-time training session.
    Accepts frontend session summary (exercise, reps, errors, rep_history, user profile)
    and returns AI coaching advice in Traditional Chinese.
    """
    exercise    = session_data.get("exercise", "exercise")
    rep_count   = session_data.get("rep_count", 0)
    error_count = session_data.get("error_count", 0)
    rep_history = session_data.get("rep_history", [])
    profile     = session_data.get("user_profile") or {}

    height = profile.get("height", "未知")
    weight = profile.get("weight", "未知")
    age    = profile.get("age", "未知")

    
    if rep_history:
        rep_lines = []
        good_count     = sum(1 for r in rep_history if r.get("quality") == "good")
        acceptable_count = sum(1 for r in rep_history if r.get("quality") == "acceptable")
        shallow_count  = sum(1 for r in rep_history if r.get("quality") == "shallow")
        error_reps     = sum(1 for r in rep_history if r.get("has_error"))

        for r in rep_history:
            q   = r.get("quality", "unknown")
            ang = r.get("min_angle", "?")
            err = "（有姿勢錯誤）" if r.get("has_error") else ""
            quality_zh = {"good": "良好", "acceptable": "尚可", "shallow": "深度不足"}.get(q, q)
            rep_lines.append(f"  第 {r.get('rep')} 次：{quality_zh}，最深角度 {ang}°{err}")

        rep_detail = "\n".join(rep_lines)
        quality_summary = (
            f"良好次數：{good_count}，尚可次數：{acceptable_count}，"
            f"深度不足次數：{shallow_count}，含姿勢錯誤次數：{error_reps}"
        )
    else:
        rep_detail = "  （無次數細節資料）"
        quality_summary = "無法判斷動作品質"


    if rep_count == 0:
        tone = (
            "使用者本次沒有完成任何有效動作。請直接告知這次訓練是失敗的，"
            "分析可能原因（動作幅度不足、姿勢錯誤導致系統無法偵測），"
            "給出從頭開始的具體步驟。絕對不能給予任何正面評價。"
        )
    elif rep_history:
        good_ratio = sum(1 for r in rep_history if r.get("quality") == "good") / len(rep_history)
        has_errors = any(r.get("has_error") for r in rep_history)
        if good_ratio >= 0.8 and not has_errors:
            tone = "整體品質優良。可以給予肯定，但仍需提出一個需要注意的細節。"
        elif good_ratio >= 0.5:
            tone = "表現參差不齊。請針對較差的幾次給出具體改進建議，不要只聚焦在好的次數上。"
        else:
            tone = (
                "大部分動作品質不佳。請以改進為主軸，明確說明問題所在，"
                "不要用模糊的鼓勵話語掩蓋問題。"
            )
    else:
        tone = "根據實際表現給出平衡且誠實的評價。"

    prompt = (
        "你是一位專業、直接、根據數據說話的 AI 健身教練。\n"
        f"使用者資料：身高 {height}cm，體重 {weight}kg，年齡 {age}。\n"
        f"訓練項目：{exercise}\n"
        f"總完成次數：{rep_count}，偵測到姿勢問題次數：{error_count}\n\n"
        f"各次動作詳情：\n{rep_detail}\n"
        f"品質統計：{quality_summary}\n\n"
        f"評價基調：{tone}\n\n"
        "請用英文和繁體中文，約 150 字，先英文在繁體中文，給出：\n"
        "1. 誠實的本次訓練評價（根據上方數據，不要美化）\n"
        "2. 具體的姿勢修正建議\n"
        "3. 下次訓練的強度或目標調整建議\n"
    )

    try:
        client   = _get_client()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        print(f"[llm_feedback] Session feedback failed ({e}), using fallback.")
        return (
            f"本次 {exercise} 訓練完成了 {rep_count} 次，偵測到 {error_count} 個姿勢問題。"
            "請保持核心穩定，動作放慢確保到位。下次訓練可適量增加組數。"
        )


def generate_feedback(summary: dict) -> str:
    """
    Call Gemini Flash to turn structured squat analysis into 2-3 sentence coaching text.
    Falls back to rule-based text if the API call fails.
    """
    from engine.pose_engine import PoseEngine

    issues    = summary.get("issues", [])
    rep_count = summary.get("rep_count", 0)
    score     = summary.get("score", 0)
    metrics   = summary.get("metrics", {})
    min_knee  = metrics.get("min_knee_angle")
    avg_torso = metrics.get("avg_torso_angle")
    avg_depth = metrics.get("avg_rep_depth")

    issue_descriptions = {
        "no_clear_rep_detected": "no complete squat rep was detected",
        "shallow_depth":         "squats were too shallow (hips didn't go low enough)",
        "forward_lean":          "torso leaned too far forward during the squat",
        "insufficient_pose_data":"not enough pose data was captured",
    }
    issue_text = "; ".join(issue_descriptions.get(i, i) for i in issues) if issues else "none"

    prompt = (
        "You are a supportive and concise fitness coach reviewing someone's squat form.\n\n"
        f"Session results:\n"
        f"- Reps completed: {rep_count}\n"
        f"- Score: {score}/100\n"
        f"- Form issues: {issue_text}\n"
        f"- Minimum knee angle reached: {min_knee}° (below 90° is good depth)\n"
        f"- Average rep depth angle: {avg_depth}°\n"
        f"- Average torso lean: {avg_torso}° (below 20° is good)\n\n"
        "Write exactly 2-3 sentences of coaching feedback. "
        "Be encouraging, realistic, and specific. "
        "Avoid exaggerated praise like 'perfect' or 'fantastic'. "
        "If no major issues are detected, briefly acknowledge strong form and suggest one small thing to keep in mind. "
        "Do not mention raw numbers — translate them into plain coaching language."
    )

    try:
        client   = _get_client()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        print(f"[llm_feedback] Gemini call failed ({e}), using fallback.")
        return PoseEngine.fallback_feedback(summary)
