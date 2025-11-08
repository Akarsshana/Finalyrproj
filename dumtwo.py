import cv2
import mediapipe as mp

mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

with mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1,
                           refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5) as face_mesh:
    
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            break
        
        image = cv2.flip(image, 1)
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                # Draw face mesh landmarks
                mp_drawing.draw_landmarks(image, face_landmarks, mp_face_mesh.FACEMESH_CONTOURS)

                # Get key points to place 3D glasses (around eyes)
                left_eye = face_landmarks.landmark[33]   # Left eye outer
                right_eye = face_landmarks.landmark[263] # Right eye outer

                ih, iw, _ = image.shape
                lx, ly = int(left_eye.x * iw), int(left_eye.y * ih)
                rx, ry = int(right_eye.x * iw), int(right_eye.y * ih)

                # Draw a "virtual glasses frame"
                cv2.rectangle(image, (lx-30, ly-20), (rx+30, ry+20), (0,255,255), 3)

        cv2.imshow('Face Mesh 3D Object Tracking', image)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
