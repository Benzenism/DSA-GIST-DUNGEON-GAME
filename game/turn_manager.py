from collections import deque
from enum import Enum, auto

class Actor(Enum):
    PLAYER = auto()
    ENEMY  = auto()

class TurnManager:
    def __init__(self):
        self._queue: deque = deque()
        self._enemy_ids: list = []
        self.turn_number: int = 0
        self._reset_queue()

    def _reset_queue(self):
        self._queue.clear()
        self._queue.append((Actor.PLAYER, -1))
        for eid in self._enemy_ids:
            self._queue.append((Actor.ENEMY, eid))

    def set_enemies(self, enemy_ids: list):
        self._enemy_ids = list(enemy_ids)
        self._reset_queue()

    def remove_enemy(self, eid: int):
        if eid in self._enemy_ids:
            self._enemy_ids.remove(eid)
        self._queue = deque(
            (a, i) for a, i in self._queue
            if not (a == Actor.ENEMY and i == eid)
        )

    def current(self):
        return self._queue[0] if self._queue else (Actor.PLAYER, -1)

    def advance(self):
        if not self._queue:
            return
        actor = self._queue.popleft()
        self._queue.append(actor)
        if self._queue[0][0] == Actor.PLAYER:
            self.turn_number += 1

    def is_player_turn(self) -> bool:
        return self.current()[0] == Actor.PLAYER

    def get_current_enemy_id(self) -> int:
        a, eid = self.current()
        return eid if a == Actor.ENEMY else -1