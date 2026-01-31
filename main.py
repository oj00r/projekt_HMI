import cv2
import mediapipe as mp
import pygame
import sys
import math
import random
import pickle
import numpy as np
from utils.Button import Button
from utils.Menu import Menu
from utils.FingerTracker import FingerTracker

pygame.init()
pygame.mixer.init()

try:
    pygame.mixer.music.load("./music/music.mp3")
    pygame.mixer.music.play(-1)
except:
    print("Brak pliku muzyki")

pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True

finger = FingerTracker(cam_index=2) # Wybor kamery
menu = Menu(screen)

while running:
    dt = clock.tick(60) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    finger.update(screen.get_width(), screen.get_height())
    finger_pos = finger.get_pos()
    pinch = finger.is_pinch()

    menu.update(finger_pos, pinch)
    menu.draw(finger_pos, pinch) 

    pygame.display.flip()

finger.release()
pygame.quit()
