import cv2
import mediapipe as mp
import pygame
import sys
from utils.Menu import Menu
from utils.FingerTracker import FingerTracker

# Inicjalizacja Pygame
pygame.init()
pygame.mixer.init()

try:
    pygame.mixer.music.load("./music/music.mp3")
    pygame.mixer.music.play(-1)
except:
    print("Brak pliku muzyki")

screen = pygame.display.set_mode((1280, 720))
pygame.display.set_caption("Menu Sterowane Gestami")
clock = pygame.time.Clock()
running = True

# Inicjalizacja trackera (upewnij się co do indeksu kamery: 0, 1 lub 2)
finger = FingerTracker(cam_index=2) 

# PRZEKAZUJEMY finger DO MENU
menu = Menu(screen, finger)

while running:
    dt = clock.tick(60) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Aktualizacja trackera
    finger.update(screen.get_width(), screen.get_height())
    finger_pos = finger.get_pos()
    pinch = finger.is_pinch()

    # Aktualizacja menu
    menu.update(finger_pos, pinch)
    
    # Rysowanie 
    menu.draw(finger_pos, pinch) 

    pygame.display.flip()

finger.release()
pygame.quit()