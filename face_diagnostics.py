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


def run_face_scan(duration_sec: int = 5):
    """
    Uruchamia kamerę na określony czas (domyślnie 5s), oblicza EAR, udział klatek z zamkniętymi oczami
    i odchylenie proporcji twarzy przy użyciu MediaPipe Tasks API.
    """
    if not MODEL_PATH.is_file():
        st.warning("Umieść face_landmarker.task obok HMS_app.py, aby uruchomić skan.")
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
        st.error(f"Nie można otworzyć modelu MediaPipe: {error}")
        return None

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        cap.release()
        detector.close()
        st.error("Nie wykryto kamery. Sprawdź połączenie lub uprawnienia.")
        return None

    video_placeholder = st.empty()
    progress_bar = st.progress(0, text="Inicjalizacja skanera biometrycznego...")

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
            h, w, _ = rgb_frame.shape

            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            results = detector.detect(mp_image)

            if results.face_landmarks:
                lm = results.face_landmarks[0]

                # 1. Pomiar zmęczenia (EAR)
                r_ear, r_pts = _calculate_ear(RIGHT_EYE, lm, w, h)
                l_ear, l_pts = _calculate_ear(LEFT_EYE, lm, w, h)
                avg_ear = (r_ear + l_ear) / 2.0
                ear_samples.append(avg_ear)

                if avg_ear < EAR_CLOSED_THRESHOLD:
                    closed_frames += 1

                eye_color = (255, 75, 75) if avg_ear < EAR_CLOSED_THRESHOLD else (0, 230, 150)
                for pts in (r_pts, l_pts):
                    for i in range(len(pts)):
                        cv2.line(rgb_frame, pts[i], pts[(i + 1) % len(pts)], eye_color, 1)

                # 2. Pomiar Fluid Shift
                p_eye_r = _get_point(lm, RIGHT_OUTER_EYE, w, h)
                p_eye_l = _get_point(lm, LEFT_OUTER_EYE, w, h)
                p_cheek_r = _get_point(lm, RIGHT_CHEEK, w, h)
                p_cheek_l = _get_point(lm, LEFT_CHEEK, w, h)

                eye_span = _euclidean(p_eye_r, p_eye_l)
                cheek_span = _euclidean(p_cheek_r, p_cheek_l)

                if eye_span > 0:
                    puffiness_samples.append(cheek_span / eye_span)

                cv2.line(rgb_frame, p_eye_r, p_eye_l, (59, 130, 246), 1)
                cv2.line(rgb_frame, p_cheek_r, p_cheek_l, (255, 165, 0), 2)

            remaining = max(0.0, duration_sec - elapsed)
            cv2.putText(
                rgb_frame,
                f"BIOMETRIC SCAN: {remaining:.1f}s",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 230, 150),
                2,
            )

            video_placeholder.image(rgb_frame, use_container_width=True)
            progress_bar.progress(min(1.0, elapsed / duration_sec), text=f"Skanowanie twarzy... Pozostało {remaining:.1f} s")

    finally:
        cap.release()
        detector.close()
        video_placeholder.empty()
        progress_bar.empty()

    if not ear_samples or not puffiness_samples:
        st.warning("Nie udało się wykryć twarzy podczas skanowania. Upewnij się, że twarz jest dobrze oświetlona.")
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
