import cv2
import mediapipe as mp
import pygame
import numpy as np
import math

class KinectGame:
    def __init__(self, screen, cam_index=0):
        self.screen = screen
        self.cam_index = cam_index
        
        # Inicjalizacja MediaPipe Pose
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.pose = self.mp_pose.Pose(model_complexity=1, min_detection_confidence=0.5)
        
        self.score = 0
        self.pose_start_time = pygame.time.get_ticks()
        self.running = True

        # Czcionki (zdefiniowane raz dla wydajności)
        self.font = pygame.font.SysFont(None, 48)
        self.big_font = pygame.font.SysFont(None, 120)

        
        self.pose_templates = [
            {"img_path": "./assets/taniec/poza1.png", "type": "hips"},
            {"img_path": "./assets/taniec/poza2.png", "type": "clapping"},
            {"img_path": "./assets/taniec/poza3.png", "type": "samolot1"},
            {"img_path": "./assets/taniec/poza4.png", "type": "samolot2"}
        ]

        self.images = []
        for p in self.pose_templates:
            try:
                img = pygame.image.load(p["img_path"]).convert_alpha()
                img = pygame.transform.scale(img, (300, 380)) 
                self.images.append(img)
            except:
                fallback = pygame.Surface((300, 380))
                fallback.fill((200, 0, 0))
                self.images.append(fallback)

    def get_dist(self, p1, p2):
        """Oblicza odległość euklidesową między dwoma punktami."""
        return math.hypot(p1.x - p2.x, p1.y - p2.y)

    def run(self):
        capture = cv2.VideoCapture(self.cam_index)

        game_absolute_start = pygame.time.get_ticks()


        while self.running:
            now = pygame.time.get_ticks()
            time_elapsed = now - self.pose_start_time
            
            # Reset cyklu co 3 minuty
            if time_elapsed > 180000:
                self.pose_start_time = now
                time_elapsed = 0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    # --- NOWA LOGIKA RESETU ---
                    if event.key == pygame.K_r:
                        self.score = 0
                        self.pose_start_time = pygame.time.get_ticks()
                        game_absolute_start = pygame.time.get_ticks()
                        print("Gra została zresetowana!")
                        pygame.mixer.music.play(-1)
                
                         

            ret, frame = capture.read()
            if not ret: break

            # Przetwarzanie obrazu
            frame = cv2.flip(frame, 1)
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.pose.process(image_rgb)

            # --- RYSOWANIE SZKIELETU ---
            if results.pose_landmarks:
                self.mp_drawing.draw_landmarks(
                    image_rgb, 
                    results.pose_landmarks, 
                    self.mp_pose.POSE_CONNECTIONS,
                    self.mp_drawing.DrawingSpec(color=(0,255,0), thickness=2, circle_radius=2),
                    self.mp_drawing.DrawingSpec(color=(255,255,255), thickness=2, circle_radius=2)
                )

            # Konwersja na Surface Pygame i wyświetlanie tła (Kamera + Szkielet)
            shape = image_rgb.shape[1::-1]
            frame_surface = pygame.image.frombuffer(image_rgb.tobytes(), shape, "RGB")
            frame_surface = pygame.transform.scale(frame_surface, (self.screen.get_width(), self.screen.get_height()))
            self.screen.blit(frame_surface, (0, 0))

            # --- LOGIKA SPRAWDZANIA POZY I WYŚWIETLANIA OBRAZKÓW ---
            if results.pose_landmarks:
                lm = results.pose_landmarks.landmark
                
                # Pobieranie punktów kluczowych
                l_wrist = lm[self.mp_pose.PoseLandmark.LEFT_WRIST]
                r_wrist = lm[self.mp_pose.PoseLandmark.RIGHT_WRIST]
                l_shoulder = lm[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
                r_shoulder = lm[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
                l_eye = lm[self.mp_pose.PoseLandmark.LEFT_EYE]
                r_eye = lm[self.mp_pose.PoseLandmark.RIGHT_EYE]
                l_hip = lm[self.mp_pose.PoseLandmark.LEFT_HIP]
                r_hip = lm[self.mp_pose.PoseLandmark.RIGHT_HIP]
                l_elbow = lm[self.mp_pose.PoseLandmark.LEFT_ELBOW]
                r_elbow = lm[self.mp_pose.PoseLandmark.RIGHT_ELBOW]


                if time_elapsed <= 15500:

                    # klaskanie
                    if (5701 <= time_elapsed < 6700 or
                        7601 <= time_elapsed < 8400 or
                        9601 <= time_elapsed < 10400 or
                        11601 <= time_elapsed < 12200 or
                        13401 <= time_elapsed < 14200):
                        # Rysowanie instrukcji
                        pygame.draw.rect(self.screen, (255, 255, 255), (15, 15, 310, 390), 3)
                        self.screen.blit(self.images[1], (20, 20))
                        
                        # Logika: Ręce wysoko i po lewej
                        rece_wysoko = l_wrist.y < l_shoulder.y and r_wrist.y < r_shoulder.y
                        rece_po_lewej = l_wrist.x < l_eye.x and r_wrist.x < r_eye.x

                        if rece_wysoko and rece_po_lewej:
                            self.score += 1
                            success_txt = self.big_font.render("DOBRZE!", True, (0, 255, 0))
                            self.screen.blit(success_txt, (20, 410))

                    # biodra
                    elif (6701 <= time_elapsed < 7600 or 
                        8401 <= time_elapsed < 9600 or 
                        10401 <= time_elapsed < 11600 or 
                        12201 <= time_elapsed < 13400 or 
                        14201 <= time_elapsed < 15500):
                        # Rysowanie instrukcji
                        pygame.draw.rect(self.screen, (255, 255, 255), (15, 15, 310, 390), 3)
                        self.screen.blit(self.images[0], (20, 20))
                        
                        # Logika
                        elbows_visible = l_elbow.visibility > 0.5 and r_elbow.visibility > 0.5
                        dist_l = self.get_dist(l_wrist, l_hip)
                        dist_r = self.get_dist(r_wrist, r_hip)
                        elbows_out = l_elbow.y < l_wrist.y and r_elbow.y < r_wrist.y

                        if dist_l < 0.2 and dist_r < 0.2 and elbows_out and elbows_visible:
                            self.score += 1
                            success_txt = self.big_font.render("DOBRZE!", True, (0, 255, 0))
                            self.screen.blit(success_txt, (20, 410))

                else:

                    # lewa reka do gory, prawa w dol
                    if (15501 <= time_elapsed < 16400 or 
                        17601 <= time_elapsed < 18600 or 
                        19501 <= time_elapsed < 20600 or 
                        21501 <= time_elapsed < 22400 or 
                        23301 <= time_elapsed < 24500 or
                        25501 <= time_elapsed < 26500 or 
                        27401 <= time_elapsed < 28400 or
                        29301 <= time_elapsed < 30300
                        ):
                        
                        # Rysowanie instrukcji
                        pygame.draw.rect(self.screen, (255, 255, 255), (15, 15, 310, 390), 3)
                        self.screen.blit(self.images[3], (20, 20))
                        
                        elbows_visible = l_elbow.visibility > 0.5 and r_elbow.visibility > 0.5
                        
                        samolot1 = l_wrist.y < l_elbow.y < l_shoulder.y < r_elbow.y < r_wrist.y

                        if samolot1 and elbows_visible:
                            self.score += 1
                            success_txt = self.big_font.render("DOBRZE!", True, (0, 255, 0))
                            self.screen.blit(success_txt, (20, 410))

                    # lewa reka w dol, prawa do gory
                    elif (16401 <= time_elapsed < 17600 or
                        18601 <= time_elapsed < 19500 or
                        20601 <= time_elapsed < 21500 or
                        22401 <= time_elapsed < 23300 or
                        24501 <= time_elapsed < 25500 or
                        26501 <= time_elapsed < 27400 or
                        28401 <= time_elapsed < 29300 or
                        30301 <= time_elapsed < 31300):
                    
                        # Rysowanie instrukcji
                        pygame.draw.rect(self.screen, (255, 255, 255), (15, 15, 310, 390), 3)
                        self.screen.blit(self.images[2], (20, 20))

                        elbows_visible = l_elbow.visibility > 0.5 and r_elbow.visibility > 0.5
                        samolot2 = r_wrist.y < r_elbow.y < r_shoulder.y < l_elbow.y < l_wrist.y



                        if elbows_visible and samolot2:
                            self.score += 1
                            success_txt = self.big_font.render("DOBRZE!", True, (0, 255, 0))
                            self.screen.blit(success_txt, (20, 410))









            # --- INTERFEJS UŻYTKOWNIKA (Zawsze widoczny) ---
            pygame.draw.rect(self.screen, (0, 0, 0), (340, 20, 400, 100))
            
            score_txt = self.font.render(f"PUNKTY: {self.score // 5}", True, (255, 255, 0))
            
            diff = now - game_absolute_start

            # 2. Pełne sekundy
            total_seconds = diff // 1000

            # 3. Części dziesiętne sekundy (0-9)
            # Bierzemy resztę z dzielenia przez 1000 i dzielimy przez 100
            deciseconds = (diff % 1000) // 100

            # 4. Renderowanie napisu (format: SEKUNDY.MILI)
            time_txt = self.font.render(f"CZAS GRY: {total_seconds}.{deciseconds}s", True, (0, 255, 255))
            
            self.screen.blit(score_txt, (350, 30))
            self.screen.blit(time_txt, (350, 75))

            # --- LOGIKA NAPISU PRZYGOTOWAWCZEGO ---
            # Sprawdzamy czy czas mieści się w przedziale 1 - 6000 ms
            if 0 < time_elapsed <= 6000 and (time_elapsed // 500) % 2 == 0:
                # Tworzymy napis (używamy big_font dla widoczności)
                prep_text = self.big_font.render("PRZYGOTUJ SIĘ!", True, (255, 255, 255)) # Biały kolor
                
                # Środkujemy napis na ekranie
                prep_rect = prep_text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 3.5))
                
                # Nakładamy napis na ekran
                self.screen.blit(prep_text, prep_rect)

                # --- INTERFEJS UŻYTKOWNIKA (Zawsze widoczny) ---
            pygame.draw.rect(self.screen, (0, 0, 0), (340, 20, 400, 100))
            
            score_txt = self.font.render(f"PUNKTY: {self.score // 5}", True, (255, 255, 0))
            diff = now - game_absolute_start
            total_seconds = diff // 1000
            deciseconds = (diff % 1000) // 100
            time_txt = self.font.render(f"CZAS GRY: {total_seconds}.{deciseconds}s", True, (0, 255, 255))
            
            self.screen.blit(score_txt, (350, 30))
            self.screen.blit(time_txt, (350, 75))

            # --- NAPIS RESETU W PRAWYM GÓRNYM ROGU ---
            reset_txt = self.font.render("RESET - KLIKNIJ R", True, (255, 255, 255))
            # Ustawiamy pozycję: 20 pikseli od prawej krawędzi, 20 pikseli od góry
            reset_rect = reset_txt.get_rect(topright=(self.screen.get_width() - 20, 20))
            self.screen.blit(reset_txt, reset_rect)
            
            

            pygame.display.flip()

        capture.release()