import cv2
import mediapipe as mp
import numpy as np
import base64
from flask import Flask
from flask_socketio import SocketIO

# Initialize Flask app
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Enable WebSocket communication with frontend

# MediaPipe setup for hand tracking
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

# Open webcam for video capture
cap = cv2.VideoCapture(0)
hands = mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Variables to track wrist rotation
previous_angle = None
rotation_count = 0
rotation_direction = None  # Clockwise or Anti-clockwise
rotated_once = False

# Function to calculate wrist rotation angle
def calculate_wrist_angle(landmarks):
    # Using wrist (0) and middle finger MCP (9) to estimate rotation
    wrist = landmarks.landmark[0]
    middle_mcp = landmarks.landmark[9]

    dx = middle_mcp.x - wrist.x
    dy = middle_mcp.y - wrist.y
    angle = np.arctan2(dy, dx) * 180 / np.pi  # Angle in degrees
    return angle

# WebSocket event handler to start video processing for wrist rotations
@socketio.on("start_rotation")
def start_rotation():
    global rotation_count, previous_angle, rotated_once

    while True:
        success, image = cap.read()
        if not success:
            continue

        image = cv2.flip(image, 1)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = hands.process(image_rgb)

        wrist_rotation_status = "No Hand Detected"
        node_color = (0, 0, 0)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                current_angle = calculate_wrist_angle(hand_landmarks)

                if previous_angle is not None:
                    diff = current_angle - previous_angle

                    # Normalize difference
                    if diff > 180:
                        diff -= 360
                    elif diff < -180:
                        diff += 360

                    # Detect full rotation when wrist rotates beyond certain threshold
                    if abs(diff) > 30:
                        if not rotated_once:
                            rotation_count += 1
                            rotated_once = True
                else:
                    rotated_once = False

                previous_angle = current_angle
                wrist_rotation_status = f"Rotations: {rotation_count}"
                node_color = (255, 0, 255)

                # Draw landmarks
                mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                                          mp_drawing.DrawingSpec(color=node_color, thickness=2, circle_radius=4),
                                          mp_drawing.DrawingSpec(color=node_color, thickness=2, circle_radius=2))

        # Reset rotated_once if hand not detected
        if not results.multi_hand_landmarks:
            rotated_once = False
            previous_angle = None

        # Display info
        cv2.putText(image, wrist_rotation_status, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, node_color, 2)

        # Encode frame and send
        _, buffer = cv2.imencode(".jpg", image)
        frame_data = base64.b64encode(buffer).decode("utf-8")

        # Emit rotation count
        socketio.emit("rotation_feed", {"image": frame_data, "count": rotation_count})

# Start server
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
