import pygame
from config import (SCREEN_WIDTH, SCREEN_HEIGHT,
                    C_BG, C_WHITE, C_MUTED, C_YELLOW, C_GREEN,
                    C_RED, C_ACCENT, C_UI_BORDER, C_UI_BG)
from leaderboard import save_entry, compute_final_score

class ResultScreen:
    def __init__(self, screen: pygame.Surface, result: dict):
        self.screen = screen
        self.result = result
        self.font_lg  = pygame.font.SysFont("consolas", 28, bold=True)
        self.font_md  = pygame.font.SysFont("consolas", 18)
        self.font_sm  = pygame.font.SysFont("consolas", 14)
        self.font_hd  = pygame.font.SysFont("consolas", 16, bold=True)

        self.board = save_entry(
            result["name"],
            result["score"],
            result["undo_count"],
            result["elapsed"],
            result["cleared"],
            result.get("turns", 0)
        )
        self.final_score = compute_final_score(
            result["score"], result["undo_count"],
            result["elapsed"], result["cleared"], result.get("turns", 0)
        )
        
        my_name = result["name"]
        self.my_rank = 1
        for i, e in enumerate(self.board):
            if (e["name"] == my_name and
                e.get("final_score") == self.final_score and
                e.get("turns") == result.get("turns", 0)):
                self.my_rank = i + 1
                break

    def run(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return "restart"
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); raise SystemExit
        self._draw()
        return None

    def _draw(self):
        self.screen.fill(C_BG)
        W, H = SCREEN_WIDTH, SCREEN_HEIGHT
        r    = self.result

        title_txt = "CLEAR!" if r["cleared"] else "GAME OVER"
        title_col = C_YELLOW       if r["cleared"] else C_RED
        ts = self.font_lg.render(title_txt, True, title_col)
        self.screen.blit(ts, ts.get_rect(center=(W//2, 40)))

        panel_w, panel_h = W - 60, 140
        px, py = 30, 80
        pygame.draw.rect(self.screen, C_UI_BG, (px, py, panel_w, panel_h), border_radius=8)
        pygame.draw.rect(self.screen, C_UI_BORDER, (px, py, panel_w, panel_h), 2, border_radius=8)

        col1 = px + 20
        col2 = px + panel_w // 2
        y    = py + 14

        def row(label, val="", color=C_WHITE, x=col1):
            s = self.font_md.render(f"{label}  {val}", True, color)
            self.screen.blit(s, (x, y))

        cleared_str = "YES" if r["cleared"] else "NO"
        cleared_col = C_GREEN if r["cleared"] else C_RED
        t = int(r["elapsed"])

        row(f"Rank:  #{self.my_rank}", "", C_YELLOW)
        row(f"Name:  {r['name']}", "", C_WHITE, col2)
        y += 24
        row(f"Cleared: {cleared_str}", "", cleared_col)
        row(f"Turns: {r.get('turns', 0)}", "", C_WHITE, col2)
        y += 24
        row(f"Time:  {t//60:02d}:{t%60:02d}", "", C_MUTED)
        row(f"Undo Used: {r['undo_count']}", "", C_MUTED, col2)
        y += 24
        
        base = r['score']
        undo_val = r['undo_count']
        time_val = int(r['elapsed'])
        turn_val = r.get('turns', 0)
        cbon = 500 if r['cleared'] else 0
        
        calc_str = f"{base}(Base) - {undo_val}*50(Undo) - {time_val}*0.5(Time) - {turn_val}*2(Turn) + {cbon}(Clear)"
        row(f"Calc:  {calc_str}", "", C_MUTED)
        y += 24
        row(f"Final Score: {self.final_score}", "", C_GREEN)

        lb_y = py + panel_h + 20
        lb_y += 8
        hd = self.font_hd.render("─── LEADERBOARD ───", True, C_ACCENT)
        self.screen.blit(hd, hd.get_rect(center=(W//2, lb_y)))
        lb_y += 26

        header_cols = [
            (40,   "Rank"),
            (100,  "Name"),
            (340,  "Final Score"),
            (530,  "Turns"),
            (700,  "Undo"),
            (800,  "Time"),
            (900,  "Cleared"),
        ]
        for hx, ht in header_cols:
            hs = self.font_sm.render(ht, True, C_MUTED)
            self.screen.blit(hs, (hx, lb_y))
        lb_y += 20
        pygame.draw.line(self.screen, C_UI_BORDER, (30, lb_y), (W-30, lb_y), 1)
        lb_y += 6

        for i, entry in enumerate(self.board[:12]):
            rank  = i + 1
            is_me = (entry["name"] == r["name"] and
                     entry.get("final_score") == self.final_score and
                     rank == self.my_rank)
            row_col = C_YELLOW if is_me else C_WHITE
            bg_col  = (40, 36, 60) if is_me else (25, 22, 35)

            pygame.draw.rect(self.screen, bg_col,
                             (32, lb_y - 2, W - 64, 22), border_radius=3)

            t_sec = int(entry.get("elapsed", 0))
            
            vals  = [
                (40,  f"#{rank}"),
                (100, entry["name"][:14]),
                (340, str(entry.get("final_score", 0))),
                (530, str(entry.get("turns", "-"))),
                (700, str(entry.get("undo_count", 0))),
                (800, f"{t_sec//60:02d}:{t_sec%60:02d}"),
                (900, "YES" if entry.get("cleared") else "NO"),
            ]
            for vx, vt in vals:
                vc = (C_GREEN if vt == "YES" else
                      C_RED   if vt == "NO"  else row_col)
                vs = self.font_sm.render(vt, True, vc)
                self.screen.blit(vs, (vx, lb_y))
            lb_y += 24
            if lb_y > H - 50:
                break

        guide = self.font_sm.render("R — Play Again   |   ESC — Quit", True, C_MUTED)
        self.screen.blit(guide, guide.get_rect(center=(W//2, H - 22)))