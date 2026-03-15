import time
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import urllib.request
import os

# ── Squat thresholds 
DOWN_ANGLE_THRESHOLD  = 100   # knee angle below this → user is in squat
UP_ANGLE_THRESHOLD    = 160   # knee angle above this (after DOWN) → rep complete
SHALLOW_DEPTH_LIMIT   = 110   # avg rep depth above this → squat too shallow
FORWARD_LEAN_LIMIT    = 25    # avg torso angle above this → too much forward lean

# ── Pushup thresholds
PUSHUP_DOWN           = 90    # elbow angle below this → bottom of pushup
PUSHUP_UP             = 155   # elbow angle above this → top of pushup

# ── Bicep curl thresholds
CURL_EXTENDED         = 140   # elbow angle above this → arm extended (start/end)
CURL_CURLED           = 55    # elbow angle below this → arm fully curled

# ── Situp thresholds 
SITUP_DOWN            = 140   # shoulder-hip-knee angle above this → lying flat
SITUP_UP              = 90    # shoulder-hip-knee angle below this → sitting up

# ── Plank thresholds 
PLANK_STRAIGHT_MIN    = 155   # shoulder-hip-ankle angle above this → good plank

# ── General 
MIN_JOINT_VISIBILITY  = 0.5   # skip frame if key joints below this confidence
MIN_VALID_FRAMES      = 10    # fewer than this → insufficient data

# ── Anti-noise / rep quality 
MIN_FRAMES_IN_PHASE = 3    # consecutive frames required to confirm a DOWN state
ANGLE_SMOOTH_FRAMES = 3    # rolling window size for angle smoothing

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pose_landmarker.task")
print(f"[PoseEngine] Model path: {os.path.abspath(MODEL_PATH)}")

if not os.path.exists(MODEL_PATH):
    try:
        print("[PoseEngine] Downloading pose model...")
        url = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
        urllib.request.urlretrieve(url, MODEL_PATH)
        print("[PoseEngine] Model downloaded.")
    except Exception as e:
        raise RuntimeError(f"[PoseEngine] Failed to download pose model: {e}")


class PoseEngine:

    def __init__(self):
        base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            output_segmentation_masks=False,
            running_mode=vision.RunningMode.IMAGE
        )
        self.detector = vision.PoseLandmarker.create_from_options(options)

        self.counter      = 0
        self.sets_done    = 0
        self.target_reps  = 12
        self.stage        = "UP"
        self.current_mode = None

        self.start_time        = None
        self.elapsed_time      = 0
        self.is_timing         = False
        self.plank_hold_start  = None
        self.plank_hold_time   = 0

        self.frames_in_down = 0   
        self.angle_buffer   = []  

        self.current_rep_min_angle = 180.0
        self.current_rep_has_error = False
        self.rep_history           = []   # [{rep, min_angle, has_error, quality}]

    # helpers 

    def _get_vis(self, landmark):
        try:
            return landmark.presence
        except AttributeError:
            return landmark.visibility

    def calculate_angle(self, a, b, c):
        a, b, c = np.array(a), np.array(b), np.array(c)
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(radians * 180.0 / np.pi)
        if angle > 180.0:
            angle = 360 - angle
        return angle

    def _extract_landmarks(self, frame):
        img_rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
        result   = self.detector.detect(mp_image)
        if result.pose_landmarks and len(result.pose_landmarks) > 0:
            return result.pose_landmarks[0]
        return None

    def _detect_side_view(self, lm):
        try:
            dx = abs(lm[11].x - lm[12].x)
            return dx < 0.2
        except Exception:
            return True

    def _torso_angle(self, lm, side="left"):
        shoulder = lm[11] if side == "left" else lm[12]
        hip      = lm[23] if side == "left" else lm[24]
        dx = abs(shoulder.x - hip.x)
        dy = abs(hip.y - shoulder.y)
        return float(np.degrees(np.arctan2(dx, dy))) if dy > 0 else 0.0

    def _reset_state(self):
        self.counter               = 0
        self.sets_done             = 0
        self.stage                 = "UP"
        self.start_time            = None
        self.elapsed_time          = 0
        self.is_timing             = False
        self.plank_hold_start      = None
        self.plank_hold_time       = 0
        self.frames_in_down        = 0
        self.angle_buffer          = []
        self.current_rep_min_angle = 180.0
        self.current_rep_has_error = False
        self.rep_history           = []

    def _smooth_angle(self, angle):
        self.angle_buffer.append(angle)
        if len(self.angle_buffer) > ANGLE_SMOOTH_FRAMES:
            self.angle_buffer.pop(0)
        return float(np.mean(self.angle_buffer))

    def _classify_rep(self, min_angle, good_thresh, shallow_thresh):
        if min_angle <= good_thresh: return "good"
        elif min_angle <= shallow_thresh: return "acceptable"
        else: return "shallow"

    def _record_rep(self, good_thresh, shallow_thresh):
        self.counter += 1
        rep = {
            "rep":       self.counter,
            "min_angle": round(self.current_rep_min_angle, 1),
            "has_error": self.current_rep_has_error,
            "quality":   self._classify_rep(self.current_rep_min_angle, good_thresh, shallow_thresh),
        }
        self.rep_history.append(rep)
        self.current_rep_min_angle = 180.0
        self.current_rep_has_error = False
        return rep

    # ──核心：雙邊計數器整合 ──
    def _analyze_reps_dual(self, lms, left_pts, right_pts, down_thresh, up_thresh):
        ang_l = self.calculate_angle([lms[left_pts[0]].x, lms[left_pts[0]].y], [lms[left_pts[1]].x, lms[left_pts[1]].y], [lms[left_pts[2]].x, lms[left_pts[2]].y])
        ang_r = self.calculate_angle([lms[right_pts[0]].x, lms[right_pts[0]].y], [lms[right_pts[1]].x, lms[right_pts[1]].y], [lms[right_pts[2]].x, lms[right_pts[2]].y])
        avg_angle = (ang_l + ang_r) / 2
        
        if avg_angle < down_thresh:
            self.frames_in_down += 1
            if self.frames_in_down >= MIN_FRAMES_IN_PHASE:
                self.stage = "DOWN"
        if avg_angle > up_thresh and self.stage == "DOWN":
            self.stage = "UP"
            self.frames_in_down = 0
            # 注意：此處僅更新狀態，不執行 _record_rep 以免破壞 process_frame 結構
        return avg_angle

    # ──核心：雙邊持時器整合 ──
    def _analyze_hold_dual(self, lms, left_pts, right_pts, min_ang, max_ang):
        ang_l = self.calculate_angle([lms[left_pts[0]].x, lms[left_pts[0]].y], [lms[left_pts[1]].x, lms[left_pts[1]].y], [lms[left_pts[2]].x, lms[left_pts[2]].y])
        ang_r = self.calculate_angle([lms[right_pts[0]].x, lms[right_pts[0]].y], [lms[right_pts[1]].x, lms[right_pts[1]].y], [lms[right_pts[2]].x, lms[right_pts[2]].y])
        avg_angle = (ang_l + ang_r) / 2

        if min_ang < avg_angle < max_ang:
            if not self.is_timing:
                self.start_time = time.time() - self.elapsed_time
                self.is_timing = True
            if self.start_time is not None:
                self.elapsed_time = time.time() - self.start_time
        else:
            self.is_timing = False
        return avg_angle

    # ── 運動處理邏輯 ──

    def _process_squat(self, lm):
        side_view = self._detect_side_view(lm)
        # 整合雙邊偵測
        angle = self._analyze_reps_dual(lm, [23, 25, 27], [24, 26, 28], DOWN_ANGLE_THRESHOLD, UP_ANGLE_THRESHOLD)
        angle = self._smooth_angle(angle)
        error_type = None

        if not side_view:
            return {"angle": round(angle, 1), "status": "請轉向側面", "count": self.counter,
                    "timer": 0, "side_view": False, "error_type": None, "last_rep": None}

        # V1 強化錯誤偵測：腳跟離地
        if angle < 130 and (lm[27].y < lm[31].y - 0.05):
            error_type = "HEEL_OFF_GROUND"
            self.current_rep_has_error = True

        if self.stage == "DOWN" or angle < DOWN_ANGLE_THRESHOLD:
            self.current_rep_min_angle = min(self.current_rep_min_angle, angle)

        last_rep = self.rep_history[-1] if self.rep_history else None
        
        if self.stage == "DOWN": status = "正在下蹲"
        elif self.stage == "UP" and angle > UP_ANGLE_THRESHOLD: 
            if last_rep is None or last_rep['rep'] != self.counter + 1:
                last_rep = self._record_rep(good_thresh=90, shallow_thresh=SHALLOW_DEPTH_LIMIT)
            status = "完成一次深蹲！"
        else: status = "OK"

        if error_type == "HEEL_OFF_GROUND": status = "腳跟請貼緊地面！"

        return {"angle": round(angle, 1), "status": status, "count": self.counter,
                "timer": 0, "side_view": side_view, "error_type": error_type, "last_rep": last_rep}

    def _process_pushup(self, lm):
        side_view = self._detect_side_view(lm)
        angle = self._analyze_reps_dual(lm, [11, 13, 15], [12, 14, 16], PUSHUP_DOWN, PUSHUP_UP)
        angle = self._smooth_angle(angle)
        error_type = None

        if not side_view:
            return {"angle": round(angle, 1), "status": "請轉向側面", "count": self.counter,
                    "timer": 0, "side_view": False, "error_type": None, "last_rep": None}

        # V1 強化錯誤偵測：背部挺直
        back_angle = self.calculate_angle([lm[11].x, lm[11].y], [lm[23].x, lm[23].y], [lm[25].x, lm[25].y])
        if back_angle < 155:
            error_type = "BACK_BENT"
            self.current_rep_has_error = True

        if self.stage == "DOWN" or angle < PUSHUP_DOWN:
            self.current_rep_min_angle = min(self.current_rep_min_angle, angle)

        last_rep = self.rep_history[-1] if self.rep_history else None
        if self.stage == "UP" and angle > PUSHUP_UP:
            if last_rep is None or last_rep['rep'] != self.counter + 1:
                last_rep = self._record_rep(good_thresh=75, shallow_thresh=PUSHUP_DOWN)
            status = "動作標準！"
        else: status = "OK"

        if error_type == "BACK_BENT": status = "請將背部挺直！"

        return {"angle": round(angle, 1), "status": status, "count": self.counter,
                "timer": 0, "side_view": side_view, "error_type": error_type, "last_rep": last_rep}

    def _process_plank(self, lm):
        side_view = self._detect_side_view(lm)
        angle = self._analyze_hold_dual(lm, [11, 23, 27], [12, 24, 28], PLANK_STRAIGHT_MIN, 180)
        angle = self._smooth_angle(angle)
        error_type = None

        if angle < 160:
            error_type = "HIPS_TOO_HIGH"
            status = "屁股抬太高了！"
        else:
            status = f"維持中! {round(self.elapsed_time, 1)}s"

        return {"angle": round(angle, 1), "status": status, "count": int(self.elapsed_time),
                "timer": round(self.elapsed_time, 1), "side_view": side_view, "error_type": error_type, "last_rep": None}

    def _process_curl(self, lm):
        # 彎舉採較彎的那隻手 (MIN) 為準以確保品質
        ang_l = self.calculate_angle([lm[11].x, lm[11].y], [lm[13].x, lm[13].y], [lm[15].x, lm[15].y])
        ang_r = self.calculate_angle([lm[12].x, lm[12].y], [lm[14].x, lm[14].y], [lm[16].x, lm[16].y])
        angle = min(ang_l, ang_r)
        angle = self._smooth_angle(angle)
        error_type = None

        # V1 強化錯誤偵測：手肘晃動
        if angle < 100 and abs(lm[11].x - lm[13].x) > 0.1:
            error_type = "ELBOW_MOVING"
            self.current_rep_has_error = True

        if angle > CURL_EXTENDED: self.stage = "DOWN"
        if angle < CURL_CURLED and self.stage == "DOWN":
            self.stage = "UP"
            self._record_rep(good_thresh=45, shallow_thresh=CURL_CURLED)
            status = "動作完美！"
        else: status = "正在彎舉"

        if error_type == "ELBOW_MOVING": status = "手肘請固定在側！"

        return {"angle": round(angle, 1), "status": status, "count": self.counter,
                "timer": 0, "side_view": True, "error_type": error_type, "last_rep": self.rep_history[-1] if self.rep_history else None}

    def _process_situp(self, lm):
        side_view = self._detect_side_view(lm)
        angle = self._analyze_reps_dual(lm, [11, 23, 25], [12, 24, 26], SITUP_UP, SITUP_DOWN)
        angle = self._smooth_angle(angle)
        error_type = None

        if angle > 110 and self.stage == "DOWN":
            error_type = "INCOMPLETE_REP"
            status = "請盡量起身！"
        else: status = "OK"

        if angle > SITUP_DOWN: self.stage = "DOWN"
        elif angle < SITUP_UP and self.stage == "DOWN":
            self.stage = "UP"
            self._record_rep(good_thresh=75, shallow_thresh=SITUP_UP)

        return {"angle": round(angle, 1), "status": status, "count": self.counter,
                "timer": 0, "side_view": side_view, "error_type": error_type, "last_rep": self.rep_history[-1] if self.rep_history else None}

    # ── Public API ────────────────────────────────────────────────────────────

    def process_frame(self, frame, mode="squat"):
        if mode != self.current_mode:
            self.current_mode = mode
            self._reset_state()

        lm = self._extract_landmarks(frame)
        landmarks_list = []
        if lm:
            for l in lm:
                landmarks_list.append({
                    "x": l.x, "y": l.y, "z": getattr(l, "z", 0),
                    "visibility": self._get_vis(l),
                })

        if not lm:
            return (
                {"angle": 0, "status": "等待偵測", "count": self.counter,
                 "timer": round(self.elapsed_time, 1), "side_view": True, "error_type": None, "last_rep": None},
                landmarks_list,
            )

        dispatch = {
            "squat":     self._process_squat,
            "pushup":    self._process_pushup,
            "plank":     self._process_plank,
            "bicep_curl": self._process_curl,
            "situp":     self._process_situp,
        }
        handler  = dispatch.get(mode, self._process_squat)
        analysis = handler(lm)
        return analysis, landmarks_list

    # ── Session path (相容性保留) ────────────────

    def process_session(self, frames):
        frame_data = []
        for frame in frames:
            try:
                lm = self._extract_landmarks(frame)
                if lm is None: continue
                result = self._analyze_reps_dual(lm, [23,25,27], [24,26,28], DOWN_ANGLE_THRESHOLD, UP_ANGLE_THRESHOLD)
                frame_data.append({
                    "knee_angle":  round(result, 1),
                    "torso_angle": round(self._torso_angle(lm, "left"), 1),
                })
            except Exception: continue

        rep_count, rep_depths = self._count_reps(frame_data)
        knee_angles  = [fd["knee_angle"] for fd in frame_data]
        return {
            "frame_data":        frame_data,
            "rep_count":         rep_count,
            "rep_depths":        rep_depths,
            "valid_frame_count": len(frame_data),
            "min_knee_angle":    round(min(knee_angles), 1) if knee_angles else None,
            "avg_torso_angle":   round(float(np.mean([fd["torso_angle"] for fd in frame_data])), 1) if frame_data else None,
        }

    def _count_reps(self, frame_data):
        stage, rep_count, rep_depths, current_min = "UP", 0, [], 180.0
        for fd in frame_data:
            angle = fd["knee_angle"]
            if angle < DOWN_ANGLE_THRESHOLD:
                stage = "DOWN"
                current_min = min(current_min, angle)
            elif angle > UP_ANGLE_THRESHOLD and stage == "DOWN":
                stage = "UP"
                rep_count += 1
                rep_depths.append(round(current_min, 1))
                current_min = 180.0
        return rep_count, rep_depths

    def summarize_session(self, session_result):
        valid_frames    = session_result["valid_frame_count"]
        rep_count       = session_result["rep_count"]
        rep_depths      = session_result["rep_depths"]
        min_knee_angle  = session_result["min_knee_angle"]
        avg_torso_angle = session_result["avg_torso_angle"]

        if valid_frames < MIN_VALID_FRAMES:
            return {
                "type": "final_result", "status": "insufficient_data", "exercise": "squat",
                "rep_count": 0, "score": 20, "issues": ["insufficient_pose_data"],
                "metrics": {"valid_frame_count": valid_frames, "min_knee_angle": None, "avg_torso_angle": None},
                "feedback": "We couldn't detect enough clear body movement. Try stepping back so your full body is visible."
            }

        issues = []
        if rep_count == 0: issues.append("no_clear_rep_detected")
        depth_ref = round(float(np.mean(rep_depths)), 1) if rep_depths else min_knee_angle
        if depth_ref is not None and depth_ref > SHALLOW_DEPTH_LIMIT: issues.append("shallow_depth")
        if avg_torso_angle is not None and avg_torso_angle > FORWARD_LEAN_LIMIT: issues.append("forward_lean")

        score = 100
        score -= issues.count("no_clear_rep_detected") * 30
        score -= issues.count("shallow_depth") * 15
        score -= issues.count("forward_lean") * 15

        return {
            "type": "final_result", "status": "success", "exercise": "squat",
            "rep_count": rep_count, "score": max(score, 0), "issues": issues,
            "metrics": {"min_knee_angle": min_knee_angle, "avg_rep_depth": depth_ref, "avg_torso_angle": avg_torso_angle, "valid_frame_count": valid_frames},
        }

    @staticmethod
    def fallback_feedback(summary: dict) -> str:
        issues = summary.get("issues", [])
        rep_count = summary.get("rep_count", 0)
        parts = []
        if "insufficient_pose_data" in issues: return "Unable to analyze — ensure full body is visible."
        if "no_clear_rep_detected" in issues: parts.append("No clear squat rep was detected.")
        else: parts.append(f"You completed {rep_count} reps.")
        if "shallow_depth" in issues: parts.append("Try lowering your hips deeper.")
        if "forward_lean" in issues: parts.append("Keep your chest more upright.")
        if not issues: parts.append("Great form — keep it up!")
        return " ".join(parts)