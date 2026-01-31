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
        
        # Animacja (sprężyste powiększanie)
        self.current_scale = 1.0
        self.target_scale = 1.0
        
        # --- UROCZA PALETA BARW ---
        # Pastelowy róż jako baza
        self.color_normal = (255, 182, 193)   # LightPink
        # Pastelowy błękit po najechaniu
        self.color_hover = (173, 216, 230)    # LightBlue
        # Ciemniejszy róż na obrys
        self.border_color = (255, 105, 180)   # HotPink
        # Kolor tekstu (biały) i jego obrysu (ciemny róż)
        self.text_color = (255, 255, 255)
        self.text_outline_color = (255, 20, 147) # DeepPink

    def update(self, finger_pos, pinch):
        # Logika bez zmian - działa na oryginalnym prostokącie
        if finger_pos and self.original_rect.collidepoint(finger_pos):
            self.hovered = True
            self.target_scale = 1.1 # Lekkie powiększenie
            
            if pinch and not self.was_pressed:
                self.was_pressed = True
                if self.action:
                    self.action()
            elif not pinch:
                self.was_pressed = False
        else:
            self.hovered = False
            self.target_scale = 1.0
            if not pinch:
                self.was_pressed = False

        # Płynna animacja (Lerp)
        self.current_scale += (self.target_scale - self.current_scale) * 0.2

    # Funkcja pomocnicza do rysowania tekstu z obrysem (efekt naklejki)
    def draw_text_with_outline(self, surface, text, font, color, outline_color, pos_rect):
        bg_txt = font.render(text, True, outline_color)
        fg_txt = font.render(text, True, color)
        
        # Rysujemy obrys 4 razy przesunięty
        offsets = [(-2, -2), (2, -2), (-2, 2), (2, 2)]
        for dx, dy in offsets:
             outline_rect = bg_txt.get_rect(center=(pos_rect.centerx + dx, pos_rect.centery + dy))
             surface.blit(bg_txt, outline_rect)
             
        # Rysujemy główny tekst na wierzchu
        txt_rect = fg_txt.get_rect(center=pos_rect.center)
        surface.blit(fg_txt, txt_rect)

    def draw(self, screen):
        # Obliczamy wizualny rozmiar
        width = int(self.original_rect.width * self.current_scale)
        height = int(self.original_rect.height * self.current_scale)
        cx, cy = self.original_rect.center
        
        # Wirtualny prostokąt do rysowania
        draw_rect = pygame.Rect(0, 0, width, height)
        draw_rect.center = (cx, cy)

        # Zaokrąglenie (połowa wysokości daje kształt pastylki)
        radius = height // 2

        # --- Rysowanie Cienia (miękki, różowy cień pod spodem) ---
        shadow_rect = draw_rect.copy()
        shadow_rect.y += 6 # Przesunięcie w dół
        # Rysujemy cień (ciemniejszy róż, lekko przezroczysty)
        shadow_surf = pygame.Surface((width, height + 10), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (219, 112, 147, 100), (0,0,width,height), border_radius=radius)
        screen.blit(shadow_surf, (draw_rect.x, draw_rect.y + 5))

        # --- Rysowanie Przycisku ---
        bg_color = self.color_hover if self.hovered else self.color_normal
        
        # 1. Grubszy obrys (jako tło)
        pygame.draw.rect(screen, self.border_color, draw_rect, border_radius=radius)
        
        # 2. Wypełnienie środka (trochę mniejsze)
        inner_rect = draw_rect.inflate(-6, -6)
        pygame.draw.rect(screen, bg_color, inner_rect, border_radius=radius-3)

        # --- Rysowanie Tekstu (z obrysem) ---
        self.draw_text_with_outline(screen, self.text, self.font, self.text_color, self.text_outline_color, draw_rect)