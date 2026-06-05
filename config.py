TITLE          = "Dungeon Master made by EECS 20255022 KIM DOHKYUN"
SCREEN_WIDTH   = 1100
SCREEN_HEIGHT  = 700
FPS            = 60

TILE_SIZE      = 32

MAP_COLS       = 25  
MAP_ROWS       = 19  
MIN_ROOMS      = 4   
MAX_ROOMS      = 6   
MIN_ROOM_SIZE  = 3
MAX_ROOM_SIZE  = 6

VIEW_COLS      = 25
VIEW_ROWS      = 19

TOTAL_FLOORS   = 3

PLAYER_MAX_HP  = 100
PLAYER_ATK     = 20
PLAYER_RANGE   = 1

ENEMY_HP       = 40
ENEMY_ATK      = 10
ENEMY_SIGHT    = 8
ENEMY_SCORE    = 100
ENEMIES_PER_FLOOR = 4
ITEMS_PER_FLOOR   = 3

MAX_UNDO       = 30

ITEMS = {
    "Health Potion":   {"effect": "heal",         "value": 30, "symbol": "P", "color": (255, 80,  80), "weight": 75},
    "Strength Potion": {"effect": "atk_boost",    "value": 10, "symbol": "S", "color": (255, 160,  0), "weight": 15},
    "Health Crystal":  {"effect": "max_hp_boost", "value": 20, "symbol": "C", "color": (80,  255, 80), "weight": 10},
}

C_BG          = (15,  12,  20)
C_WALL        = (55,  50,  70)
C_FLOOR       = (40,  35,  50)
C_PLAYER      = (80,  200, 255)
C_ENEMY       = (220, 70,  70)
C_HEAVY_ENEMY = (160, 40, 180)  
C_STAIR       = (255, 215, 0)
C_UI_BG       = (20,  18,  28)
C_UI_BORDER   = (80,  70,  100)
C_WHITE       = (230, 225, 240)
C_MUTED       = (140, 130, 160)
C_GREEN       = (80,  200, 120)
C_RED         = (220, 70,  70)
C_YELLOW      = (255, 215, 0)
C_ACCENT      = (120, 100, 200)

LEADERBOARD_FILE = "leaderboard.json"