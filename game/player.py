from typing import Dict, Tuple
from config import PLAYER_MAX_HP, PLAYER_ATK, PLAYER_RANGE, ITEMS

class Player:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.hp      = PLAYER_MAX_HP
        self.max_hp  = PLAYER_MAX_HP
        self.atk     = PLAYER_ATK
        self.range   = PLAYER_RANGE
        self.inventory: Dict[str, int] = {}

    def move(self, dx: int, dy: int, dungeon_map, occupied: set) -> bool:
        nx, ny = self.x + dx, self.y + dy
        if dungeon_map.is_walkable(nx, ny) and (nx, ny) not in occupied:
            self.x, self.y = nx, ny
            return True
        return False

    def attack_adjacent(self, enemies: list) -> list:
        hits = []
        for e in enemies:
            if abs(e.x - self.x) <= self.range and abs(e.y - self.y) <= self.range:
                e.hp -= self.atk
                hits.append({"enemy": e, "dmg": self.atk, "killed": e.hp <= 0})
        return hits

    def pick_up(self, item_name: str):
        self.inventory[item_name] = self.inventory.get(item_name, 0) + 1

    def use_item(self, item_name: str) -> str:
        if self.inventory.get(item_name, 0) <= 0:
            return f"No {item_name}!"
        data   = ITEMS.get(item_name, {})
        effect = data.get("effect", "")
        value  = data.get("value", 0)
        
        if effect == "heal":
            self.hp = min(self.max_hp, self.hp + value)
            msg = f"Used {item_name}: +{value} HP"
        elif effect == "atk_boost":
            self.atk += value
            msg = f"Used {item_name}: ATK +{value}"
        elif effect == "max_hp_boost":
            self.max_hp += value
            msg = f"Used {item_name}: Max HP +{value}!"
        else:
            msg = f"Used {item_name}."
            
        self.inventory[item_name] -= 1
        if self.inventory[item_name] == 0:
            del self.inventory[item_name]
        return msg

    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, dmg: int):
        self.hp = max(0, self.hp - dmg)

    @property
    def pos(self) -> Tuple[int, int]:
        return (self.x, self.y)