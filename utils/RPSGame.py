import pygame
import pickle
import numpy as np
import random
from utils.Button import Button

class RPSGame:
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.state = "START"  # START, PLAYING, RESULT
        
        # Ładowanie modelu
        try:
            model_dict = pickle.load(open('./model.p', 'rb'))
            self.model = model_dict['model']
        except FileNotFoundError:
            print("Błąd: Nie znaleziono pliku model.p")
            self.model = None

        self.labels_dict = {0: 'Kamien', 1: 'Papier', 2: 'Nozyce'}
        
        self.user_move = None
        self.computer_move = None
        self.result_text = ""
        self.timer = 0
        
        center_x = screen.get_width() // 2
        self.back_button = Button(
            rect=(center_x - 150, screen.get_height() - 100, 300, 60),
            text="Powrót do menu",
            font=self.font,
            action=self.reset_to_menu
        )

    def reset_to_menu(self):
        # Ta metoda zostanie nadpisana w Menu.py, aby zmienić self.state
        pass

    def get_prediction(self, hand_landmarks):
        """Przetwarza landmarki na format akceptowany przez model."""
        if not self.model or not hand_landmarks:
            return None
        
        data_aux = []
        x_ = []
        y_ = []

        # Pobieranie współrzędnych
        for i in range(len(hand_landmarks.landmark)):
            x = hand_landmarks.landmark[i].x
            y = hand_landmarks.landmark[i].y
            x_.append(x)
            y_.append(y)

        # Normalizacja danych (tak jak podczas treningu)
        for i in range(len(hand_landmarks.landmark)):
            data_aux.append(hand_landmarks.landmark[i].x - min(x_))
            data_aux.append(hand_landmarks.landmark[i].y - min(y_))

        prediction = self.model.predict([np.asarray(data_aux)])
        return self.labels_dict[int(prediction[0])]

    def update(self, finger_tracker, pinch):
        pos = finger_tracker.get_pos()
        self.back_button.update(pos, pinch)

        if self.state == "START":
            if pinch and not self.back_button.rect.collidepoint(pos if pos else (0,0)):
                self.state = "PLAYING"
                self.timer = pygame.time.get_ticks()

        elif self.state == "PLAYING":
            elapsed = (pygame.time.get_ticks() - self.timer) // 1000
            if elapsed >= 3:  # 3 sekundy na pokazanie gestu
                # Pobierz surowe dane z mediapipe (musisz zmodyfikować FingerTracker)
                raw_hand = finger_tracker.get_raw_landmarks() 
                if raw_hand:
                    self.user_move = self.get_prediction(raw_hand)
                    self.computer_move = random.choice(['Kamien', 'Papier', 'Nozyce'])
                    self.resolve_winner()
                    self.state = "RESULT"
                else:
                    self.result_text = "Nie wykryto dłoni!"
                    self.state = "RESULT"

        elif self.state == "RESULT":
            if pinch and (pygame.time.get_ticks() - self.timer > 5000): # reset po 2 sek od wyniku
                self.state = "START"

    def resolve_winner(self):
        if self.user_move == self.computer_move:
            self.result_text = "Remis!"
        elif (self.user_move == 'Papier' and self.computer_move == 'Kamien') or \
             (self.user_move == 'Kamien' and self.computer_move == 'Nozyce') or \
             (self.user_move == 'Nozyce' and self.computer_move == 'Papier'):
            self.result_text = "Wygrałeś!"
        else:
            self.result_text = "Przegrałeś!"

    def draw(self, finger_pos, pinch):
        self.screen.fill((30, 30, 50)) # Tło gry
        
        self.back_button.draw(self.screen)

        if self.state == "START":
            txt = self.font.render("Zrób gest PINCH, aby zacząć!", True, (255, 255, 255))
            self.screen.blit(txt, (self.screen.get_width()//2 - 200, 200))

        elif self.state == "PLAYING":
            count = 3 - (pygame.time.get_ticks() - self.timer) // 1000
            txt = self.font.render(f"Pokaż gest za: {count}", True, (255, 255, 0))
            self.screen.blit(txt, (self.screen.get_width()//2 - 100, 200))

        elif self.state == "RESULT":
            u_txt = self.font.render(f"Ty: {self.user_move}", True, (255, 255, 255))
            c_txt = self.font.render(f"PC: {self.computer_move}", True, (255, 255, 255))
            r_txt = self.font.render(self.result_text, True, (0, 255, 0))
            
            self.screen.blit(u_txt, (200, 200))
            self.screen.blit(c_txt, (800, 200))
            self.screen.blit(r_txt, (self.screen.get_width()//2 - 100, 400))