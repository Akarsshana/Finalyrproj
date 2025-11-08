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
mp_drawing = mp.solutions.drawing_utils  # Utility for drawing hand landmarks
mp_hands = mp.solutions.hands  # Hand tracking module

# Open webcam for video capture
cap = cv2.VideoCapture(0)  # Capture video from default camera
hands = mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)  # Initialize hand tracking model

# Variables to track hand states and count hand open-close cycles
hand_state_prev = "Unknown"  # Previous state of the hand
open_close_count = 0  # Counter for hand open-close actions

# Function to classify the current state of the hand (Open, Half-Closed, or Closed)
def classify_hand_state(landmarks):
    global hand_state_prev, open_close_count  # Access global variables

    finger_tips = [8, 12, 16, 20]  # Indices of fingertip landmarks
    curled_fingers = sum(1 for tip in finger_tips if landmarks.landmark[tip].y > landmarks.landmark[tip - 2].y)  
    # Count the number of fingers that are curled (lower than their corresponding knuckles)

    # Determine the hand state based on the number of curled fingers
    if curled_fingers == 0:
        current_state = "Fully Open"
    elif curled_fingers == 4:
        current_state = "Fully Closed"
    else:
        current_state = "Half Closed"

    # Count the number of open-close cycles
    if hand_state_prev == "Fully Closed" and current_state == "Fully Open":
        open_close_count += 1  # Increment count when hand transitions from fully closed to open

    hand_state_prev = current_state  # Update previous hand state
    return current_state  # Return the current state

# WebSocket event handler to start video processing
@socketio.on("start_video")
def start_video():
    global open_close_count  # Access global counter

    while True:
        success, image = cap.read()  # Capture frame from webcam
        if not success:
            continue  # Skip frame if capture failed

        image = cv2.flip(image, 1)  # Flip the image horizontally for natural view
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # Convert frame to RGB format
        results = hands.process(image_rgb)  # Detect hands in the frame

        hand_state = "Unknown"  # Default hand state
        node_color = (0, 0, 0)  # Default landmark color (black)

        if results.multi_hand_landmarks:  # If hands are detected
            for hand_landmarks in results.multi_hand_landmarks:
                hand_state = classify_hand_state(hand_landmarks)  # Get the current hand state

                # Set colors based on hand state
                if hand_state == "Fully Open":
                    node_color = (0, 255, 0)  # Green for fully open
                elif hand_state == "Half Closed":
                    node_color = (0, 255, 255)  # Yellow for half closed
                elif hand_state == "Fully Closed":
                    node_color = (0, 0, 255)  # Red for fully closed

                # Draw hand landmarks with the determined color
                mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                                          mp_drawing.DrawingSpec(color=node_color, thickness=2, circle_radius=4),
                                          mp_drawing.DrawingSpec(color=node_color, thickness=2, circle_radius=2))

        # Display hand state text on the frame
        cv2.putText(image, f"Hand: {hand_state}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, node_color, 2)
        # Display open-close count on the frame
        cv2.putText(image, f"Open-Close Count: {open_close_count}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

        # Encode frame as JPEG image
        _, buffer = cv2.imencode(".jpg", image)
        frame_data = base64.b64encode(buffer).decode("utf-8")  # Convert to base64 string

        # Send the processed video frame and open-close count to the frontend
        socketio.emit("video_feed", {"frame": frame_data, "count": open_close_count})

# Run the Flask app with WebSocket support
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)  # Start the server on port 5000
