import json, os
from typing import List, Dict
from config import LEADERBOARD_FILE

def compute_final_score(base_score: int, undo_count: int,
                        elapsed: float, cleared: bool, turns: int) -> int:
    score  = base_score
    score -= undo_count * 50
    score -= int(elapsed * 0.5)
    score -= turns * 2  
    if cleared:
        score += 500
    return max(0, score)

def load_leaderboard() -> List[Dict]:
    if not os.path.exists(LEADERBOARD_FILE):
        return []
    try:
        with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []

def save_entry(name: str, base_score: int, undo_count: int,
               elapsed: float, cleared: bool, turns: int) -> List[Dict]:
    board = load_leaderboard()
    entry = {
        "name":        name,
        "base_score":  base_score,
        "undo_count":  undo_count,
        "elapsed":     round(elapsed, 1),
        "cleared":     cleared,
        "turns":       turns,
        "final_score": compute_final_score(base_score, undo_count, elapsed, cleared, turns),
    }
    board.append(entry)
    
    board.sort(key=lambda e: (
        0 if e.get("cleared") else 1,   
        -e.get("final_score", 0),       
        e.get("undo_count", 0),         
        e.get("turns", 999999),         
        e.get("elapsed", 999999.0)      
    ))
    
    try:
        with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
            json.dump(board, f, ensure_ascii=False, indent=2)
    except IOError:
        pass
    return board