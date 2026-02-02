import pygame

class Button:
    def __init__(self, rect, text, font, action=None):
        self.original_rect = pygame.Rect(rect)
        self.rect = self.original_rect.copy()
        self.text = text
        self.font = font
        self.action = action
        
        # Stan
        self.hovered = False
        self.was_pressed = False
        
        # Styl 16-bitowy (Retro Kolory)
        self.color_face = (192, 192, 192)      # Szary (baza)
        self.color_highlight = (255, 255, 255) # Biały (światło)
        self.color_shadow = (128, 128, 128)    # Ciemnoszary (cień)
        self.color_black = (0, 0, 0)           # Czarny (obrys)
        
        self.color_face_hover = (220, 220, 255) # Lekki błękit po najechaniu
        self.text_color = (0, 0, 0)

    def update(self, finger_pos, pinch):
        if finger_pos and self.original_rect.collidepoint(finger_pos):
            self.hovered = True
            
            if pinch and not self.was_pressed:
                self.was_pressed = True
                if self.action:
                    self.action()
            elif not pinch:
                self.was_pressed = False
        else:
            self.hovered = False
            if not pinch:
                self.was_pressed = False

    def draw(self, screen):
        # Ustalanie pozycji (jeśli kliknięty, przesuń w dół-prawo)
        offset_x = 0
        offset_y = 0
        
        # Efekt wciśnięcia (gdy uszczypnięcie na przycisku)
        is_pressed = self.hovered and self.was_pressed
        if is_pressed:
            offset_x = 4
            offset_y = 4

        # Główny prostokąt (przesunięty)
        current_rect = self.original_rect.move(offset_x, offset_y)
        
        # 1. Cień "rzucany" na tło (czarny prostokąt pod spodem)
        # Rysujemy go tylko, jeśli przycisk NIE jest wciśnięty
        if not is_pressed:
            shadow_rect = self.original_rect.move(6, 6)
            pygame.draw.rect(screen, self.color_black, shadow_rect)

        # 2. Wypełnienie przycisku
        bg_color = self.color_face_hover if self.hovered else self.color_face
        pygame.draw.rect(screen, bg_color, current_rect)

        # 3. Obrys (Border) - 1px czarny
        pygame.draw.rect(screen, self.color_black, current_rect, 2)

        # 4. Efekt 3D (Bevel) - chyba że wciśnięty (wtedy płaski lub odwrócony)
        if not is_pressed:
            # Jasne krawędzie (Góra i Lewa)
            pygame.draw.line(screen, self.color_highlight, (current_rect.left + 2, current_rect.top + 2), (current_rect.right - 3, current_rect.top + 2), 3)
            pygame.draw.line(screen, self.color_highlight, (current_rect.left + 2, current_rect.top + 2), (current_rect.left + 2, current_rect.bottom - 3), 3)
            
            # Ciemne krawędzie (Dół i Prawa)
            pygame.draw.line(screen, self.color_shadow, (current_rect.left + 2, current_rect.bottom - 2), (current_rect.right - 2, current_rect.bottom - 2), 3)
            pygame.draw.line(screen, self.color_shadow, (current_rect.right - 2, current_rect.top + 2), (current_rect.right - 2, current_rect.bottom - 2), 3)

        # 5. Tekst (Bez antyaliasingu dla efektu pikseli)
        # Render(text, antialias, color) -> antialias=False
        text_surf = self.font.render(self.text, False, self.text_color)
        text_rect = text_surf.get_rect(center=current_rect.center)
        
        # Jeśli wciśnięty, tekst też się przesuwa
        screen.blit(text_surf, text_rect)