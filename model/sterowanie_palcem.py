import cv2
import mediapipe as mp
import numpy as np

mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(2)

while True:
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)

    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)


    if results.multi_hand_landmarks:
        hand = results.multi_hand_landmarks[0]

        h, w, _ = frame.shape
        index_tip = hand.landmark[8]
        x = int(index_tip.x * w)
        y = int(index_tip.y * h)


        cv2.circle(frame, (x, y), 10, (0, 255, 0), -1)

 
        steering_x = (x - w/2) / (w/2)   
        steering_y = (y - h/2) / (h/2)  
        print("Steering - x:", round(steering_x,3), " y: ", round(steering_y,3))

    cv2.imshow("Sterowanie rekom", frame)
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
