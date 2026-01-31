import pygame

class Button:
    def __init__(self, rect, text, font, action=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.action = action
        self.hovered = False
        self.was_pressed = False  # blokada podwójnego kliknięcia

    def update(self, finger_pos, pinch):
        if finger_pos and self.rect.collidepoint(finger_pos):
            self.hovered = True

            # klik tylko przy zmianie stanu pinch
            if pinch and not self.was_pressed:
                self.was_pressed = True
                if self.action:
                    self.action()
            elif not pinch:
                # reset blokady, kiedy pinch puści
                self.was_pressed = False
        else:
            self.hovered = False
            # reset blokady, jeśli palec wyszedł poza przycisk
            if not pinch:
                self.was_pressed = False

    def draw(self, screen):
        color = (220, 220, 255) if self.hovered else (170, 170, 210)
        pygame.draw.rect(screen, color, self.rect, border_radius=12)
        pygame.draw.rect(screen, (40, 40, 80), self.rect, 3, border_radius=12)

        text_surf = self.font.render(self.text, True, (20, 20, 40))
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
