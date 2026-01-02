import cv2
import mediapipe as mp
import numpy as np
import base64

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

cap = cv2.VideoCapture(0)

run_joinhands = False
rep_count = 0
hands_above = False
accuracy = 0


def euclidean_distance(a, b):
    return np.linalg.norm(np.array(a) - np.array(b))


def calculate_accuracy(l, r):
    d = euclidean_distance(l, r)
    return max(0, 100 - (d / 0.25) * 100)


def joinhands_loop(socketio):
    global run_joinhands, rep_count, hands_above, accuracy

    rep_count = 0
    hands_above = False
    run_joinhands = True

    while run_joinhands:
        success, frame = cap.read()
        if not success:
            continue

        frame = cv2.flip(frame, 1)
        results = pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        if results.pose_landmarks:
            lm = results.pose_landmarks.landmark

            left = (lm[mp_pose.PoseLandmark.LEFT_INDEX].x,
                    lm[mp_pose.PoseLandmark.LEFT_INDEX].y)
            right = (lm[mp_pose.PoseLandmark.RIGHT_INDEX].x,
                     lm[mp_pose.PoseLandmark.RIGHT_INDEX].y)

            ear_y = (lm[mp_pose.PoseLandmark.LEFT_EAR].y +
                     lm[mp_pose.PoseLandmark.RIGHT_EAR].y) / 2

            avg_y = (left[1] + right[1]) / 2
            accuracy = calculate_accuracy(left, right)

            if avg_y < ear_y and not hands_above:
                hands_above = True

            elif avg_y > ear_y + 0.08 and hands_above:
                if accuracy >= 80:
                    rep_count += 1
                hands_above = False

            mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        _, buffer = cv2.imencode(".jpg", frame)
        socketio.emit("joinhands_feed", {
            "frame": base64.b64encode(buffer).decode(),
            "count": rep_count,
            "accuracy": accuracy
        })

        socketio.sleep(0.03)


def stop_joinhands_loop():
    global run_joinhands
    run_joinhands = False
