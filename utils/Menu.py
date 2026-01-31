import cv2
import mediapipe as mp
import pygame
import sys
import math
import random
import pickle
import numpy as np
from utils.Button import Button
from utils.RPSGame import RPSGame

MENU_MAIN = "main"
MENU_GAME_SELECT = "game_select"
MENU_SETTINGS = "settings"

class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 48)
        self.bg_main = pygame.transform.scale(
            pygame.image.load("./assets/bg_main.png").convert(), 
            (screen.get_width(), screen.get_height()))
        self.bg_game_select = pygame.transform.scale(
            pygame.image.load("./assets/bg_main.png").convert(), 
            (screen.get_width(), screen.get_height()))
        self.bg_settings = pygame.transform.scale(
            pygame.image.load("./assets/bg_main.png").convert(), 
            (screen.get_width(), screen.get_height()))

        self.state = MENU_MAIN
        self._create_main_buttons()

        self.volume = 0.5  
        pygame.mixer.music.set_volume(self.volume)

    # Przyciski dla odpowiednich stanów MENU
    def _create_main_buttons(self):
        center_x = self.screen.get_width() // 2
        center_y = self.screen.get_height() // 2

        self.buttons = [
            Button(
                rect=(center_x - 150, center_y - 100, 300, 60),
                text="Wybór gry",
                font=self.font,
                action=self.select_game
            ),
            Button(
                rect=(center_x - 150, center_y, 300, 60),
                text="Ustawienia",
                font=self.font,
                action=self.settings
            ),
            Button(
                rect=(center_x - 150, center_y + 100, 300, 60),
                text="Wyjście",
                font=self.font,
                action=self.exit_game
            )
        ]


    def _create_game_select_buttons(self):
        center_x = self.screen.get_width() // 2
        center_y = self.screen.get_height() // 2

        self.buttons = [
            Button(
                rect=(center_x - 200, center_y - 60, 400, 60),
                text="Papier Kamień Nożyce",
                font=self.font,
                action=self.game_rps
            ),
            Button(
                rect=(center_x - 200, center_y + 40, 400, 60),
                text="Kinect - sterowanie ciałem",
                font=self.font,
                action=self.game_kinect
            ),
            Button(
                rect=(center_x - 150, center_y + 140, 300, 50),
                text="Powrót",
                font=self.font,
                action=self.back_to_menu
            )
        ]

    def _create_settings_buttons(self):
        center_x = self.screen.get_width() // 2
        center_y = self.screen.get_height() // 2

        self.buttons = [
            Button(
                rect=(center_x - 200, center_y - 60, 400, 60),
                text="Głośność +",
                font=self.font,
                action=self.volume_up
            ),
            Button(
                rect=(center_x - 200, center_y + 10, 400, 60),
                text="Głośność -",
                font=self.font,
                action=self.volume_down
            ),
            Button(
                rect=(center_x - 150, center_y + 140, 300, 50),
                text="Powrót",
                font=self.font,
                action=self.back_to_menu
            )
        ]

    # Okno gier do wyboru
    def select_game(self):
        self.state = MENU_GAME_SELECT   
        self._create_game_select_buttons()

    def back_to_menu(self):
        self.state = MENU_MAIN
        self._create_main_buttons()


    def game_rps(self):
        print("Start gry: Kinect – sterowanie ciałem")


    def game_kinect(self):
        print("Start gry: Kinect – sterowanie ciałem")
        # tu później: zmiana sceny na grę

    # OKNO ustawień oraz podgłaśnianie i ściszanie
    def settings(self):
        self.state = MENU_SETTINGS
        self._create_settings_buttons()
        volume_text = self.font.render(f"Głośność: {int(self.volume*100)}%", True, (255, 255, 255))
        self.screen.blit(volume_text, (50, 50))

    def volume_up(self):
        self.volume = min(1.0, self.volume + 0.1)
        pygame.mixer.music.set_volume(self.volume)
        print(f"Głośność: {int(self.volume*100)}%")

    def volume_down(self):
        self.volume = max(0.0, self.volume - 0.1)
        pygame.mixer.music.set_volume(self.volume)
        print(f"Głośność: {int(self.volume*100)}%")


    # Wyjście
    def exit_game(self):
        pygame.quit()
        sys.exit()

    
    def handle_events(self, events):
        for event in events:
            for button in self.buttons:
                button.handle_event(event)
    
    # akutalizacja kursora
    def update(self, finger_pos, pinch):
        if not pinch:
            self.lock_interaction = False

        # Aktualizuj przyciski tylko, jeśli nie ma blokady
        if not self.lock_interaction:
            for button in self.buttons:
                old_state = self.state 
                button.update(finger_pos, pinch)
                
                if self.state != old_state:
                    self.lock_interaction = True
                    break
    
    # Rysowanie kursora
    def draw(self, finger_pos, pinch):

        if self.state == MENU_MAIN:
            self.screen.blit(self.bg_main, (0, 0))
        elif self.state == MENU_GAME_SELECT:
            self.screen.blit(self.bg_game_select, (0, 0))
        elif self.state == MENU_SETTINGS:
            self.screen.blit(self.bg_settings, (0, 0))
    
        for button in self.buttons:
            button.draw(self.screen)

        cursor_pos = None
        if finger_pos:
            for button in self.buttons:
                if button.rect.collidepoint(finger_pos):
                    break
            if cursor_pos is None:
                cursor_pos = finger_pos

        if cursor_pos:
            pygame.draw.circle(self.screen, (0, 255, 0), cursor_pos, 10)
            if pinch:
                pygame.draw.circle(self.screen, (255, 0, 0), cursor_pos, 14, 3)    

