import pygame
import sys
import random
import cv2
import mediapipe as mp
# Importujemy tracker z sąsiedniego pliku w tym samym folderze
try:
    from utils.FingerTracker import FingerTracker
except:
    from FingerTracker import FingerTracker

# --- Stałe Konfiguracyjne ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Kolory (Urocza paleta)
COLOR_BG = (135, 206, 250)       # Niebo (SkyBlue)
COLOR_BIRD = (255, 215, 0)       # Złoty ptak
COLOR_PIPE = (152, 251, 152)     # Miętowe rury
COLOR_TEXT = (255, 255, 255)     # Biały tekst

# --- FIZYKA (ZMODYFIKOWANA DLA DYNAMIKI) ---
GRAVITY = 0.5          # Zwiększone z 0.5 (szybsze spadanie)
JUMP_STRENGTH = -5    # Zwiększone z -8  (mocniejszy skok w górę)
PIPE_SPEED = 8         # Zwiększone z 5   (szybszy przesuw ekranu)
PIPE_GAP = 240         # Odstęp góra-dół (nieco większy, bo gra jest szybsza)
PIPE_FREQUENCY = 2000  # Zmniejszone z 1500 (rury są bliżej siebie w poziomie)

class BirdGame:
    def __init__(self, cam_index=0):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Flappy Fist - Sterowanie Pięścią")
        self.clock = pygame.time.Clock()
        # Używamy czcionki systemowej, pogrubionej
        try:
            self.font = pygame.font.SysFont("arial rounded mt bold", 64)
            self.small_font = pygame.font.SysFont("arial rounded mt bold", 32)
        except:
            self.font = pygame.font.SysFont(None, 64, bold=True)
            self.small_font = pygame.font.SysFont(None, 32, bold=True)

        # --- Inicjalizacja Trackera ---
        self.tracker = FingerTracker(cam_index=cam_index)
        self.was_closed = False

        # --- Stan Gry ---
        self.reset_game()
        self.game_active = False 

    def reset_game(self):
        self.bird_rect = pygame.Rect(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2, 40, 40)
        self.bird_velocity = 0
        self.score = 0
        
        # Rury
        self.pipes = []
        self.last_pipe_time = pygame.time.get_ticks()
        
    def create_pipe(self):
        min_height = 100
        max_height = SCREEN_HEIGHT - 100 - PIPE_GAP
        
        random_pipe_pos = random.randint(min_height, max_height)
        
        bottom_pipe_top = random_pipe_pos + PIPE_GAP
        bottom_pipe = pygame.Rect(SCREEN_WIDTH, bottom_pipe_top, 80, SCREEN_HEIGHT - bottom_pipe_top)
        
        top_pipe = pygame.Rect(SCREEN_WIDTH, 0, 80, random_pipe_pos)
        
        return bottom_pipe, top_pipe

    def move_pipes(self, pipes):
        for pipe in pipes:
            pipe.centerx -= PIPE_SPEED
        # Usuwanie rur za ekranem
        return [pipe for pipe in pipes if pipe.right > 0]

    def draw_elements(self, pipes, bird_rect, score):
        # Tło
        self.screen.fill(COLOR_BG)
        
        for pipe in pipes:
            pygame.draw.rect(self.screen, COLOR_PIPE, pipe, border_radius=10)
            pygame.draw.rect(self.screen, (100, 200, 100), pipe, width=3, border_radius=10)

        # Ptak
        pygame.draw.rect(self.screen, COLOR_BIRD, bird_rect, border_radius=8)
        pygame.draw.circle(self.screen, (255,255,255), (bird_rect.right-10, bird_rect.top+10), 8)
        pygame.draw.circle(self.screen, (0,0,0), (bird_rect.right-8, bird_rect.top+10), 3)

        # Wynik
        score_surface = self.font.render(str(int(score)), True, COLOR_TEXT)
        score_shadow = self.font.render(str(int(score)), True, (0,0,0))
        score_rect = score_surface.get_rect(center=(SCREEN_WIDTH / 2, 100))
        self.screen.blit(score_shadow, (score_rect.x+3, score_rect.y+3))
        self.screen.blit(score_surface, score_rect)

    def check_collision(self, pipes):
        for pipe in pipes:
            if self.bird_rect.colliderect(pipe):
                return True
        # Kolizja sufit lub podłoga
        if self.bird_rect.top <= 0 or self.bird_rect.bottom >= SCREEN_HEIGHT:
            return True
        return False

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False # Wyjście do menu
                    if event.key == pygame.K_SPACE and not self.game_active:
                        self.reset_game()
                        self.game_active = True

            #  Aktualizacja Trackera
            self.tracker.update(SCREEN_WIDTH, SCREEN_HEIGHT)
            is_closed = self.tracker.is_fist()
            
            # Detekcja SKOKU: Moment przejścia z otwartej dłoni w zamkniętą
            jump_triggered = False
            if is_closed and not self.was_closed:
                jump_triggered = True
        
            self.was_closed = is_closed

            if self.game_active:
                self.bird_velocity += GRAVITY
                
                keys = pygame.key.get_pressed()
                if (keys[pygame.K_SPACE] or jump_triggered):
                    self.bird_velocity = JUMP_STRENGTH
                
                self.bird_rect.centery += self.bird_velocity

                # Generowanie rur
                current_time = pygame.time.get_ticks()
                if current_time - self.last_pipe_time > PIPE_FREQUENCY:
                    self.pipes.extend(self.create_pipe())
                    self.last_pipe_time = current_time

                # Ruch rur
                self.pipes = self.move_pipes(self.pipes)
                self.score += 0.05 

                if self.check_collision(self.pipes):
                    self.game_active = False # Game Over

            self.draw_elements(self.pipes, self.bird_rect, self.score)
        
            if not self.game_active:
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 120)) # tło
                self.screen.blit(overlay, (0,0))
                
                msg1 = self.font.render("Zaciśnij pięść, aby skoczyć!", True, COLOR_TEXT)
                msg2 = self.small_font.render("Naciśnij SPACJĘ lub zaciśnij pięść, aby zacząć", True, COLOR_TEXT)
                msg3 = self.small_font.render("ESC - Powrót do Menu", True, COLOR_TEXT)
                
                msg1_rect = msg1.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 50))
                msg2_rect = msg2.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 20))
                msg3_rect = msg3.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 80))
                
                self.screen.blit(msg1, msg1_rect)
                self.screen.blit(msg2, msg2_rect)
                self.screen.blit(msg3, msg3_rect)
                
                if jump_triggered:
                     self.reset_game()
                     self.game_active = True

            if is_closed:
                pygame.draw.circle(self.screen, (255, 50, 50), (50, 50), 20) # Czerwona kropka = pięść
            elif self.tracker.active:
                 pygame.draw.circle(self.screen, (50, 255, 50), (50, 50), 20) # Zielona kropka = widzi dłoń
            else:
                 pygame.draw.circle(self.screen, (100, 100, 100), (50, 50), 20) # Szara = brak dłoni

            pygame.display.flip()
            self.clock.tick(FPS)

        self.tracker.release()
        pygame.quit()

# Sekcja uruchomieniowa (dla subprocess)
if __name__ == "__main__":
    import sys
    camera_idx = 2
    if len(sys.argv) > 1:
        try:
            camera_idx = int(sys.argv[1])
        except ValueError:
            pass
            
    game = BirdGame(cam_index=camera_idx)
    game.run()