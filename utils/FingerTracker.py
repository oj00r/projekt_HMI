import cv2
import mediapipe as mp
import math

class FingerTracker:
    def __init__(self, cam_index=0):
        self.cam_index = cam_index
        self.cap = cv2.VideoCapture(self.cam_index)
        
        # Optymalizacja dla wydajności
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            model_complexity=0,      # Tryb Lite (szybki)
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        self.x = None
        self.y = None
        self.active = False
        self.pinch = False
        self.fist_closed = False # Nowa flaga
        self.results = None

    def update(self, screen_width, screen_height):
        if not self.cap.isOpened():
            self.active = False
            return

        ret, frame = self.cap.read()
        if not ret:
            self.active = False
            self.pinch = False
            self.fist_closed = False
            return

        # Zmniejszamy klatkę do analizy
        small_frame = cv2.resize(frame, (320, 240))
        frame_flipped = cv2.flip(small_frame, 1)
        img_rgb = cv2.cvtColor(frame_flipped, cv2.COLOR_BGR2RGB)
        
        self.active = False
        self.pinch = False
        self.fist_closed = False
        self.results = self.hands.process(img_rgb)

        if self.results.multi_hand_landmarks:
            hand = self.results.multi_hand_landmarks[0]
            lm = hand.landmark

            # --- 1. Pozycja kursora (czubek palca wskazującego) ---
            index_tip = lm[8]
            self.x = int(index_tip.x * screen_width)
            self.y = int(index_tip.y * screen_height)
            self.active = True

            # --- 2. Wykrywanie Uszczypnięcia (Pinch) ---
            thumb_tip = lm[4]
            # Obliczamy dystans na znormalizowanych współrzędnych (0.0 - 1.0)
            # Uwaga: Ponieważ obraz jest spłaszczony (320x240), dystans w osi Y jest "szybszy".
            # Korekta na proporcje ekranu (zakładając typowe 4:3 dla kamerki)
            dx = (thumb_tip.x - index_tip.x)
            dy = (thumb_tip.y - index_tip.y) * (320/240) 
            distance = math.hypot(dx, dy)
            
            # Próg uszczypnięcia (może wymagać dostrojenia w zależności od kamery)
            self.pinch = distance < 0.07 

            # --- 3. Wykrywanie Pięści (NOWOŚĆ) ---
            # Sprawdzamy, czy czubki 4 palców są niżej (większe Y) niż ich stawy środkowe (PIP)
            # Indeksy: 8 (czubek) vs 6 (staw), 12 vs 10, 16 vs 14, 20 vs 18
            fingers_folded = 0
            if lm[8].y > lm[6].y: fingers_folded += 1  # Wskazujący
            if lm[12].y > lm[10].y: fingers_folded += 1 # Środkowy
            if lm[16].y > lm[14].y: fingers_folded += 1 # Serdeczny
            if lm[20].y > lm[18].y: fingers_folded += 1 # Mały

            # Jeśli co najmniej 3 z 4 palców są zgięte, uznajemy to za pięść
            if fingers_folded >= 3:
                self.fist_closed = True

    def get_pos(self):
        if self.active:
            return self.x, self.y
        return None

    def is_pinch(self):
        return self.pinch

    # Nowa metoda dostępowa
    def is_fist(self):
        return self.fist_closed

    def release(self):
        if self.cap.isOpened():
            self.cap.release()

    def reinit(self):
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.cam_index)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    
    def get_raw_landmarks(self):
        if self.results and self.results.multi_hand_landmarks:
            return self.results.multi_hand_landmarks[0]
        return None