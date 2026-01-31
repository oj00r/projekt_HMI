import cv2
import mediapipe as mp
import pygame
import math

class FingerTracker:
    def __init__(self, cam_index=0):
        self.cam_index = cam_index  # Zapamiętujemy indeks kamery
        self.cap = cv2.VideoCapture(self.cam_index)
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1)
        self.x = None
        self.y = None
        self.active = False
        self.pinch = False
        self.results = None

    def update(self, screen_width, screen_height):
        # Jeśli kamera nie jest otwarta, nic nie rób
        if not self.cap.isOpened():
            self.active = False
            return

        ret, frame = self.cap.read()
        if not ret:
            self.active = False
            self.pinch = False
            return

        frame = cv2.flip(frame, 1)
        # Konwersja kolorów jest ważna dla MediaPipe
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        self.active = False
        self.pinch = False
        self.results = self.hands.process(img_rgb)

        if self.results.multi_hand_landmarks:
            hand = self.results.multi_hand_landmarks[0]

            index_tip = hand.landmark[8]
            thumb_tip = hand.landmark[4]

            self.x = int(index_tip.x * screen_width)
            self.y = int(index_tip.y * screen_height)
            self.active = True

            dx = thumb_tip.x - index_tip.x
            dy = thumb_tip.y - index_tip.y
            distance = math.hypot(dx, dy)
            self.pinch = distance < 0.04

    def get_pos(self):
        if self.active:
            return self.x, self.y
        return None

    def is_pinch(self):
        return self.pinch

    def release(self):
        if self.cap.isOpened():
            self.cap.release()
            # Nie niszczymy okien tutaj, bo to może zamknąć okno pygame
            # cv2.destroyAllWindows()

    # Nowa metoda do ponownego uruchomienia kamery po powrocie z gry
    def reinit(self):
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.cam_index)
    
    def get_raw_landmarks(self):
        if self.results and self.results.multi_hand_landmarks:
            return self.results.multi_hand_landmarks[0]
        return None