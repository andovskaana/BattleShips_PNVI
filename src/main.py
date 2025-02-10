import pygame
import sys
from src import menu

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Battleships")
    clock = pygame.time.Clock()
    menu.loading_animation(screen, clock)
    menu.main_menu(pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE))

    # Placeholder for game loop once implemented
    print("Game starting...")

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
