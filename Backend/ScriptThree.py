import cv2
import mediapipe as mp
import numpy as np
import base64
from flask import Flask
from flask_socketio import SocketIO

# Flask setup
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# MediaPipe Pose setup
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Camera
cap = cv2.VideoCapture(0)

# States
hold_time = 0
max_hold = 0
accuracy = 0

# Helper Functions
def euclidean_distance(pt1, pt2):
    return np.linalg.norm(np.array(pt1) - np.array(pt2))

def calculate_accuracy(left_wrist, right_wrist):
    dist = euclidean_distance(left_wrist, right_wrist)
    normalized = min(dist / 0.3, 1.0)
    acc = (1 - normalized) * 100
    return round(acc, 2)

# Main Exercise Logic
@socketio.on("start_joinhands")  # ✅ aligned with frontend
def start_joinhands():
    global accuracy, hold_time, max_hold

    print("▶️ Arm Raise + Hold Duration Tracking Started")
    hold_time = 0
    max_hold = 0

    while True:
        success, frame = cap.read()
        if not success:
            continue

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        results = pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        if results.pose_landmarks:
            lm = results.pose_landmarks.landmark

            # Fingertip points
            left_index = (lm[mp_pose.PoseLandmark.LEFT_INDEX].x, lm[mp_pose.PoseLandmark.LEFT_INDEX].y)
            right_index = (lm[mp_pose.PoseLandmark.RIGHT_INDEX].x, lm[mp_pose.PoseLandmark.RIGHT_INDEX].y)

            # Reference lines
            left_ear_y = lm[mp_pose.PoseLandmark.LEFT_EAR].y
            right_ear_y = lm[mp_pose.PoseLandmark.RIGHT_EAR].y
            ear_y = (left_ear_y + right_ear_y) / 2
            avg_y = (left_index[1] + right_index[1]) / 2

            # Accuracy when hands are high
            accuracy = calculate_accuracy(left_index, right_index) if avg_y < ear_y else 0

            # Hold tracking
            if avg_y < ear_y:
                hold_time += 1
                max_hold = max(max_hold, hold_time)
            else:
                hold_time = 0

            # Draw Pose
            mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            cv2.line(frame, (0, int(ear_y * h)), (w, int(ear_y * h)), (255, 0, 0), 2)

        # Display info
        cv2.putText(frame, f"Hold Time: {hold_time/30:.1f}s", (50, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 3)
        cv2.putText(frame, f"Accuracy: {accuracy:.1f}%", (50, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 128, 255), 3)

        # Emit frame and stats
        _, buffer = cv2.imencode(".jpg", frame)
        socketio.emit("joinhands_feed", {
            "frame": base64.b64encode(buffer).decode("utf-8"),
            "hold_time": round(hold_time / 30, 1),
            "accuracy": accuracy
        })

        socketio.sleep(0.03)

if __name__ == "__main__":
    print("🚀 Flask backend running at http://localhost:5000")
    socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)
