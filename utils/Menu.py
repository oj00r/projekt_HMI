import pygame
import sys
from utils.Button import Button

MENU_MAIN = "main"
MENU_GAME_SELECT = "game_select"
MENU_SETTINGS = "settings"

class Menu:
    def __init__(self, screen, finger_tracker):
        self.screen = screen
        self.finger_tracker = finger_tracker
        # Używamy domyślnej czcionki systemowej, ale pogrubionej, żeby była bardziej "puchata"
        try:
            self.font = pygame.font.SysFont("arial rounded mt bold", 48)
        except:
             self.font = pygame.font.SysFont(None, 48, bold=True)
             
        
        # Ładowanie tła - zmieniono kolory fallback (awaryjne) na pastelowe
        try:
            self.bg_main = pygame.transform.scale(
                pygame.image.load("./assets/bg_main.png").convert(), 
                (screen.get_width(), screen.get_height()))
            self.bg_game_select = self.bg_main
            self.bg_settings = self.bg_main
        except:
            # Fallback: Pastelowe kremowe tło
            self.bg_main = pygame.Surface((screen.get_width(), screen.get_height()))
            self.bg_main.fill((255, 253, 208)) # Cream color
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
            Button((center_x - 150, center_y - 100, 300, 60), "Wybór gry", self.font, self.select_game),
            Button((center_x - 150, center_y, 300, 60), "Ustawienia", self.font, self.settings),
            Button((center_x - 150, center_y + 100, 300, 60), "Wyjście", self.font, self.exit_game)
        ]

    def _create_game_select_buttons(self):
        center_x = self.screen.get_width() // 2
        center_y = self.screen.get_height() // 2

        self.buttons = [
            Button((center_x - 200, center_y - 60, 400, 60), "Papier Kamień Nożyce", self.font, self.game_rps),
            Button((center_x - 200, center_y + 40, 400, 60), "Kinect - sterowanie", self.font, self.game_kinect),
            Button((center_x - 150, center_y + 140, 300, 50), "Powrót", self.font, self.back_to_menu)
        ]

    def _create_settings_buttons(self):
        center_x = self.screen.get_width() // 2
        center_y = self.screen.get_height() // 2

        self.buttons = [
            Button((center_x - 200, center_y - 60, 400, 60), "Głośność +", self.font, self.volume_up),
            Button((center_x - 200, center_y + 10, 400, 60), "Głośność -", self.font, self.volume_down),
            Button((center_x - 150, center_y + 140, 300, 50), "Powrót", self.font, self.back_to_menu)
        ]

    def select_game(self):
        self.state = MENU_GAME_SELECT   
        self._create_game_select_buttons()

    def back_to_menu(self):
        self.state = MENU_MAIN
        self._create_main_buttons()

    def game_rps(self):
        print("Uruchamianie RPS...")
        
        # 1. ZWOLNIJ KAMERĘ w Pygame
        self.finger_tracker.release()
        
        # Minimalizuj okno Pygame (opcjonalne, czasem pomaga)
        pygame.display.iconify()
        
        # Import wewnątrz funkcji, żeby uniknąć cyklicznych zależności
        from utils.RPSGame import RPSGame
        
        # Przekazujemy indeks kamery, a nie obiekt capture
        try:
            game = RPSGame(cam_index=self.finger_tracker.cam_index)
            game.run()
        except Exception as e:
            print(f"Błąd gry RPS: {e}")
        
        # Po zamknięciu Ursina (jeśli w ogóle wróci - Ursina często zamyka cały proces)
        # Przywracamy okno Pygame
        pygame.display.set_mode((1280, 720))
        
        # 2. WŁĄCZ KAMERĘ PONOWNIE dla Menu
        self.finger_tracker.reinit()
            
    def game_kinect(self):
        print("Start gry: Kinect – sterowanie ciałem")

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

    # --- NOWA UROCZA METODA DRAW ---
    def draw(self, finger_pos, pinch):
        # 1. Rysowanie tła
        if self.state == MENU_MAIN:
            self.screen.blit(self.bg_main, (0, 0))
        elif self.state == MENU_GAME_SELECT:
            self.screen.blit(self.bg_game_select, (0, 0))
        elif self.state == MENU_SETTINGS:
            self.screen.blit(self.bg_settings, (0, 0))
            # Uroczy pasek głośności (zaokrąglony)
            vol_width = 200
            # Tło paska (jasnoszare)
            pygame.draw.rect(self.screen, (220, 220, 220), (50, 100, vol_width, 15), border_radius=8) 
            # Wypełnienie (różowe)
            if self.volume > 0:
                pygame.draw.rect(self.screen, (255, 105, 180), (50, 100, int(vol_width * self.volume), 15), border_radius=8)
    
        # 2. Rysowanie przycisków
        for button in self.buttons:
            button.draw(self.screen)
            
        # Tekst w ustawieniach (z obrysem, jak przyciski)
        if self.state == MENU_SETTINGS:
            # Używamy metody pomocniczej z pierwszego przycisku (trochę hack, ale działa)
            if self.buttons:
                 self.buttons[0].draw_text_with_outline(self.screen, f"Głośność: {int(self.volume*100)}%", self.font, (255,255,255), (255, 105, 180), pygame.Rect(50, 40, 200, 50))

        # 3. Rysowanie KURSORA (Urocza bąbelkowa kropka)
        cursor_pos = finger_pos
        is_snapped = False
        
        if finger_pos:
            for button in self.buttons:
                if button.original_rect.collidepoint(finger_pos):
                    is_snapped = True
                    break
        
        if cursor_pos:
            cx, cy = cursor_pos
            
            # Paleta kolorów kursora
            color_normal = (135, 206, 250)  # Pastelowy błękit (SkyBlue)
            color_snapped = (152, 251, 152) # Pastelowa mięta (PaleGreen)
            color_pinch = (255, 182, 193)   # Pastelowy róż (LightPink)
            
            # Wybór koloru i rozmiaru
            if pinch:
                color = color_pinch
                radius = 12 # Mniejszy przy kliku (efekt "ściśnięcia")
                border_width = 3
            elif is_snapped:
                color = color_snapped
                radius = 18 # Większy przy najechaniu
                border_width = 5
            else:
                color = color_normal
                radius = 15 # Normalny
                border_width = 4

            # Rysowanie:
            # 1. Zewnętrzna, półprzezroczysta otoczka (dla miękkości)
            s = pygame.Surface((radius*2+10, radius*2+10), pygame.SRCALPHA)
            pygame.draw.circle(s, (*color, 100), (radius+5, radius+5), radius+4)
            self.screen.blit(s, (cx - (radius+5), cy - (radius+5)))

            # 2. Gruby, biały obrys
            pygame.draw.circle(self.screen, (255, 255, 255), (cx, cy), radius, border_width)
            
            # 3. Kolorowy środek
            pygame.draw.circle(self.screen, color, (cx, cy), radius - border_width)