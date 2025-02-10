import pygame
import random
import sys
from src import menu

pygame.init()
# Game Constants
GRID_SIZE = 10
CELL_SIZE = 40
MARGIN = 1  # Thin grid lines
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
PLAYER_OFFSET = 50
AI_OFFSET = 550

# Colors
GRID_LINE = (200, 200, 200)  # Brighter grid color
OCEAN = (50, 100, 180)
HIT_COLOR = (220, 50, 60)
MISS_COLOR = (200, 200, 200)
TEXT_COLOR = (255, 255, 255)
HIGHLIGHT = (100, 200, 100)
INVALID = (200, 50, 50)
FOG_COLOR = (70, 70, 70)  # Semi-transparent dark fog

# Difficulty settings
def set_difficulty(difficulty):
    global AI_SHOT_OPTIONS, MAX_HINTS, ENABLE_FOG, FOG_SIZE
    if difficulty == "EASY":
        AI_SHOT_OPTIONS = [1]
        MAX_HINTS = 3
        ENABLE_FOG = False
    elif difficulty == "HARD":
        AI_SHOT_OPTIONS = [1, 2, 3]
        MAX_HINTS = 5
        ENABLE_FOG = True
        FOG_SIZE = (20, 50)
    elif difficulty == "MEDIUM":
        AI_SHOT_OPTIONS = [1]
        MAX_HINTS = 3
        ENABLE_FOG = True
        FOG_SIZE = (15, 50)

# Ship Configuration
SHIPS = {
    "Battleship": [5, "../assets/Sprites/BT_1_Active", "../assets/Sprites/BT_1_Deactive"],
    "Cruiser": [4, "../assets/Sprites/BT_2_Active", "../assets/Sprites/BT_2_Deactive"],
    "Submarine": [4, "../assets/Sprites/BT_3_Active", "../assets/Sprites/BT_3_Deactive"],
    "Rescue Ship": [3, "../assets/Sprites/BT_4_Active", "../assets/Sprites/BT_4_Deactive"],
    "Destroyer": [2, "../assets/Sprites/BT_5_Active", "../assets/Sprites/BT_5_Deactive"]
}

# Initialize mixer
pygame.mixer.init()
win_sound = pygame.mixer.Sound('../assets/Sounds/win.wav')
win_sound.set_volume(0.7)
lost_sound = pygame.mixer.Sound('../assets/Sounds/lost.mp3')
lost_sound.set_volume(0.7)
explosion_sound = pygame.mixer.Sound("../assets/Sounds/explosion.wav")
explosion_sound.set_volume(0.7)
splash_sound = pygame.mixer.Sound("../assets/Sounds/splash.wav")
splash_sound.set_volume(0.7)
# Fonts
FONT = pygame.font.Font(None, 30)
FONT_LARGE = pygame.font.Font(None, 60)


# 2. Modified Ship class
class Ship:
    def __init__(self, name, size, active_sprite, deactive_sprite):
        self.name = name
        self.size = size
        self.orientation = 'H'
        self.row = -1
        self.col = -1
        # Load H and V sprites for active and deactive states
        self.active_H = pygame.image.load(f"{active_sprite}_H.png").convert_alpha()
        self.active_V = pygame.image.load(f"{active_sprite}_V.png").convert_alpha()
        self.deactive_H = pygame.image.load(f"{deactive_sprite}_H.png").convert_alpha()
        self.deactive_V = pygame.image.load(f"{deactive_sprite}_V.png").convert_alpha()

    def get_sprite(self, is_deactive=False):
        # Choose sprite based on orientation and state
        if self.orientation == 'H':
            img = self.deactive_H if is_deactive else self.active_H
        else:
            img = self.deactive_V if is_deactive else self.active_V

        # Scale the sprite to fit the grid
        if self.orientation == 'H':
            width = CELL_SIZE * self.size - MARGIN
            height = CELL_SIZE - MARGIN
        else:
            width = CELL_SIZE - MARGIN
            height = CELL_SIZE * self.size - MARGIN

        return pygame.transform.scale(img, (width, height))

class Animation:
    def __init__(self, pos, anim_type, board_type):
        self.pos = pos
        self.frame = 0
        self.type = anim_type
        self.last_update = pygame.time.get_ticks()
        self.board_type = board_type

        if anim_type == "explosion":
            self.frames = [pygame.image.load(f"../assets/Animations/fire1_ {i:03}.png") for i in range(13)]
        else:
            self.frames = [pygame.image.load("../assets/Animations/splash.png")]

        self.frames = [pygame.transform.scale(frame, (CELL_SIZE, CELL_SIZE)) for frame in self.frames]

class GameState:
    def __init__(self):
        self.player_board = [[None] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.ai_board = [[None] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.player_hits = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.ai_hits = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.ships = [
            Ship(name, size, active, deactive)
            for name, (size, active, deactive) in SHIPS.items()
        ]
        self.current_ship = 0
        self.animations = []
        self.player_score = 0
        self.ai_score = 0
        self.game_phase = "setup"
        self.player_turn = True
        self.hint_uses = MAX_HINTS
        self.fog_positions = set()
        self.fog_active = ENABLE_FOG
        if self.fog_active:
            self.generate_fog()
        self.probability_map = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]

    def generate_fog(self):
        if not self.fog_active:
            return
        self.fog_positions.clear()
        num_clusters = random.randint(1, 3)
        for _ in range(num_clusters):
            cluster_size = random.randint(*FOG_SIZE)
            start_x, start_y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
            self.expand_fog_cluster(start_x, start_y, cluster_size)

    def expand_fog_cluster(self, x, y, size):
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        cluster = [(x, y)]
        self.fog_positions.add((x, y))
        for _ in range(size - 1):
            if not cluster:
                break
            cx, cy = random.choice(cluster)
            random.shuffle(directions)
            for dx, dy in directions:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE and (nx, ny) not in self.fog_positions:
                    self.fog_positions.add((nx, ny))
                    cluster.append((nx, ny))
                    break

    def remove_fog(self, x, y):
        if (x, y) in self.fog_positions:
            self.fog_positions.remove((x, y))

    def reset(self):
        self.__init__()
        self.place_ai_ships()

    def place_ai_ships(self):
        for ship in self.ships:
            placed = False
            while not placed:
                row = random.randint(0, GRID_SIZE - 1)
                col = random.randint(0, GRID_SIZE - 1)
                orientation = random.choice(['H', 'V'])

                if self.validate_ship_placement(row, col, ship.size, orientation, ai=True):
                    for i in range(ship.size):
                        if orientation == 'H':
                            self.ai_board[row][col + i] = ship
                        else:
                            self.ai_board[row + i][col] = ship
                    placed = True

    def validate_ship_placement(self, row, col, size, orientation, ai=False):
        board = self.ai_board if ai else self.player_board
        if orientation == 'H':
            if col + size > GRID_SIZE:
                return False
            return all(board[row][col + i] is None for i in range(size))
        else:
            if row + size > GRID_SIZE:
                return False
            return all(board[row + i][col] is None for i in range(size))

    def update_probability_map(self):
        self.probability_map = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.ai_hits[y][x] == 2:
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE and self.ai_hits[ny][nx] == 0:
                            self.probability_map[ny][nx] += 10


# 3. Updated draw_grid function
def draw_grid(screen, offset_x, reveal_ships=False, board=None, hits=None, fog_positions=set(), fog_active=False):
    # Draw base grid with lines
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            # Cell background
            rect = pygame.Rect(
                offset_x + col * (CELL_SIZE + MARGIN),
                PLAYER_OFFSET + row * (CELL_SIZE + MARGIN),
                CELL_SIZE,
                CELL_SIZE
            )
            pygame.draw.rect(screen, OCEAN, rect)

            if hits:
                if hits[row][col] == 1:
                    pygame.draw.circle(screen, MISS_COLOR, rect.center, CELL_SIZE // 4)
                elif hits[row][col] == 2:
                    pygame.draw.circle(screen, HIT_COLOR, rect.center, CELL_SIZE // 2)

            if fog_active and (col, row) in fog_positions:
                fog_surface = pygame.Surface((CELL_SIZE, CELL_SIZE))
                fog_surface.fill(FOG_COLOR)
                screen.blit(fog_surface, rect.topleft)
            # Grid lines
            pygame.draw.rect(screen, GRID_LINE, rect, 1)

    # Draw complete ships
    if reveal_ships and board:
        drawn_ships = set()
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                ship = board[row][col]
                if ship and ship not in drawn_ships:
                    drawn_ships.add(ship)

                    # Calculate the ship's start position
                    start_x = offset_x + ship.col * (CELL_SIZE + MARGIN)
                    start_y = PLAYER_OFFSET + ship.row * (CELL_SIZE + MARGIN)

                    # Draw each segment of the ship
                    for i in range(ship.size):
                        if ship.orientation == 'H':
                            segment_rect = pygame.Rect(
                                start_x + i * (CELL_SIZE + MARGIN),
                                start_y,
                                CELL_SIZE,
                                CELL_SIZE
                            )
                        else:
                            segment_rect = pygame.Rect(
                                start_x,
                                start_y + i * (CELL_SIZE + MARGIN),
                                CELL_SIZE,
                                CELL_SIZE
                            )

                        # Check if this segment is hit
                        if ship.orientation == 'H':
                            hit_row = ship.row
                            hit_col = ship.col + i
                        else:
                            hit_row = ship.row + i
                            hit_col = ship.col

                        is_hit = hits and hits[hit_row][hit_col] == 2
                        segment_sprite = ship.get_sprite(is_deactive=is_hit)

                        # Ensure proper transparency handling
                        segment_sprite = segment_sprite.convert_alpha()

                        # Crop the sprite to this segment
                        cropped = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                        if ship.orientation == 'H':
                            cropped.blit(segment_sprite, (0, 0), (i * (CELL_SIZE + MARGIN), 0, CELL_SIZE, CELL_SIZE))
                        else:
                            cropped.blit(segment_sprite, (0, 0), (0, i * (CELL_SIZE + MARGIN), CELL_SIZE, CELL_SIZE))

                        screen.blit(cropped, segment_rect)



def handle_placement_phase(screen, state, mouse_pos):
    ship = state.ships[state.current_ship]
    col = (mouse_pos[0] - PLAYER_OFFSET) // (CELL_SIZE + MARGIN)
    row = (mouse_pos[1] - PLAYER_OFFSET) // (CELL_SIZE + MARGIN)

    valid = False
    if 0 <= col < GRID_SIZE and 0 <= row < GRID_SIZE:
        if ship.orientation == 'H':
            valid = col + ship.size <= GRID_SIZE
        else:
            valid = row + ship.size <= GRID_SIZE

        if valid:
            valid = state.validate_ship_placement(row, col, ship.size, ship.orientation)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN and valid:
            ship.row = row  # Update the ship's row
            ship.col = col  # Update the ship's column
            for i in range(ship.size):
                if ship.orientation == 'H':
                    state.player_board[row][col + i] = ship
                else:
                    state.player_board[row + i][col] = ship
            state.current_ship += 1
            if state.current_ship >= len(state.ships):
                state.game_phase = "playing"

        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            ship.orientation = 'V' if ship.orientation == 'H' else 'H'

    # Inside handle_placement_phase's preview code:
    if valid and state.current_ship < len(state.ships):
        ship = state.ships[state.current_ship]
        if ship.orientation == 'H':
            preview_width = CELL_SIZE * ship.size
            preview_height = CELL_SIZE
        else:
            # HERE WE NEED TO MAKE A TRANSFORM SO IT TRANSFORMS NICELY
            preview_width = CELL_SIZE
            preview_height = CELL_SIZE * ship.size

        preview_rect = pygame.Rect(
            PLAYER_OFFSET + col * CELL_SIZE,
            PLAYER_OFFSET + row * CELL_SIZE,
            preview_width,
            preview_height
        )
        screen.blit(ship.get_sprite(), preview_rect)

    return row, col, valid


def ai_turn(state):
    # Randomly determine number of shots (1-3) with weighted probabilities
    num_shots = random.choice(AI_SHOT_OPTIONS)

    for _ in range(num_shots):
        target = None
        candidates = []

        # Look for high-probability targets first
        max_prob = max(max(row) for row in state.probability_map)
        if max_prob > 0:
            candidates = [(x, y) for y in range(GRID_SIZE) for x in range(GRID_SIZE)
                          if state.probability_map[y][x] == max_prob and state.ai_hits[y][x] == 0]

        # Fallback to random valid target if no high-prob targets
        if not candidates:
            candidates = [(x, y) for y in range(GRID_SIZE) for x in range(GRID_SIZE)
                          if state.ai_hits[y][x] == 0]

        if not candidates:
            break  # No valid targets left

        target = random.choice(candidates)
        x, y = target

        # Process the attack
        if state.player_board[y][x] is not None:
            state.ai_hits[y][x] = 2
            state.animations.append(Animation((x, y), "explosion", "player"))
            explosion_sound.play()
        else:
            state.ai_hits[y][x] = 1
            state.animations.append(Animation((x, y), "splash", "player"))
            splash_sound.play()

        # Update probability after each shot
        state.update_probability_map()

def check_victory(hits, board):
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            if board[y][x] is not None and hits[y][x] != 2:
                return False
    return True

import pygame

def draw_ship_status(screen, state):
    """ Draws the ship status below the grid with correct colors, displaying only horizontal ship images. """
    status_x = PLAYER_OFFSET
    status_y = PLAYER_OFFSET + GRID_SIZE * (CELL_SIZE + MARGIN) + 50  # Move further below the grid

    # Draw the status label
    text = FONT.render("Player | Damaged Ships Status:", True, TEXT_COLOR)
    screen.blit(text, (status_x, status_y))

    # Draw the ships below the label
    offset_x = 120  # Start position after "Damaged Ships Status:" text
    status_y += 40  # Move the ships further down
    for ship in state.ships:
        # Determine the ship's damage state
        damage_status = any(
            state.ai_hits[row][col] == 2
            for row in range(GRID_SIZE)
            for col in range(GRID_SIZE)
            if state.player_board[row][col] == ship
        )

        # Always use the horizontal sprite, regardless of ship orientation
        ship_sprite = ship.active_H if not damage_status else ship.deactive_H
        # Scale the ship sprite to be larger
        scaled_width = CELL_SIZE * ship.size + 10
        scaled_height = CELL_SIZE + 10
        ship_sprite = pygame.transform.scale(ship_sprite, (scaled_width, scaled_height))
        ship_rect = pygame.Rect(status_x + offset_x, status_y, scaled_width, scaled_height)
        screen.blit(ship_sprite, ship_rect)

        offset_x += scaled_width + 20  # Space out the ships more


def main_game(difficulty, screen_mode):
    pygame.init()
    set_difficulty(difficulty)

    # Load and play background music
    pygame.mixer.music.load("../assets/Sounds/valkyries.mid")  # Change this to your actual file path
    pygame.mixer.music.set_volume(0.5)  # Adjust volume (0.0 to 1.0)
    pygame.mixer.music.play(-1)  # Play in an infinite loop

    is_fullscreen = (screen_mode == pygame.FULLSCREEN)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT),
                                     pygame.FULLSCREEN if is_fullscreen else pygame.RESIZABLE)
    pygame.display.set_caption("Battleship Wars")
    clock = pygame.time.Clock()

    state = GameState()
    state.place_ai_ships()

    hint_uses = MAX_HINTS  # Hint counter
    hint_active = False
    hint_positions = []

    while True:
        current_time = pygame.time.get_ticks()
        screen.fill(OCEAN)
        mouse_pos = pygame.mouse.get_pos()

        if state.game_phase == "setup":
            draw_grid(screen, PLAYER_OFFSET, reveal_ships=True, board=state.player_board)
            row, col, valid = handle_placement_phase(screen, state, mouse_pos)

            # Draw current ship info
            if state.current_ship < len(state.ships):
                ship = state.ships[state.current_ship]
                text = FONT.render(f"Placing: {ship.name} ({ship.size} cells)", True, TEXT_COLOR)
                screen.blit(text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT-100))

        elif state.game_phase == "playing":
            draw_grid(screen, PLAYER_OFFSET, reveal_ships=True, board=state.player_board, hits=state.ai_hits)
            draw_grid(screen, AI_OFFSET, hits=state.player_hits, fog_positions=state.fog_positions, fog_active=state.fog_active)

            draw_ship_status(screen, state)
            # Draw hint button, quit button
            hint_button = pygame.Rect(SCREEN_WIDTH - 220, 210, 120, 40)
            pygame.draw.rect(screen, (0, 150, 255), hint_button)
            button_text = FONT.render(f"Hints: {hint_uses}", True, TEXT_COLOR)
            screen.blit(button_text, (SCREEN_WIDTH - 200, 220))

            exit_button = pygame.Rect(SCREEN_WIDTH - 220, 280, 120, 40)
            pygame.draw.rect(screen, (0, 150, 255), exit_button)
            button_text = FONT.render(f"Quit", True, TEXT_COLOR)
            screen.blit(button_text, (SCREEN_WIDTH - 185, 290))

            # Handle animations
            for anim in state.animations[:]:
                frame = anim.frames[min(anim.frame, len(anim.frames) - 1)]
                screen.blit(frame, (
                    (AI_OFFSET if anim.board_type == "ai" else PLAYER_OFFSET) + anim.pos[0] * (CELL_SIZE + MARGIN),
                    PLAYER_OFFSET + anim.pos[1] * (CELL_SIZE + MARGIN)
                ))
                if pygame.time.get_ticks() - anim.last_update > 100:
                    anim.frame += 1
                    anim.last_update = pygame.time.get_ticks()
                    if anim.frame >= len(anim.frames):
                        state.animations.remove(anim)

            # If hint is active, highlight hint positions
            if hint_active:
                for x, y in hint_positions:
                    pygame.draw.rect(screen, HIGHLIGHT, (
                        AI_OFFSET + x * (CELL_SIZE + MARGIN),
                        PLAYER_OFFSET + y * (CELL_SIZE + MARGIN),
                        CELL_SIZE,
                        CELL_SIZE
                    ), 3)

            # Handle player input
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                # Toggle fullscreen when pressing 'F'
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_f:
                        is_fullscreen = not is_fullscreen  # Toggle fullscreen state
                        if is_fullscreen:
                            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
                        else:
                            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos

                    grid_x = (mx - AI_OFFSET) // (CELL_SIZE + MARGIN)
                    grid_y = (my - PLAYER_OFFSET) // (CELL_SIZE + MARGIN)

                    if 0 <= grid_x < GRID_SIZE and 0 <= grid_y < GRID_SIZE:
                        state.player_hits[grid_y][grid_x] = 2 if state.ai_board[grid_y][grid_x] else 1
                        state.player_turn = False
                        state.generate_fog()  # Refresh fog after turn

                    if exit_button.collidepoint(mx, my):
                        print("Quitting game...")
                        menu.main_menu(screen)
                        pygame.mixer.music.pause()  # Pauses music
                        return  # Exit the menu function without quitting pygame

                    # If clicking the hint button
                    if hint_button.collidepoint(mx, my) and hint_uses > 0 and not hint_active:
                        hint_active = True
                        hint_uses -= 1

                        # Find all available positions
                        all_positions = [(x, y) for y in range(GRID_SIZE) for x in range(GRID_SIZE)
                                         if state.player_hits[y][x] == 0]
                        ship_positions = [(x, y) for x, y in all_positions if state.ai_board[y][x] is not None]
                        non_ship_positions = [(x, y) for x, y in all_positions if state.ai_board[y][x] is None]

                        # Ensure one position has a ship
                        hint_positions = []
                        if len(ship_positions) >= 1:
                            hint_positions.append(random.choice(ship_positions))

                        # Add two random non-ship positions
                        if len(non_ship_positions) >= 2:
                            hint_positions += random.sample(non_ship_positions, 2)
                        elif len(non_ship_positions) == 1:
                            hint_positions.append(non_ship_positions[0])

                        # Shuffle to randomize the order of the hint positions
                        random.shuffle(hint_positions)


                    # If clicking a hint position
                    elif hint_active:
                        grid_x = (mx - AI_OFFSET) // (CELL_SIZE + MARGIN)
                        grid_y = (my - PLAYER_OFFSET) // (CELL_SIZE + MARGIN)

                        if (grid_x, grid_y) in hint_positions:
                            if state.ai_board[grid_y][grid_x] is not None:
                                state.player_hits[grid_y][grid_x] = 2
                                state.animations.append(Animation((grid_x, grid_y), "explosion", "ai"))
                                explosion_sound.play()
                            else:
                                state.player_hits[grid_y][grid_x] = 1
                                state.animations.append(Animation((grid_x, grid_y), "splash", "ai"))
                                splash_sound.play()

                            hint_active = False
                            state.player_turn = False

                    # If normally clicking to attack AI board
                    elif not hint_active:
                        grid_x = (mx - AI_OFFSET) // (CELL_SIZE + MARGIN)
                        grid_y = (my - PLAYER_OFFSET) // (CELL_SIZE + MARGIN)

                        if 0 <= grid_x < GRID_SIZE and 0 <= grid_y < GRID_SIZE:
                            if state.player_hits[grid_y][grid_x] == 0:
                                if state.ai_board[grid_y][grid_x] is not None:
                                    state.player_hits[grid_y][grid_x] = 2
                                    state.animations.append(Animation((grid_x, grid_y), "explosion", "ai"))
                                    explosion_sound.play()
                                else:
                                    state.player_hits[grid_y][grid_x] = 1
                                    state.animations.append(Animation((grid_x, grid_y), "splash", "ai"))
                                    splash_sound.play()

                                state.player_turn = False

            # AI's turn
            if not state.player_turn:
                ai_turn(state)
                state.player_turn = True

            # Check victory
            if check_victory(state.player_hits, state.ai_board):
                state.player_score += 1
                state.game_phase = "gameover"
            elif check_victory(state.ai_hits, state.player_board):
                state.ai_score += 1
                state.game_phase = "gameover"

        elif state.game_phase == "gameover":
            pygame.mixer.music.stop()  # Stop the current music
            pygame.time.delay(1500)
            if state.player_score == 1:
                win_sound.play()
                text = FONT_LARGE.render(f"YOU WIN!", True, TEXT_COLOR)
            else:
                lost_sound.play()
                text = FONT_LARGE.render(f"YOU LOST!", True, TEXT_COLOR)
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
            pygame.display.flip()
            pygame.time.delay(3000)
            state.reset()
            pygame.mixer.music.play(-1)  # Restart the music from the beginning
            hint_uses = MAX_HINTS  # Reset hint counter
            hint_active = False

        # Draw UI elements
        if difficulty == "MEDIUM":
            turn_text = FONT.render("Difficulty: Medium | Fog: Active | Enemy MultiShot: Inactive", True, TEXT_COLOR)
        elif difficulty == "HARD":
            turn_text = FONT.render("Difficulty: Hard | Fog: Active | Enemy MultiShot: Active", True, TEXT_COLOR)
        else:
            turn_text = FONT.render("Difficulty: Easy | Fog: Inactive | Enemy MultiShot: Inactive", True, TEXT_COLOR)
        screen.blit(turn_text, (20, 20))

        pygame.display.flip()
        clock.tick(30)
# TESTING
#if __name__ == "__main__":
#    main_game("MEDIUM", pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT)))