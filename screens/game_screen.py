import pygame, time, copy, random
from config import *
from game.map_gen import DungeonMap, TILE_STAIR, TILE_WALL
from game.player import Player
from game.enemy import Enemy
from game.turn_manager import TurnManager


class GameScreen:
    def __init__(self, screen: pygame.Surface, player_name: str):
        self.screen      = screen
        self.player_name = player_name
        self.font        = pygame.font.SysFont("consolas", 14)
        self.font_sm     = pygame.font.SysFont("consolas", 12)
        self.font_lg     = pygame.font.SysFont("consolas", 22, bold=True)
        self.font_hd     = pygame.font.SysFont("consolas", 15, bold=True)
        self.score       = 0
        self.floor       = 1
        self.start_time  = time.time()
        self.game_over   = False
        self.cleared     = False
        self.result      = None
        self.camera_x    = 0
        self.camera_y    = 0
        self.action_log  = []
        self.undo_stack  = []
        self.undo_count  = 0
        self._floor_changed = False

        # 층별 시드 고정 (Undo 대비)
        self.floor_seeds = [random.randint(0, 999999) for _ in range(TOTAL_FLOORS + 2)]
        self._init_floor()

    def _init_floor(self, carry_player: Player = None, carry_turns: int = 0):
        seed = self.floor_seeds[self.floor]
        self.dungeon = DungeonMap()
        self.dungeon.generate(seed)
        sx, sy = self.dungeon.player_start()

        if carry_player is None:
            self.player = Player(sx, sy)
        else:
            self.player   = carry_player
            self.player.x = sx
            self.player.y = sy

        self.enemies     = [Enemy(ex, ey, etype) for ex, ey, etype in self.dungeon.enemy_spawns]
        self.floor_items = {(ix, iy): iname for ix, iy, iname in self.dungeon.item_positions}

        self.turn_mgr = TurnManager()
        self.turn_mgr.set_enemies(list(range(len(self.enemies))))
        self.turn_mgr.turn_number = carry_turns

        self._show_msg(f"Entered Floor {self.floor}!")

    def _push_undo(self):
        state = {
            "player":     copy.deepcopy(self.player),
            "enemies":    copy.deepcopy(self.enemies),
            "floor_items":copy.deepcopy(self.floor_items),
            "turn_mgr":   copy.deepcopy(self.turn_mgr),
            "score":      self.score,
            "floor":      self.floor,
            "dungeon":    copy.deepcopy(self.dungeon),
            "action_log": list(self.action_log),
        }
        self.undo_stack.append(state)

    def _pop_undo(self) -> bool:
        if not self.undo_stack:
            return False
        if self.undo_count >= MAX_UNDO:
            return False
        current_undo_count = self.undo_count + 1
        state = self.undo_stack.pop()
        self.player      = state["player"]
        self.enemies     = state["enemies"]
        self.floor_items = state["floor_items"]
        self.turn_mgr    = state["turn_mgr"]
        self.score       = state["score"]
        self.floor       = state["floor"]
        self.dungeon     = state["dungeon"]
        self.action_log  = state["action_log"]
        self.undo_count  = current_undo_count
        return True

    def run(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if not self.game_over and not self.cleared:
                self._handle_event(event)
            elif (event.type == pygame.KEYDOWN and
                  event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE)):
                return self._make_result()

        if not self.game_over and not self.cleared:
            self._process_enemy_turns()
            self._check_death()

        self._draw()
        return self.result

    def _handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if not self.turn_mgr.is_player_turn():
            return

        acted = False
        self._floor_changed = False
        key   = event.key

        move_map = {
            pygame.K_w: (0,-1), pygame.K_UP:    (0,-1),
            pygame.K_s: (0, 1), pygame.K_DOWN:  (0, 1),
            pygame.K_a: (-1,0), pygame.K_LEFT:  (-1,0),
            pygame.K_d: ( 1,0), pygame.K_RIGHT: ( 1,0),
        }

        if key in move_map:
            dx, dy = move_map[key]
            self._push_undo()
            occupied = {(en.x, en.y) for en in self.enemies}
            if self.player.move(dx, dy, self.dungeon, occupied):
                self._on_player_move()
                acted = True
            else:
                self.undo_stack.pop()

        elif key == pygame.K_SPACE:
            self._push_undo()
            hits = self.player.attack_adjacent(self.enemies)
            if hits:
                for h in hits:
                    e = h["enemy"]
                    if h["killed"]:
                        idx = self.enemies.index(e)
                        self.enemies.remove(e)
                        self.turn_mgr.remove_enemy(idx)
                        self.score += ENEMY_SCORE
                        self._show_msg(f"Enemy Killed! (+{ENEMY_SCORE}pt)")
                    else:
                        self._show_msg(f"Enemy Attacked! (HP: {e.hp}/{e.max_hp})")
                self.turn_mgr.set_enemies(list(range(len(self.enemies))))
                acted = True
            else:
                self.undo_stack.pop()
                self._show_msg("No adjacent enemy.")

        elif key in (pygame.K_1, pygame.K_2, pygame.K_3):
            slot = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2}[key]
            items_list = list(self.player.inventory.keys())
            if slot < len(items_list):
                self._push_undo()
                msg = self.player.use_item(items_list[slot])
                self._show_msg(msg)
                acted = True
            else:
                self._show_msg("No item in that slot.")

        elif key == pygame.K_z:
            if self.undo_count >= MAX_UNDO:
                self._show_msg(f"Undo limit reached! (Max {MAX_UNDO})")
            elif self._pop_undo():
                undo_remain = MAX_UNDO - self.undo_count
                self._show_msg(f"Undo! (Remaining: {undo_remain})")
                acted = False
            else:
                self._show_msg("Nothing to undo.")

        elif key == pygame.K_ESCAPE:
            self.game_over = True
            self.result    = self._make_result()

        # 층 이동 시 advance()를 막아 적의 선제 이동 방지
        if acted and not self._floor_changed:
            self.turn_mgr.advance()

    def _on_player_move(self):
        px, py = self.player.x, self.player.y

        # 아이템 획득
        if (px, py) in self.floor_items:
            iname = self.floor_items.pop((px, py))
            self.player.pick_up(iname)
            self._show_msg(f"Picked up: {iname}")

        if self.dungeon.get_tile(px, py) == TILE_STAIR:
            if self.floor < TOTAL_FLOORS:
                self.floor += 1
                current_turns = self.turn_mgr.turn_number + 1
                self._init_floor(carry_player=self.player, carry_turns=current_turns)
                self._floor_changed = True
            else:
                self.cleared = True
                self._show_msg("★ YOU WIN! ★ Press ENTER...")
                self.result  = self._make_result()

    def _process_enemy_turns(self):
        if self.turn_mgr.is_player_turn():
            return
        eid = self.turn_mgr.get_current_enemy_id()
        if 0 <= eid < len(self.enemies):
            e        = self.enemies[eid]
            occupied = {(en.x, en.y) for en in self.enemies if en is not e}
            occupied.add((self.player.x, self.player.y))
            if e.distance_to(self.player.x, self.player.y) <= 1.5:
                dmg = e.attack_player(self.player)
                self._show_msg(f"Enemy attacks! -{dmg} HP")
            else:
                e.move_toward(self.dungeon, self.player.x, self.player.y, occupied)
        self.turn_mgr.advance()

    def _check_death(self):
        if not self.player.is_alive():
            self.game_over = True
            self.result    = self._make_result()

    def _show_msg(self, txt: str):
        self.action_log.append(txt)
        if len(self.action_log) > 14:
            self.action_log.pop(0)

    def _make_result(self) -> dict:
        return {
            "score":      self.score,
            "undo_count": self.undo_count,
            "elapsed":    time.time() - self.start_time,
            "cleared":    self.cleared,
            "name":       self.player_name,
            "turns":      self.turn_mgr.turn_number,
        }

    def _update_camera(self):
        self.camera_x = max(0, min(self.player.x - VIEW_COLS // 2,
                                   self.dungeon.cols - VIEW_COLS))
        self.camera_y = max(0, min(self.player.y - VIEW_ROWS // 2,
                                   self.dungeon.rows - VIEW_ROWS))

    def _draw(self):
        self.screen.fill(C_BG)
        self._update_camera()
        self._draw_map()
        self._draw_entities()
        self._draw_ui()

    def _draw_map(self):
        tc = {0: C_WALL, 1: C_FLOOR, 2: C_STAIR}
        for ty in range(VIEW_ROWS):
            for tx in range(VIEW_COLS):
                mx, my = self.camera_x + tx, self.camera_y + ty
                tile   = self.dungeon.get_tile(mx, my)
                color  = tc.get(tile, C_WALL)
                r = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(self.screen, color, r)
                if tile != TILE_WALL:
                    pygame.draw.rect(self.screen, (22, 20, 32), r, 1)

        for (ix, iy), iname in self.floor_items.items():
            sx = ix - self.camera_x
            sy = iy - self.camera_y
            if 0 <= sx < VIEW_COLS and 0 <= sy < VIEW_ROWS:
                ic  = ITEMS[iname]["color"]
                sym = ITEMS[iname]["symbol"]
                cx  = sx * TILE_SIZE + TILE_SIZE // 2
                cy  = sy * TILE_SIZE + TILE_SIZE // 2
                pygame.draw.circle(self.screen, ic, (cx, cy), 8)
                ts  = self.font_sm.render(sym, True, (10, 10, 10))
                self.screen.blit(ts, ts.get_rect(center=(cx, cy)))

    def _draw_entities(self):
        for e in self.enemies:
            sx = e.x - self.camera_x
            sy = e.y - self.camera_y
            if not (0 <= sx < VIEW_COLS and 0 <= sy < VIEW_ROWS):
                continue
            ex, ey = sx * TILE_SIZE, sy * TILE_SIZE
            enemy_color = C_HEAVY_ENEMY if e.enemy_type == "heavy" else C_ENEMY
            pygame.draw.rect(self.screen, enemy_color,
                             (ex+4, ey+4, TILE_SIZE-8, TILE_SIZE-8), border_radius=4)
            hp_r = e.hp / e.max_hp
            bw   = TILE_SIZE - 8
            pygame.draw.rect(self.screen, (70, 20, 20), (ex+4, ey+1, bw, 3))
            pygame.draw.rect(self.screen, C_GREEN, (ex+4, ey+1, int(bw*hp_r), 3))
            if e.active:
                pygame.draw.rect(self.screen, C_YELLOW,
                                 (ex+4, ey+4, TILE_SIZE-8, TILE_SIZE-8), 1, border_radius=4)

        px_s = (self.player.x - self.camera_x) * TILE_SIZE
        py_s = (self.player.y - self.camera_y) * TILE_SIZE
        cx   = px_s + TILE_SIZE // 2
        cy   = py_s + TILE_SIZE // 2
        pygame.draw.circle(self.screen, C_PLAYER, (cx, cy), TILE_SIZE//2 - 3)
        pygame.draw.circle(self.screen, C_WHITE,  (cx, cy), TILE_SIZE//2 - 3, 2)

    def _draw_ui(self):
        ux = VIEW_COLS * TILE_SIZE + 4
        uw = SCREEN_WIDTH - ux
        pygame.draw.rect(self.screen, C_UI_BG,    (ux, 0, uw, SCREEN_HEIGHT))
        pygame.draw.line(self.screen, C_UI_BORDER, (ux, 0), (ux, SCREEN_HEIGHT), 2)

        x = ux + 10
        y = 10

        def txt(s, color=C_WHITE, dy=20):
            nonlocal y
            self.screen.blit(self.font.render(s, True, color), (x, y))
            y += dy

        def sep(label=""):
            nonlocal y
            pygame.draw.line(self.screen, C_UI_BORDER, (ux+4, y), (ux+uw-4, y), 1)
            y += 4
            if label:
                self.screen.blit(self.font_hd.render(label, True, C_ACCENT), (x, y))
                y += 20

        txt(f"Player : {self.player_name}", C_YELLOW, 22)
        txt(f"Floor  : {self.floor} / {TOTAL_FLOORS}")
        txt(f"Score  : {self.score}", C_GREEN)
        txt(f"Turn   : {self.turn_mgr.turn_number}", C_MUTED)
        t = int(time.time() - self.start_time)
        txt(f"Time   : {t//60:02d}:{t%60:02d}", C_MUTED)
        y += 4

        sep("── HP ──────────────")
        hp_r = self.player.hp / self.player.max_hp
        br   = pygame.Rect(x, y, uw-22, 14)
        pygame.draw.rect(self.screen, (60, 20, 20), br, border_radius=3)
        pygame.draw.rect(self.screen, C_GREEN,
                         (x, y, int((uw-22)*hp_r), 14), border_radius=3)
        hs = self.font_sm.render(f"{self.player.hp}/{self.player.max_hp}", True, C_WHITE)
        self.screen.blit(hs, hs.get_rect(center=br.center))
        y += 20
        txt(f"ATK    : {self.player.atk}", C_MUTED)
        y += 4

        sep("── UNDO ────────────")
        undo_remain = max(0, MAX_UNDO - self.undo_count)
        undo_r = undo_remain / MAX_UNDO
        ur = pygame.Rect(x, y, uw-22, 14)
        pygame.draw.rect(self.screen, (40, 30, 50), ur, border_radius=3)
        pygame.draw.rect(self.screen, C_ACCENT,
                         (x, y, int((uw-22)*undo_r), 14), border_radius=3)
        us = self.font_sm.render(f"{undo_remain} / {MAX_UNDO}", True, C_WHITE)
        self.screen.blit(us, us.get_rect(center=ur.center))
        y += 20
        y += 4

        sep("── Inventory ───────")
        items = list(self.player.inventory.items())
        if not items:
            txt("(empty)", C_MUTED, 18)
        else:
            for i, (iname, cnt) in enumerate(items[:6]):
                c = C_YELLOW if i < 3 else C_MUTED
                txt(f"[{i+1}] {iname} x{cnt}", c, 18)
        y += 4

        sep("── Controls ────────")
        for h in ["WASD/Arrow - Move",
                  "SPACE      - Attack",
                  "1/2/3      - Use Item",
                  "Z          - Undo",
                  "ESC        - Give Up"]:
            txt(h, C_MUTED, 17)
        y += 4

        sep("── Action Log ──────")
        for msg in self.action_log:
            txt(msg, C_YELLOW, 18)