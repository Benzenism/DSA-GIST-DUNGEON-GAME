import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, C_BG, C_WHITE, C_MUTED, C_YELLOW, C_UI_BORDER

class StartScreen:
    def __init__(self, screen: pygame.Surface):
        self.screen      = screen
        self.font_title  = pygame.font.SysFont("consolas", 48, bold=True)
        self.font_sub    = pygame.font.SysFont("consolas", 20)
        self.font_input  = pygame.font.SysFont("consolas", 26)
        self.font_hint   = pygame.font.SysFont("consolas", 15)
        self.name_buffer = ""
        self.max_len     = 14
        self.error_msg   = ""
        self.cursor_tick = 0

    def run(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    name = self.name_buffer.strip()
                    if name:
                        return name
                    self.error_msg = "Please enter your name."
                elif event.key == pygame.K_BACKSPACE:
                    self.name_buffer = self.name_buffer[:-1]
                    self.error_msg   = ""
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit(); raise SystemExit
                elif len(self.name_buffer) < self.max_len and event.unicode.isprintable():
                    if event.unicode.isascii():
                        self.name_buffer += event.unicode
                        self.error_msg   = ""
                    else:
                        self.error_msg = "English/Numbers only."
                        
        self._draw()
        return None

    def _draw(self):
        self.cursor_tick += 1
        self.screen.fill(C_BG)
        W, H = SCREEN_WIDTH, SCREEN_HEIGHT

        t = self.font_title.render("DUNGEON MASTER", True, C_YELLOW)
        self.screen.blit(t, t.get_rect(center=(W//2, H//3 - 20)))

        s = self.font_sub.render("GIST 26-1 DSA FINAL PROJECT", True, C_MUTED)
        self.screen.blit(s, s.get_rect(center=(W//2, H//3 + 40)))

        bw, bh = 360, 48
        bx, by = W//2 - bw//2, H//2 + 10
        pygame.draw.rect(self.screen, C_UI_BORDER, (bx-2, by-2, bw+4, bh+4), border_radius=8)
        pygame.draw.rect(self.screen, (28, 24, 40),  (bx, by, bw, bh), border_radius=8)

        cursor = "|" if (self.cursor_tick // 28) % 2 == 0 else ""
        ns = self.font_input.render(self.name_buffer + cursor, True, C_WHITE)
        self.screen.blit(ns, (bx + 12, by + 8))

        lbl = self.font_sub.render("Enter your name:", True, C_MUTED)
        self.screen.blit(lbl, lbl.get_rect(center=(W//2, by - 28)))

        if self.error_msg:
            es = self.font_hint.render(self.error_msg, True, (220, 70, 70))
            self.screen.blit(es, es.get_rect(center=(W//2, by + bh + 18)))

        hint = self.font_hint.render("ENTER to start  |  ESC to quit", True, C_MUTED)
        self.screen.blit(hint, hint.get_rect(center=(W//2, H*3//4)))

        controls = [
            "[ WASD / Arrow Keys ] — Move                 ",
            "[       SPACE       ] — Attack adjacent enemy",
            "[     1 / 2 / 3     ] — Use inventory item   ",
            "[         Z         ] — Undo last action     ",
        ]
        y = H*3//4 + 36
        for line in controls:
            cs = self.font_hint.render(line, True, C_MUTED)
            self.screen.blit(cs, cs.get_rect(center=(W//2, y)))
            y += 22