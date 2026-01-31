import cv2
import mediapipe as mp
import numpy as np
import os
import uuid

# Initialize mediapipe modules
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

# Create output folder if it doesn’t exist
output_dir = 'Output Images'
os.makedirs(output_dir, exist_ok=True)

# Define a function for gesture classification
def get_hand_gesture(landmarks):
    # Get coordinates for each fingertip and base
    thumb_tip = landmarks[4]
    thumb_ip = landmarks[3]
    index_tip = landmarks[8]
    index_pip = landmarks[6]
    middle_tip = landmarks[12]
    middle_pip = landmarks[10]
    ring_tip = landmarks[16]
    ring_pip = landmarks[14]
    pinky_tip = landmarks[20]
    pinky_pip = landmarks[18]
    wrist = landmarks[0]

    # Convert to numpy arrays for vector math
    thumb_tip_y = thumb_tip.y
    index_tip_y = index_tip.y
    middle_tip_y = middle_tip.y
    ring_tip_y = ring_tip.y
    pinky_tip_y = pinky_tip.y

    # Gesture logic based on landmark positions (normalized)
    if (index_tip_y < index_pip.y and
        middle_tip_y < middle_pip.y and
        ring_tip_y < ring_pip.y and
        pinky_tip_y < pinky_pip.y):
        return "Papier"
    
    if (index_tip_y > index_pip.y and
        middle_tip_y > middle_pip.y and
        ring_tip_y > ring_pip.y and
        pinky_tip_y > pinky_pip.y):
        return "Kamień"

    # Thumbs up / down based on relative thumb direction
    if thumb_tip.y < wrist.y and all([
        index_tip.y > index_pip.y,
        middle_tip.y > middle_pip.y,
        ring_tip.y > ring_pip.y,
        pinky_tip.y > pinky_pip.y
    ]):
        return "Thumbs Up"

    if thumb_tip.y > wrist.y and all([
        index_tip.y > index_pip.y,
        middle_tip.y > middle_pip.y,
        ring_tip.y > ring_pip.y,
        pinky_tip.y > pinky_pip.y
    ]):
        return "Thumbs Down"

    # Peace sign ✌️
    if (index_tip_y < index_pip.y and
        middle_tip_y < middle_pip.y and
        ring_tip_y > ring_pip.y and
        pinky_tip_y > pinky_pip.y):
        return "Nożyce"

    # OK sign (index and thumb tips close together)
    dist = np.sqrt((thumb_tip.x - index_tip.x)**2 + (thumb_tip.y - index_tip.y)**2)
    if dist < 0.05 and middle_tip_y < middle_pip.y and ring_tip_y < ring_pip.y and pinky_tip_y < pinky_pip.y:
        return "OK 👌"

    return "Unknown"

# Initialize webcam
cap = cv2.VideoCapture(2)

# Start MediaPipe Hands
with mp_hands.Hands(min_detection_confidence=0.8,
                    min_tracking_confidence=0.5,
                    max_num_hands=2) as hands:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Convert the BGR image to RGB and flip for selfie view
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = cv2.flip(image, 1)
        image.flags.writeable = False

        # Process the frame
        results = hands.process(image)

        # Convert back to BGR
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        gesture_text = ""

        # Draw hand landmarks
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    image, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(121, 22, 76), thickness=2, circle_radius=4),
                    mp_drawing.DrawingSpec(color=(250, 44, 250), thickness=2, circle_radius=2),
                )

                # Gesture recognition
                gesture_text = get_hand_gesture(hand_landmarks.landmark)

                # Show gesture name
                cv2.putText(image, gesture_text, (10, 50), cv2.FONT_HERSHEY_SIMPLEX,
                            1, (0, 255, 0), 2, cv2.LINE_AA)
        
        # Show frame
        cv2.imshow('Hand Gesture Recognition', image)

        # Save frame
        cv2.imwrite(os.path.join(output_dir, f'{uuid.uuid1()}.jpg'), image)

        # Exit
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

# Cleanup
cap.release()
cv2.destroyAllWindows()
