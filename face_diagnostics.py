import time
import math
from pathlib import Path
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import streamlit as st

MODEL_PATH = Path(__file__).resolve().parent / "face_landmarker.task"


def _euclidean(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def _get_point(landmarks, idx, w, h):
    lm = landmarks[idx]
    return int(lm.x * w), int(lm.y * h)


def _calculate_ear(eye_indices, landmarks, w, h):
    pts = [_get_point(landmarks, idx, w, h) for idx in eye_indices]
    v1 = _euclidean(pts[1], pts[5])
    v2 = _euclidean(pts[2], pts[4])
    horiz = _euclidean(pts[0], pts[3])
    if horiz == 0:
        return 0.0, pts
    return (v1 + v2) / (2.0 * horiz), pts


def run_face_scan(duration_sec: int = 5, video_slot=None):
    """
    Runs the webcam for duration_sec seconds (default 5s), crops preview to a 1:1 square
    so it fits inside the 270x270 card slot, and computes EAR, PERCLOS, and fluid shift.
    """
    if not MODEL_PATH.is_file():
        st.warning("Place face_landmarker.task next to HMS_app.py to run scan.")
        return None

    RIGHT_EYE = [33, 160, 158, 133, 153, 144]
    LEFT_EYE = [362, 385, 387, 263, 373, 380]

    RIGHT_OUTER_EYE = 33
    LEFT_OUTER_EYE = 263
    RIGHT_CHEEK = 58
    LEFT_CHEEK = 288

    EAR_CLOSED_THRESHOLD = 0.22
    BASELINE_PUFFINESS_RATIO = 1.32

    base_options = python.BaseOptions(model_asset_path=str(MODEL_PATH))
    options = vision.FaceLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.IMAGE,
        num_faces=1,
        min_face_detection_confidence=0.6,
        min_tracking_confidence=0.6,
    )
    try:
        detector = vision.FaceLandmarker.create_from_options(options)
    except (OSError, RuntimeError, ValueError) as error:
        st.error(f"Failed to load MediaPipe model: {error}")
        return None

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        cap.release()
        detector.close()
        st.error("Camera not detected. Check connection or permissions.")
        return None

    if video_slot is None:
        video_slot = st.empty()

    ear_samples = []
    puffiness_samples = []
    closed_frames = 0

    start_time = time.monotonic()

    try:
        while True:
            elapsed = time.monotonic() - start_time
            if elapsed >= duration_sec:
                break

            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            orig_h, orig_w, _ = rgb_frame.shape
            side = min(orig_h, orig_w)
            y0 = (orig_h - side) // 2
            x0 = (orig_w - side) // 2
            rgb_frame = rgb_frame[y0:y0 + side, x0:x0 + side].copy()
            h, w, _ = rgb_frame.shape

            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            results = detector.detect(mp_image)

            if results.face_landmarks:
                lm = results.face_landmarks[0]

                # 1. Fatigue metric (EAR)
                r_ear, r_pts = _calculate_ear(RIGHT_EYE, lm, w, h)
                l_ear, l_pts = _calculate_ear(LEFT_EYE, lm, w, h)
                avg_ear = (r_ear + l_ear) / 2.0
                ear_samples.append(avg_ear)

                if avg_ear < EAR_CLOSED_THRESHOLD:
                    closed_frames += 1

                eye_color = (245, 158, 11) if avg_ear < EAR_CLOSED_THRESHOLD else (16, 185, 129)
                for pts in (r_pts, l_pts):
                    for i in range(len(pts)):
                        cv2.line(rgb_frame, pts[i], pts[(i + 1) % len(pts)], eye_color, 1)

                # 2. Fluid Shift metric
                p_eye_r = _get_point(lm, RIGHT_OUTER_EYE, w, h)
                p_eye_l = _get_point(lm, LEFT_OUTER_EYE, w, h)
                p_cheek_r = _get_point(lm, RIGHT_CHEEK, w, h)
                p_cheek_l = _get_point(lm, LEFT_CHEEK, w, h)

                eye_span = _euclidean(p_eye_r, p_eye_l)
                cheek_span = _euclidean(p_cheek_r, p_cheek_l)

                if eye_span > 0:
                    puffiness_samples.append(cheek_span / eye_span)

                cv2.line(rgb_frame, p_eye_r, p_eye_l, (59, 130, 246), 1)
                cv2.line(rgb_frame, p_cheek_r, p_cheek_l, (245, 158, 11), 2)

            remaining = max(0.0, duration_sec - elapsed)
            progress_ratio = min(1.0, elapsed / duration_sec)

            cv2.putText(
                rgb_frame,
                f"SCAN: {remaining:.1f}s",
                (14, 28),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (96, 165, 250),
                2,
            )

            bar_h = 6
            cv2.rectangle(rgb_frame, (0, h - bar_h), (w, h), (17, 22, 37), -1)
            cv2.rectangle(rgb_frame, (0, h - bar_h), (int(w * progress_ratio), h), (0, 50, 160), -1)

            video_slot.image(rgb_frame, width=270)

    finally:
        cap.release()
        detector.close()

    if not ear_samples or not puffiness_samples:
        st.toast("No face detected during scan. Ensure proper lighting and face the camera.")
        return None

    mean_ear = sum(ear_samples) / len(ear_samples)
    perclos = (closed_frames / len(ear_samples)) * 100.0
    mean_ratio = sum(puffiness_samples) / len(puffiness_samples)
    fluid_shift_pct = ((mean_ratio - BASELINE_PUFFINESS_RATIO) / BASELINE_PUFFINESS_RATIO) * 100.0

    return {
        "mean_ear": round(mean_ear, 3),
        "perclos": round(perclos, 1),
        "fluid_shift_pct": round(fluid_shift_pct, 1),
    }