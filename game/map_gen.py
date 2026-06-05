import random
import math
from collections import deque
from dataclasses import dataclass
from typing import List, Tuple
from config import (MAP_COLS, MAP_ROWS, MIN_ROOMS, MAX_ROOMS,
                    MIN_ROOM_SIZE, MAX_ROOM_SIZE, ITEMS, ITEMS_PER_FLOOR,
                    ENEMIES_PER_FLOOR)

TILE_WALL  = 0
TILE_FLOOR = 1
TILE_STAIR = 2

@dataclass
class Room:
    x: int
    y: int
    w: int
    h: int

    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.w // 2, self.y + self.h // 2)

    def intersects(self, other: "Room", margin: int = 1) -> bool:
        return (self.x - margin < other.x + other.w and
                self.x + self.w + margin > other.x and
                self.y - margin < other.y + other.h and
                self.y + self.h + margin > other.y)

class DungeonMap:
    def __init__(self, cols: int = MAP_COLS, rows: int = MAP_ROWS):
        self.cols = cols
        self.rows = rows
        self.tiles: List[List[int]] = [[TILE_WALL] * cols for _ in range(rows)]
        self.rooms: List[Room] = []
        self.stair_pos: Tuple[int, int] = (0, 0)
        self.item_positions: List[Tuple[int, int, str]] = []
        self.enemy_spawns: List[Tuple[int, int, str]] = []
        self.occupied_positions = set()

    def generate(self, seed: int = None):
        if seed is not None:
            random.seed(seed)
        num_rooms = random.randint(MIN_ROOMS, MAX_ROOMS)
        attempts  = 0
        
        while len(self.rooms) < num_rooms and attempts < 300:
            attempts += 1
            w = random.randint(MIN_ROOM_SIZE, MAX_ROOM_SIZE)
            h = random.randint(MIN_ROOM_SIZE, MAX_ROOM_SIZE)
            
            if not self.rooms:
                x = random.randint(self.cols // 4, self.cols * 3 // 4 - w)
                y = random.randint(self.rows // 4, self.rows * 3 // 4 - h)
            else:
                base = random.choice(self.rooms)
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(base.w/2 + w/2 + 1, base.w/2 + w/2 + 4)
                x = int(base.center[0] + math.cos(angle) * dist - w/2)
                y = int(base.center[1] + math.sin(angle) * dist - h/2)
                
            x = max(1, min(x, self.cols - w - 2))
            y = max(1, min(y, self.rows - h - 2))
            room = Room(x, y, w, h)
            
            if any(room.intersects(r) for r in self.rooms):
                continue
            
            self._carve_room(room)
            if self.rooms:
                closest_room = min(self.rooms, key=lambda r: math.hypot(r.center[0] - room.center[0], r.center[1] - room.center[1]))
                self._connect_rooms(closest_room.center, room.center)
                
            self.rooms.append(room)

        start_room = self.rooms[0]
        farthest_room = self._find_farthest_room_bfs(start_room.center)
        
        sx, sy = farthest_room.center
        self.tiles[sy][sx] = TILE_STAIR
        self.stair_pos = (sx, sy)
        
        # 위치 겹침 방지 세팅
        self.occupied_positions.clear()
        self.occupied_positions.add(self.stair_pos)
        self.occupied_positions.add(self.player_start())
        
        self._place_items()
        self._place_enemies()

    def _find_farthest_room_bfs(self, start_pos: Tuple[int, int]) -> Room:
        distances = {}
        queue = deque([(start_pos[0], start_pos[1], 0)])
        visited = set([start_pos])

        while queue:
            cx, cy, dist = queue.popleft()
            distances[(cx, cy)] = dist
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = cx + dx, cy + dy
                if self.is_walkable(nx, ny) and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny, dist + 1))

        farthest_room = self.rooms[0]
        max_dist = -1
        for room in self.rooms[1:]:
            d = distances.get(room.center, -1)
            if d > max_dist:
                max_dist = d
                farthest_room = room
        return farthest_room

    def _carve_room(self, room: Room):
        for ry in range(room.y, room.y + room.h):
            for rx in range(room.x, room.x + room.w):
                self.tiles[ry][rx] = TILE_FLOOR

    def _connect_rooms(self, a: Tuple[int, int], b: Tuple[int, int]):
        ax, ay = a
        bx, by = b
        if random.random() < 0.5:
            self._carve_h(ay, ax, bx)
            self._carve_v(bx, ay, by)
        else:
            self._carve_v(ax, ay, by)
            self._carve_h(by, ax, bx)

    def _carve_h(self, y, x1, x2):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.tiles[y][x] = TILE_FLOOR

    def _carve_v(self, x, y1, y2):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.tiles[y][x] = TILE_FLOOR

    def _place_items(self):
        item_names = list(ITEMS.keys())
        item_weights = [ITEMS[name].get("weight", 10) for name in item_names]
        
        placed = 0
        for room in self.rooms[1:]:
            if placed >= ITEMS_PER_FLOOR:
                break
                
            valid_pos = False
            attempts = 0
            rx, ry = 0, 0
            
            # 아이템이 겹쳐 생성되거나 목적지, 적 위에 생성되지 않게 보장
            while not valid_pos and attempts < 20:
                rx = random.randint(room.x, room.x + room.w - 1)
                ry = random.randint(room.y, room.y + room.h - 1)
                if (rx, ry) not in self.occupied_positions and self.tiles[ry][rx] != TILE_STAIR:
                    valid_pos = True
                attempts += 1
                
            if not valid_pos:
                continue
                
            self.occupied_positions.add((rx, ry))
            chosen_item = random.choices(item_names, weights=item_weights, k=1)[0]
            self.item_positions.append((rx, ry, chosen_item))
            placed += 1

    def _place_enemies(self):
        placed = 0
        for room in self.rooms[1:]:
            if placed >= ENEMIES_PER_FLOOR:
                break
                
            valid_pos = False
            attempts = 0
            ex, ey = 0, 0

            # 적이 겹쳐 생성되거나 목적지, 아이템 위에 생성되지 않게 보장
            while not valid_pos and attempts < 20:
                ex = random.randint(room.x + 1, room.x + room.w - 2)
                ey = random.randint(room.y + 1, room.y + room.h - 2)
                if (ex, ey) not in self.occupied_positions and self.tiles[ey][ex] != TILE_STAIR:
                    valid_pos = True
                attempts += 1
                
            if not valid_pos:
                continue

            self.occupied_positions.add((ex, ey))
            etype = "heavy" if random.random() < 0.3 else "normal"
            self.enemy_spawns.append((ex, ey, etype))
            placed += 1

    def is_walkable(self, x: int, y: int) -> bool:
        if 0 <= x < self.cols and 0 <= y < self.rows:
            return self.tiles[y][x] != TILE_WALL
        return False

    def get_tile(self, x: int, y: int) -> int:
        if 0 <= x < self.cols and 0 <= y < self.rows:
            return self.tiles[y][x]
        return TILE_WALL

    def player_start(self) -> Tuple[int, int]:
        return self.rooms[0].center