import cv2
import mediapipe as mp
import pygame
import math


class FingerTracker:
    def __init__(self, cam_index=0):
        self.cap = cv2.VideoCapture(cam_index)
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1)
        self.x = None
        self.y = None
        self.active = False
        self.pinch = False  # informacja o pinch
        self.results = None # Dodaj to

    def update(self, screen_width, screen_height):
        ret, frame = self.cap.read()
        if not ret:
            self.active = False
            self.pinch = False
            return

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(img_rgb)

        self.active = False
        self.pinch = False
        self.results = self.hands.process(img_rgb) 

        if results.multi_hand_landmarks:
            hand = results.multi_hand_landmarks[0]

            # landmarky
            index_tip = hand.landmark[8]
            thumb_tip = hand.landmark[4]

            # mapowanie do pygame
            self.x = int(index_tip.x * screen_width)
            self.y = int(index_tip.y * screen_height)
            self.active = True

            # pinch – odległość kciuka od palca wskazującego
            dx = thumb_tip.x - index_tip.x
            dy = thumb_tip.y - index_tip.y
            distance = math.hypot(dx, dy)
            self.pinch = distance < 0.04  # próg do testów, możesz zmienić

    def get_pos(self):
        if self.active:
            return self.x, self.y
        return None

    def is_pinch(self):
        return self.pinch

    def release(self):
        self.cap.release()
        cv2.destroyAllWindows()
    
    def get_raw_landmarks(self):
        if self.results and self.results.multi_hand_landmarks:
            return self.results.multi_hand_landmarks[0]
        return None