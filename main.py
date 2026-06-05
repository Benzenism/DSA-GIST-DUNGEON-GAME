import pygame
from screens.start_screen  import StartScreen
from screens.game_screen   import GameScreen
from screens.result_screen import ResultScreen
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE

def main():
    pygame.init()
    pygame.display.set_caption(TITLE)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock  = pygame.time.Clock()

    state        = "start"
    player_name  = ""
    game_result  = {}

    start_screen  = StartScreen(screen)
    game_screen   = None
    result_screen = None

    while True:
        clock.tick(FPS)

        if state == "start":
            name = start_screen.run()
            if name is not None:
                player_name = name
                game_screen = GameScreen(screen, player_name)
                state       = "game"

        elif state == "game":
            result = game_screen.run()
            if result is not None:
                game_result   = result
                result_screen = ResultScreen(screen, game_result)
                state         = "result"

        elif state == "result":
            action = result_screen.run()
            if action == "restart":
                start_screen = StartScreen(screen)
                state        = "start"

        pygame.display.flip()

if __name__ == "__main__":
    main()