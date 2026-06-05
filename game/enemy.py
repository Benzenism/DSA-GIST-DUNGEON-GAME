import heapq
import math
from typing import Optional, Tuple, List
from config import ENEMY_HP, ENEMY_ATK, ENEMY_SIGHT

class Enemy:
    def __init__(self, x: int, y: int, enemy_type: str = "normal"):
        self.x = x
        self.y = y
        self.enemy_type = enemy_type
        
        # normal 적(빨간색): HP 40, ATK 10, 시야 8
        #  heavy 적(보라색): HP 1.5배, ATK 2배, 시야 0.5배
        if enemy_type == "heavy":
            self.max_hp = int(ENEMY_HP * 1.5)
            self.hp = self.max_hp
            self.atk = int(ENEMY_ATK * 2.0)
            self.sight = int(ENEMY_SIGHT * 0.5)
        else:
            self.max_hp = ENEMY_HP
            self.hp = ENEMY_HP
            self.atk = ENEMY_ATK
            self.sight = ENEMY_SIGHT
            
        self.active = False

    def is_alive(self) -> bool:
        return self.hp > 0

    def distance_to(self, px: int, py: int) -> float:
        return math.hypot(self.x - px, self.y - py)

    def take_damage(self, dmg: int):
        self.hp = max(0, self.hp - dmg)

    def attack_player(self, player) -> int:
        player.take_damage(self.atk)
        return self.atk

    def astar_step(self, dungeon_map, px: int, py: int) -> Optional[Tuple[int, int]]:
        dist = self.distance_to(px, py)
        if dist > self.sight:
            self.active = False
            return None
            
        self.active = True
        if dist <= 1.5:
            return None
            
        path = self._astar(dungeon_map, (self.x, self.y), (px, py))
        if path and len(path) > 1:
            return path[1]
        return None

    def _astar(self, dungeon_map,
               start: Tuple[int, int],
               goal:  Tuple[int, int]) -> List[Tuple[int, int]]:
        def h(pos):
            return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])

        open_set  = []
        heapq.heappush(open_set, (h(start), 0, start[0], start[1]))
        came_from: dict = {}
        g_score   = {start: 0}

        while open_set:
            f, g, cx, cy = heapq.heappop(open_set)
            current = (cx, cy)
            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                path.reverse()
                return path
            for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
                nx, ny    = cx + dx, cy + dy
                neighbor  = (nx, ny)
                if not dungeon_map.is_walkable(nx, ny):
                    continue
                tentative_g = g + 1
                if tentative_g < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor]   = tentative_g
                    heapq.heappush(open_set,
                        (tentative_g + h(neighbor), tentative_g, nx, ny))
        return []

    def move_toward(self, dungeon_map, px: int, py: int, occupied: set) -> bool:
        nxt = self.astar_step(dungeon_map, px, py)
        if nxt is None:
            return False
        nx, ny = nxt
        if (nx, ny) not in occupied:
            self.x, self.y = nx, ny
            return True
        return False