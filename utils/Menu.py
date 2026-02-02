import pygame
import sys
import subprocess
from utils.Button import Button

MENU_MAIN = "main"
MENU_GAME_SELECT = "game_select"
MENU_SETTINGS = "settings"

class Menu:
    def __init__(self, screen, finger_tracker):
        self.screen = screen
        self.finger_tracker = finger_tracker
        
        # Styl 16-bit: Używamy czcionki technicznej/monospace
        # "Courier New", "Consolas" lub domyślna systemowa
        try:
            self.font = pygame.font.SysFont("courier new", 40, bold=True)
            self.font_small = pygame.font.SysFont("courier new", 30, bold=True)
        except:
             self.font = pygame.font.SysFont(None, 48, bold=False)
             self.font_small = pygame.font.SysFont(None, 40, bold=False)
             
        # Ładowanie tła
        try:
            self.bg_main = pygame.transform.scale(
                pygame.image.load("./assets/menu.png").convert(), 
                (screen.get_width(), screen.get_height()))
            self.bg_game_select = self.bg_main
            self.bg_settings = self.bg_main
        except:
            # Fallback: Retro Grid (Fioletowe tło z siatką)
            self.bg_main = pygame.Surface((screen.get_width(), screen.get_height()))
            self.bg_main.fill((50, 20, 80)) # Ciemny fiolet
            # Rysowanie siatki
            for x in range(0, screen.get_width(), 40):
                pygame.draw.line(self.bg_main, (70, 40, 100), (x, 0), (x, screen.get_height()), 2)
            for y in range(0, screen.get_height(), 40):
                pygame.draw.line(self.bg_main, (70, 40, 100), (0, y), (screen.get_width(), y), 2)
                
            self.bg_game_select = self.bg_main
            self.bg_settings = self.bg_main

        self.state = MENU_MAIN
        self.lock_interaction = False
        self._create_main_buttons()

        self.volume = 0.5  
        pygame.mixer.music.set_volume(self.volume)

    def _create_main_buttons(self):
        center_x = self.screen.get_width() // 2
        center_y = self.screen.get_height() // 2

        self.buttons = [
            Button((center_x - 150, center_y - 100, 300, 60), "WYBÓR GRY", self.font, self.select_game),
            Button((center_x - 150, center_y, 300, 60), "USTAWIENIA", self.font, self.settings),
            Button((center_x - 150, center_y + 100, 300, 60), "WYJŚCIE", self.font, self.exit_game)
        ]

    def _create_game_select_buttons(self):
        center_x = self.screen.get_width() // 2
        center_y = self.screen.get_height() // 2

        self.buttons = [
            Button((center_x - 200, center_y - 140, 400, 60), "PAPIER KAMIEŃ", self.font_small, self.game_rps),
            Button((center_x - 200, center_y - 60, 400, 60), "FLAPPY FIST", self.font_small, self.game_bird),
            Button((center_x - 200, center_y + 20, 400, 60), "KINECT DANCE", self.font_small, self.game_kinect),
            Button((center_x - 150, center_y + 120, 300, 50), "<< POWRÓT", self.font, self.back_to_menu)
        ]

    def _create_settings_buttons(self):
        center_x = self.screen.get_width() // 2
        center_y = self.screen.get_height() // 2

        self.buttons = [
            Button((center_x - 200, center_y - 60, 400, 60), "GŁOŚNOŚĆ +", self.font, self.volume_up),
            Button((center_x - 200, center_y + 10, 400, 60), "GŁOŚNOŚĆ -", self.font, self.volume_down),
            Button((center_x - 150, center_y + 140, 300, 50), "<< POWRÓT", self.font, self.back_to_menu)
        ]

    def select_game(self):
        self.state = MENU_GAME_SELECT   
        self._create_game_select_buttons()

    def back_to_menu(self):
        self.state = MENU_MAIN
        self._create_main_buttons()

    # --- OBSŁUGA GIER ---
    def game_rps(self):
        print("Uruchamianie RPS...")
        self.finger_tracker.release()
        try:
            subprocess.run([sys.executable, "utils/RPSGame.py", str(self.finger_tracker.cam_index)])
        except Exception as e:
            print(f"Błąd: {e}")
        self.screen = pygame.display.set_mode((1280, 720))
        self.finger_tracker.reinit()
        self.state = MENU_GAME_SELECT
        self._create_game_select_buttons()

    def game_bird(self):
        print("Uruchamianie Flappy Fist...")
        self.finger_tracker.release()
        try:
            subprocess.run([sys.executable, "utils/BirdGame.py", str(self.finger_tracker.cam_index)])
        except Exception as e:
            print(f"Błąd: {e}")
        self.screen = pygame.display.set_mode((1280, 720))
        self.finger_tracker.reinit()
        self.finger_tracker.pinch = False
        self.state = MENU_GAME_SELECT
        self._create_game_select_buttons()

    def game_kinect(self):
        print("Uruchamianie Kinect...")
        self.finger_tracker.release()
        try:
            from utils.KinectGame import KinectGame
        except ImportError:
            print("Brak pliku KinectGame.py")
            self.finger_tracker.reinit()
            return

        old_w, old_h = self.screen.get_width(), self.screen.get_height()
        try:
            pygame.mixer.music.fadeout(1000)
            pygame.mixer.music.load("./music/kinect_music.mp3")
            pygame.mixer.music.play(-1)
        except: pass

        try:
            game = KinectGame(self.screen, cam_index=self.finger_tracker.cam_index)
            game.run()
        except Exception as e:
            print(f"Błąd: {e}")
        
        try:
            pygame.mixer.music.load("./music/music.mp3")
            pygame.mixer.music.play(-1)
        except: pass

        self.screen = pygame.display.set_mode((old_w, old_h))
        self.finger_tracker.reinit()
        self.state = MENU_GAME_SELECT
        self._create_game_select_buttons()

    def settings(self):
        self.state = MENU_SETTINGS
        self._create_settings_buttons()

    def volume_up(self):
        self.volume = min(1.0, self.volume + 0.1)
        pygame.mixer.music.set_volume(self.volume)

    def volume_down(self):
        self.volume = max(0.0, self.volume - 0.1)
        pygame.mixer.music.set_volume(self.volume)

    def exit_game(self):
        self.finger_tracker.release()
        pygame.quit()
        sys.exit()

    def update(self, finger_pos, pinch):
            if not pinch:
                self.lock_interaction = False
            if not self.lock_interaction:
                for button in self.buttons[:]:
                    old_state = self.state 
                    button.update(finger_pos, pinch)
                    if self.state != old_state:
                        self.lock_interaction = True
                        break

    def draw(self, finger_pos, pinch):
        # 1. Rysowanie tła
        if self.state == MENU_MAIN:
            self.screen.blit(self.bg_main, (0, 0))
        elif self.state == MENU_GAME_SELECT:
            self.screen.blit(self.bg_game_select, (0, 0))
        elif self.state == MENU_SETTINGS:
            self.screen.blit(self.bg_settings, (0, 0))
            
            # Pasek głośności w stylu retro (blokowy)
            vol_width = 300
            pygame.draw.rect(self.screen, (50, 50, 50), (50, 100, vol_width, 30)) # Tło
            
            # Wypełnienie blokowe (zielone segmenty)
            blocks = int(self.volume * 10)
            for i in range(blocks):
                pygame.draw.rect(self.screen, (0, 255, 0), (50 + i*30 + 2, 102, 26, 26))

    
        # 2. Rysowanie przycisków
        for button in self.buttons:
            button.draw(self.screen)
            
        # 3. Tekst w ustawieniach (NAPRAWIONE)
        if self.state == MENU_SETTINGS:
             # Rysujemy tekst bezpośrednio, bez użycia metody Button
             label_text = f"GŁOŚNOŚĆ: {int(self.volume*100)}%"
             
             # Cień tekstu (czarny)
             txt_shadow = self.font.render(label_text, False, (0, 0, 0))
             self.screen.blit(txt_shadow, (52, 52))
             
             # Właściwy tekst (biały)
             txt_main = self.font.render(label_text, False, (255, 255, 255))
             self.screen.blit(txt_main, (50, 50))

        # 4. Rysowanie KURSORA - PIKSELOWA STRZAŁKA
        if finger_pos:
            x, y = finger_pos
            
            # Kolory kursora
            c_fill = (255, 255, 255) # Biały
            c_outline = (0, 0, 0)    # Czarny
            
            if pinch:
                c_fill = (255, 50, 50) # Czerwony jak kliknie
            
            # Definicja kształtu strzałki
            cursor_points = [
                (x, y),          # Czubek
                (x, y + 30),     # Lewy dół
                (x + 10, y + 22),# Wcięcie
                (x + 22, y + 34),# Ogon dół
                (x + 28, y + 28),# Ogon góra
                (x + 16, y + 16),# Wcięcie góra
                (x + 30, y + 10) # Prawy bok
            ]
            
            # Obrys
            pygame.draw.polygon(self.screen, c_outline, [(p[0]+2, p[1]+2) for p in cursor_points], 0) # Cień rzucany
            pygame.draw.polygon(self.screen, c_outline, [(p[0]-2, p[1]) for p in cursor_points], 6) # Obrys gruby
            
            # Wypełnienie
            pygame.draw.polygon(self.screen, c_fill, cursor_points, 0)