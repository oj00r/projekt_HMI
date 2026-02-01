import pygame
import sys
from utils.Button import Button

MENU_MAIN = "main"
MENU_GAME_SELECT = "game_select"
MENU_SETTINGS = "settings"

class Menu:
    def __init__(self, screen, finger_tracker):
        self.screen = screen
        self.finger_tracker = finger_tracker # Przechowujemy referencję do trackera
        self.font = pygame.font.SysFont(None, 48)
        
        # Ładowanie tła (uproszczone dla bezpieczeństwa, upewnij się że pliki istnieją)
        try:
            self.bg_main = pygame.transform.scale(
                pygame.image.load("./assets/bg_main.png").convert(), 
                (screen.get_width(), screen.get_height()))
            self.bg_game_select = self.bg_main
            self.bg_settings = self.bg_main
        except:
            # Fallback jeśli brak grafiki
            self.bg_main = pygame.Surface((screen.get_width(), screen.get_height()))
            self.bg_main.fill((50, 50, 50))
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
            Button((center_x - 500, center_y - 60, 400, 60), "Papier Kamień Nożyce", self.font, self.game_rps),
            Button((center_x - 500, center_y + 40, 400, 60), "Po prostu tańcz®", self.font, self.game_kinect),
            Button((center_x - 450, center_y + 140, 300, 50), "Powrót", self.font, self.back_to_menu)
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
        print("Uruchamianie Kinect Game w oknie głównym...")
        
        # 1. Zwalniamy tracker menu (bo KinectGame otworzy kamerę sam)
        self.finger_tracker.release()
        
        # Importujemy nową klasę
        from utils.KinectGame import KinectGame
        
        # Zapisujemy obecną rozdzielczość, żeby wiedzieć do czego wrócić
        old_w, old_h = self.screen.get_width(), self.screen.get_height()
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)


        try:
            pygame.mixer.music.fadeout(1000) # Płynne wyciszenie muzyki z menu (1 sekunda)
            pygame.mixer.music.load("./music/kinect_music.mp3")
            pygame.mixer.music.play(-1) # Odtwarzanie w pętli
        except Exception as e:
            print(f"Nie udało się załadować muzyki gry: {e}")

        try:
            # Przekazujemy 'self.screen', aby gra rysowała w tym samym oknie
            game = KinectGame(self.screen, cam_index=self.finger_tracker.cam_index)
            game.run()
        except Exception as e:
            print(f"Błąd uruchamiania gry Kinect: {e}")
        

        try:
            pygame.mixer.music.fadeout(1000) # Wyciszamy muzykę z gry Kinect
            pygame.mixer.music.load("./music/music.mp3") # Ładujemy standardową muzykę menu
            pygame.mixer.music.play(-1)
        except Exception as e:
             print(f"Błąd przy przywracaniu muzyki menu: {e}")

        # Po wyjściu z pętli gry przywracamy stare wymiary (1280x720)
        self.screen = pygame.display.set_mode((old_w, old_h))

        # 2. Po zakończeniu gry, przywracamy kamerę dla menu
        self.finger_tracker.reinit()


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
            # Kopia listy, aby uniknąć błędów przy zmianie stanu
            for button in self.buttons[:]:
                old_state = self.state 
                button.update(finger_pos, pinch)
                if self.state != old_state:
                    self.lock_interaction = True
                    break
    
    def draw(self, finger_pos, pinch):
        if self.state == MENU_MAIN:
            self.screen.blit(self.bg_main, (0, 0))
        elif self.state == MENU_GAME_SELECT:
            self.screen.blit(self.bg_game_select, (0, 0))
        elif self.state == MENU_SETTINGS:
            self.screen.blit(self.bg_settings, (0, 0))
    
        for button in self.buttons:
            button.draw(self.screen)
        
        # Wyświetlanie głośności w ustawieniach
        if self.state == MENU_SETTINGS:
            volume_text = self.font.render(f"Głośność: {int(self.volume*100)}%", True, (255, 255, 255))
            self.screen.blit(volume_text, (50, 50))

        cursor_pos = None
        if finger_pos:
            # Prosta logika przyciągania kursora do przycisku (opcjonalne)
            for button in self.buttons:
                if button.rect.collidepoint(finger_pos):
                    break
            cursor_pos = finger_pos

        if cursor_pos:
            pygame.draw.circle(self.screen, (0, 255, 0), cursor_pos, 10)
            if pinch:
                pygame.draw.circle(self.screen, (255, 0, 0), cursor_pos, 14, 3)