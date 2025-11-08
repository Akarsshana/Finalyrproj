import cv2
import mediapipe as mp
import time

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

# Fingertip landmark indices
THUMB_TIP = 4
FINGERTIPS = [8, 12, 16, 20]  # Index, Middle, Ring, Pinky

current_target_index = 0
tap_start_time = None
tap_times = []

def distance(p1, p2):
    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5

cap = cv2.VideoCapture(0)

while True:
    success, img = cap.read()
    if not success:
        break

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    h, w, _ = img.shape
    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            lm_list = []
            for id, lm in enumerate(handLms.landmark):
                lm_list.append((int(lm.x * w), int(lm.y * h)))

            thumb_tip = lm_list[THUMB_TIP]
            target_tip = lm_list[FINGERTIPS[current_target_index]]

            # Check distance between thumb and the current target finger
            dist_to_target = distance(thumb_tip, target_tip)

            # Make sure other fingers are NOT touching the thumb
            others_far = True
            for i, fid in enumerate(FINGERTIPS):
                if i != current_target_index:
                    dist = distance(thumb_tip, lm_list[fid])
                    if dist < 40:  # Threshold distance
                        others_far = False
                        break

            cv2.putText(img, f"Target: {['Index','Middle','Ring','Pinky'][current_target_index]}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

            if dist_to_target < 40 and others_far:
                if tap_start_time is None:
                    tap_start_time = time.time()
            else:
                if tap_start_time:
                    tap_duration = time.time() - tap_start_time
                    tap_times.append((FINGERTIPS[current_target_index], tap_duration))
                    print(f"Tapped {['Index','Middle','Ring','Pinky'][current_target_index]} in {tap_duration:.2f} sec")
                    tap_start_time = None
                    current_target_index += 1
                    if current_target_index >= len(FINGERTIPS):
                        print("\n--- Tap Summary ---")
                        for f_id, duration in tap_times:
                            label = ['Index', 'Middle', 'Ring', 'Pinky'][FINGERTIPS.index(f_id)]
                            print(f"{label}: {duration:.2f} sec")
                        print("-------------------\n")
                        current_target_index = 0
                        tap_times = []

            mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)

    cv2.imshow("Finger Tap Exercise", img)
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
