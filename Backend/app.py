import cv2
import mediapipe as mp
import numpy as np
import base64
from flask import Flask
from flask_socketio import SocketIO

import threading

# =====================================================
# 🧩 Flask + SocketIO Setup
# =====================================================
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# =====================================================
# 🧠 MediaPipe Models
# =====================================================
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands
mp_pose = mp.solutions.pose

hands = mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# =====================================================
# 🎥 Camera Setup
# =====================================================
cap = cv2.VideoCapture(0)
lock = threading.Lock()
# =====================================================
# ▶️ Run flags (REQUIRED to stop loops on Retry)
# =====================================================

run_openclose = False
run_rotation = False
run_joinhands = False



# =====================================================
# 📊 Shared States
# =====================================================
open_close_count = 0
hand_state_prev = "Unknown"

rotation_count = 0
previous_angle = None
rotated_once = False

rep_count = 0
hands_above_head = False
accuracy = 0

# =====================================================
# 🧮 Helper Functions
# =====================================================

def classify_hand_state(landmarks):
    """Detect whether hand is open, closed, or half closed."""
    global hand_state_prev, open_close_count
    finger_tips = [8, 12, 16, 20]
    curled_fingers = sum(1 for tip in finger_tips if landmarks.landmark[tip].y > landmarks.landmark[tip - 2].y)

    if curled_fingers == 0:
        current_state = "Fully Open"
    elif curled_fingers == 4:
        current_state = "Fully Closed"
    else:
        current_state = "Half Closed"

    if hand_state_prev == "Fully Closed" and current_state == "Fully Open":
        open_close_count += 1

    hand_state_prev = current_state
    return current_state


def calculate_wrist_angle(landmarks):
    """Calculate wrist rotation angle."""
    wrist = landmarks.landmark[0]
    middle_mcp = landmarks.landmark[9]
    dx = middle_mcp.x - wrist.x
    dy = middle_mcp.y - wrist.y
    angle = np.arctan2(dy, dx) * 180 / np.pi
    return angle


def euclidean_distance(pt1, pt2):
    return np.linalg.norm(np.array(pt1) - np.array(pt2))


def calculate_accuracy(left, right):
    """Generic accuracy measure for proximity."""
    dist = euclidean_distance(left, right)
    normalized = min(dist / 0.25, 1.0)
    return round((1 - normalized) * 100, 2)
# ===============================
# 🛑 STOP ALL EXERCISES (ADD HERE)
# ===============================
def stop_all():
    global run_openclose, run_rotation, run_joinhands
    run_openclose = False
    run_rotation = False
    run_joinhands = False

# =====================================================
# ✋ EXERCISE 1 → Hand Open-Close
# =====================================================
@socketio.on("start_openclose")
def start_openclose():
    global run_openclose, open_close_count, hand_state_prev

    stop_all()
    run_openclose = True
    open_close_count = 0
    hand_state_prev = "Unknown"

    print("▶️ Open–Close Exercise Started")

    while run_openclose:
        with lock:
            success, image = cap.read()
        if not success:
            continue

        image = cv2.flip(image, 1)
        results = hands.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        state = "No Hand"
        if results.multi_hand_landmarks:
            for hl in results.multi_hand_landmarks:
                state = classify_hand_state(hl)
                mp_drawing.draw_landmarks(image, hl, mp_hands.HAND_CONNECTIONS)

        cv2.putText(image, f"State: {state}", (30, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2)
        cv2.putText(image, f"Count: {open_close_count}", (30, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)

        _, buffer = cv2.imencode(".jpg", image)
        socketio.emit("video_feed", {
            "frame": base64.b64encode(buffer).decode(),
            "count": open_close_count
        })

        @socketio.on("stop_openclose")
        def stop_openclose():
            global run_openclose
            run_openclose = False
            print("🛑 Open–Close stopped")

@socketio.on("start_rotation")
def start_rotation():
    global run_rotation, rotation_count, previous_angle, rotated_once

    stop_all()
    run_rotation = True
    rotation_count = 0
    previous_angle = None
    rotated_once = False

    print("▶️ Wrist Rotation Started")

    while run_rotation:
        with lock:
            success, image = cap.read()
        if not success:
            continue

        image = cv2.flip(image, 1)
        results = hands.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        if results.multi_hand_landmarks:
            for hl in results.multi_hand_landmarks:
                angle = calculate_wrist_angle(hl)

                if previous_angle is not None:
                    diff = angle - previous_angle
                    if diff > 180: diff -= 360
                    if diff < -180: diff += 360

                    if abs(diff) > 30 and not rotated_once:
                        rotation_count += 1
                        rotated_once = True
                    elif abs(diff) < 10:
                        rotated_once = False

                previous_angle = angle
                mp_drawing.draw_landmarks(image, hl, mp_hands.HAND_CONNECTIONS)

        cv2.putText(image, f"Rotations: {rotation_count}", (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2)

        _, buffer = cv2.imencode(".jpg", image)
        socketio.emit("rotation_feed", {
            "image": base64.b64encode(buffer).decode(),
            "count": rotation_count
        })
@socketio.on("stop_rotation")
def stop_rotation():
    global run_rotation
    run_rotation = False
    print("🛑 Rotation stopped")




@socketio.on("stop_video")
def stop_video():
    global run_rotation
    run_rotation = False
    print("🛑 Video stopped")



# =====================================================
# 🙌 EXERCISE 3 → Arm Raise + Join Hands (POSE-based)
# =====================================================
@socketio.on("start_joinhands")
def start_joinhands():
    stop_all()

    global run_joinhands, rep_count, hands_above_head, accuracy

    run_joinhands = True
    rep_count = 0
    hands_above_head = False
    accuracy = 0

    print("▶️ Arm Raise + Join Hands Started")

    while run_joinhands:


        with lock:
            success, frame = cap.read()
        if not success:
            continue

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image_rgb)

        if results.pose_landmarks:
            lm = results.pose_landmarks.landmark
            left_wrist = (lm[mp_pose.PoseLandmark.LEFT_WRIST].x, lm[mp_pose.PoseLandmark.LEFT_WRIST].y)
            right_wrist = (lm[mp_pose.PoseLandmark.RIGHT_WRIST].x, lm[mp_pose.PoseLandmark.RIGHT_WRIST].y)
            nose_y = lm[mp_pose.PoseLandmark.NOSE].y

            avg_y = (left_wrist[1] + right_wrist[1]) / 2
            accuracy = calculate_accuracy(left_wrist, right_wrist) if avg_y < nose_y else 0

            # Detect raise
            if avg_y < nose_y and not hands_above_head:
                hands_above_head = True
            # Detect lower
            elif avg_y > nose_y + 0.15 and hands_above_head:
                if accuracy >= 80:
                    rep_count += 1
                hands_above_head = False

            mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        cv2.putText(frame, f"Reps: {rep_count}", (50, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 3)
        cv2.putText(frame, f"Accuracy: {accuracy:.1f}%", (50, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 128, 255), 3)

        _, buffer = cv2.imencode(".jpg", frame)
        socketio.emit("joinhands_feed", {
            "frame": base64.b64encode(buffer).decode("utf-8"),
            "count": rep_count,
            "accuracy": accuracy
            
        })
@socketio.on("stop_joinhands")
def stop_joinhands():
    global run_joinhands
    run_joinhands = False
    print("🛑 Join hands exercise stopped")


        

# =====================================================
# 🚀 Run Server
# =====================================================
if __name__ == "__main__":
    print("✅ MotionAid Flask Backend Running → http://localhost:5000")
    socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)
