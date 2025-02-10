import pygame
from pygame.locals import MOUSEBUTTONDOWN
import sys
import math
import random
import time

from src import game
from src.config import TITLE_FONT, OPTION_FONT, WHITE, BLACK

# Screen settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WATER_LEVEL = SCREEN_HEIGHT - 300

# TEXT Colors
BUTTON_COLOR = (50, 50, 50)
BUTTON_BORDER_COLOR = (200, 200, 200)
BUTTON_HOVER_COLOR = (80, 80, 80)
TEXT_COLOR = WHITE

# Colors
COLORS = {
    "deep_water": (0, 40, 85),
    "mid_water": (0, 76, 102),
    "shallow_water": (0, 105, 148),
    "foam": (200, 220, 255),
    "sparkle": (255, 255, 200)
}

class Button:
    def __init__(self, x, y, width, height, text=None, image=None, font=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.image = image
        self.font = font or pygame.font.Font(None, 40)
        self.clicked = False

    def draw(self, screen):
        # Check if the mouse is over the button
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            color = BUTTON_HOVER_COLOR
        else:
            color = BUTTON_COLOR

        # Draw button background and border
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, BUTTON_BORDER_COLOR, self.rect, width=2, border_radius=10)

        # Draw text or image
        if self.text:
            text_surf = self.font.render(self.text, True, TEXT_COLOR)
            text_rect = text_surf.get_rect(center=self.rect.center)
            screen.blit(text_surf, text_rect)
        elif self.image:
            image_rect = self.image.get_rect(center=self.rect.center)
            screen.blit(self.image, image_rect)

    def is_clicked(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False

class Submarine(pygame.sprite.Sprite):
    def __init__(self, screen_width, water_level, sprite_images):
        super().__init__()
        self.screen_width = screen_width
        self.water_level = water_level
        self.sprite_images = sprite_images
        self.image = random.choice(self.sprite_images)  # Randomize initial sprite
        self.rect = self.image.get_rect()
        self.width = self.rect.width
        self.height = self.rect.height
        self.reset_position()

    def reset_position(self):
        """Reset the submarine's position and direction."""
        self.direction = random.choice([-1, 1])  # -1: right-to-left, 1: left-to-right
        self.image = random.choice(self.sprite_images)  # Randomize sprite again
        if self.direction == 1:
            self.x = -self.width  # Start off-screen left
        else:
            self.x = self.screen_width  # Start off-screen right
            self.image = pygame.transform.flip(self.image, True, False)  # Flip for left-facing
        self.y = WATER_LEVEL - self.height // 2 +100# Adjust to submerge half of the submarine
        self.speed = random.uniform(1.2, 2.5)  # Randomize speed
        self.visible = True

    def update(self):
        """Update the submarine's position and handle resetting when off-screen."""
        if self.direction == 1:  # Moving left-to-right
            self.x += self.speed
            if self.x > self.screen_width:  # Off-screen right
                self.reset_position()
        else:  # Moving right-to-left
            self.x -= self.speed
            if self.x < -self.width:  # Off-screen left
                self.reset_position()

    def draw(self, screen):
        """Draw the submarine with a clipped area to simulate submersion."""
        if self.visible:
            # Define a clipping rectangle that matches the water level
            clip_rect = pygame.Rect(0, 0, self.screen_width, WATER_LEVEL + 100)
            screen.set_clip(clip_rect)  # Set clipping area

            # Draw the submarine (only the part above water will be visible)
            screen.blit(self.image, (self.x, self.y))

            # Reset clipping to draw other elements normally
            screen.set_clip(None)

class Wave:
    def __init__(self, y_offset, speed, amplitude, length):
        self.y_offset = y_offset
        self.speed = speed
        self.amplitude = amplitude
        self.length = length
        self.phase = random.uniform(0, 2 * math.pi)

class Slider:
    def __init__(self, x, y, width, min_val, max_val, initial_val):
        self.rect = pygame.Rect(x, y, width, 20)
        self.min_val = min_val
        self.max_val = max_val
        self.val = initial_val
        self.dragging = False

    def draw(self, screen):
        pygame.draw.rect(screen, BUTTON_COLOR, self.rect, border_radius=10)
        handle_x = self.rect.x + int((self.val - self.min_val) / (self.max_val - self.min_val) * self.rect.width)
        pygame.draw.circle(screen, BUTTON_HOVER_COLOR, (handle_x, self.rect.centery), 10)

    def update(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            mouse_x = event.pos[0]
            self.val = max(self.min_val, min(self.max_val, self.min_val + (mouse_x - self.rect.x) / self.rect.width * (self.max_val - self.min_val)))

class WaterAnimation:
    def __init__(self, screen):
        self.screen = screen
        self.waves = [
            Wave(y_offset=0, speed=0.8, amplitude=25, length=200),
            Wave(y_offset=30, speed=1.0, amplitude=20, length=180),
            Wave(y_offset=60, speed=1.2, amplitude=15, length=160),
            Wave(y_offset=90, speed=1.4, amplitude=10, length=140)
        ]
        self.sparkles = []
        self.foam_particles = []
        self.gradient = self.create_gradient_background()

    def create_gradient_background(self):
        gradient = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = COLORS["deep_water"][0] * (1 - t) + COLORS["shallow_water"][0] * t
            g = COLORS["deep_water"][1] * (1 - t) + COLORS["shallow_water"][1] * t
            b = COLORS["deep_water"][2] * (1 - t) + COLORS["shallow_water"][2] * t
            pygame.draw.line(gradient, (int(r), int(g), int(b)), (0, y), (SCREEN_WIDTH, y))
        return gradient

    def update_waves(self):
        for wave in self.waves:
            wave.phase += wave.speed * 0.05
            wave.phase %= 2 * math.pi

    def draw_waves(self):
        """Draw all wave layers with dynamic lighting"""
        for i, wave in enumerate(self.waves):
            color = pygame.Color(*COLORS["mid_water"])
            color.hsla = (210, 40, 30 + i * 5, 0)

            points = []
            for x in range(-50, SCREEN_WIDTH + 50, 5):
                y = WATER_LEVEL + wave.y_offset
                y += math.sin(x / wave.length + wave.phase) * wave.amplitude
                points.append((x, y))

            if len(points) > 2:
                pygame.draw.polygon(self.screen, color,
                                    points + [(SCREEN_WIDTH + 50, SCREEN_HEIGHT), (-50, SCREEN_HEIGHT)])

    def add_sparkles(self):
        """Add light sparkles to water surface"""
        if random.random() < 0.05:
            x = random.randint(0, SCREEN_WIDTH)
            y = WATER_LEVEL - random.randint(0, 50)
            self.sparkles.append([x, y, random.randint(5, 15)])

    def update_sparkles(self):
        """Animate and remove old sparkles"""
        new_sparkles = []
        for sparkle in self.sparkles:
            sparkle[1] -= 0.5
            sparkle[2] -= 0.1
            if sparkle[2] > 0:
                new_sparkles.append(sparkle)
        self.sparkles = new_sparkles

    def draw_sparkles(self):
        """Draw light sparkles"""
        for x, y, size in self.sparkles:
            alpha = min(255, int(size * 50))
            surface = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(surface, (*COLORS["sparkle"], alpha), (3, 3), int(size / 2))
            self.screen.blit(surface, (x - 3, y - 3))

    def add_foam(self):
        """Add foam particles at wave peaks"""
        for wave in self.waves[:2]:  # Only top waves get foam
            for _ in range(2):
                x = random.randint(0, SCREEN_WIDTH)
                wave_y = WATER_LEVEL + wave.y_offset + math.sin(x / wave.length + wave.phase) * wave.amplitude
                self.foam_particles.append([x, wave_y, random.uniform(1.0, 2.0)])

    def update_foam(self):
        """Animate and remove old foam particles"""
        new_foam = []
        for particle in self.foam_particles:
            particle[0] += random.uniform(-0.5, 0.5)
            particle[1] += random.uniform(-0.2, 0.5)
            particle[2] -= 0.02
            if particle[2] > 0:
                new_foam.append(particle)
        self.foam_particles = new_foam

    def draw_foam(self):
        """Draw foam particles"""
        for x, y, size in self.foam_particles:
            alpha = min(255, int(size * 120))
            surface = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(surface, (*COLORS["foam"], alpha), (4, 4), int(size))
            self.screen.blit(surface, (x - 4, y - 4))

    def draw_background(self):
        self.screen.blit(self.gradient, (0, 0))
        self.update_waves()
        self.draw_waves()

        self.add_sparkles()
        self.update_sparkles()
        self.draw_sparkles()

        self.add_foam()
        self.update_foam()
        self.draw_foam()

def draw_text(screen, text, font, color, x, y):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(x, y))
    screen.blit(text_surface, text_rect)


def loading_animation(screen, clock):
    screen.fill(BLACK)
    pygame.display.flip()

    font = pygame.font.Font(None, 50)

    for alpha in range(0, 256, 5):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        screen.fill(BLACK)
        text_surface_creator = font.render("Creator:", True, (alpha, alpha, alpha))
        text_rect_creator = text_surface_creator.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        text_surface_name = font.render("ANA ANDOVSKA", True, (alpha, alpha, alpha))
        text_rect_name = text_surface_name.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
        screen.blit(text_surface_creator, text_rect_creator)
        screen.blit(text_surface_name, text_rect_name)
        pygame.display.flip()
        clock.tick(30)

    pygame.time.wait(1000)

    for alpha in range(255, -1, -5):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(WHITE)
        overlay.set_alpha(255 - alpha)
        screen.blit(overlay, (0, 0))
        pygame.display.flip()
        clock.tick(30)

    pygame.time.wait(500)

def load_submarine_sprites():
    """Load submarine sprite images."""
    sprites = []
    for i in range(1, 6):  # 5 sprite images
        sprite = pygame.image.load(f"../assets/Menu/submarine{i}.png").convert_alpha()
        sprites.append(pygame.transform.scale(sprite, (140, 100)))  # Resize if needed
    return sprites


def main_menu(screen_mode):
    pygame.init()

    # Load and play background music
    pygame.mixer.music.load("../assets/Sounds/mars.mid")  # Change this to your actual file path
    pygame.mixer.music.set_volume(0.5)  # Adjust volume (0.0 to 1.0)
    pygame.mixer.music.play(-1)  # Play in an infinite loop

    is_fullscreen = (screen_mode == pygame.FULLSCREEN)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT),
                                     pygame.FULLSCREEN if is_fullscreen else pygame.RESIZABLE)
    pygame.display.set_caption("Battleships")
    clock = pygame.time.Clock()

    water_animation = WaterAnimation(screen)
    submarine_sprites = load_submarine_sprites()
    submarine = Submarine(SCREEN_WIDTH, WATER_LEVEL, submarine_sprites)

    instructions_icon = pygame.image.load("../assets/Menu/help_icon.png").convert_alpha()
    exit_icon = pygame.image.load("../assets/Menu/exit_icon.png").convert_alpha()
    instructions_icon = pygame.transform.scale(instructions_icon, (100, 100))
    exit_icon = pygame.transform.scale(exit_icon, (55, 55))

    start_button = Button(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2, 400, 70, text="Start Game", font=TITLE_FONT)
    instructions_button = Button(SCREEN_WIDTH // 2 - 300, SCREEN_HEIGHT // 2 + 150, 100, 100, image=instructions_icon)
    exit_button = Button(SCREEN_WIDTH // 2 + 200, SCREEN_HEIGHT // 2 + 150, 100, 100, image=exit_icon)

    easy_button = Button(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 150, 400, 70, text="EASY", font=TITLE_FONT)
    medium_button = Button(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 50, 400, 70, text="MEDIUM", font=TITLE_FONT)
    hard_button = Button(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 + 50, 400, 70, text="HARD", font=TITLE_FONT)
    back_button = Button(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 + 150, 400, 70, text="BACK", font=TITLE_FONT)

    instructions_font = pygame.font.Font(None, 36)
    instructions_text = [
        "",
        "Game Controls:",
        "- Mouse Click: Place ships, attack enemy grid.",
        "- Spacebar: Rotate ship orientation.",
        "- Hint Button: Reveal ship locations (limited).",
        "- Quit Button: Exit the game.",
        "- F Key: Toggle Fullscreen mode.",
    ]

    logo_image = pygame.image.load("../assets/Menu/battleship_logo.png").convert_alpha()
    logo_image = pygame.transform.scale(logo_image, (300, 300))
    logo_rect = logo_image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))

    global show_difficulty_buttons, show_instructions
    show_difficulty_buttons = False
    show_instructions = False
    selected_difficulty = None

    while True:
        screen.fill(BLACK)
        water_animation.draw_background()
        submarine.update()
        submarine.draw(screen)

        if show_instructions:
            # Draw a semi-transparent background for the instructions
            pygame.draw.rect(screen, BUTTON_COLOR,
                             (SCREEN_WIDTH // 4, SCREEN_HEIGHT // 4, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2),
                             border_radius=15)
            pygame.draw.rect(screen, BUTTON_BORDER_COLOR,
                             (SCREEN_WIDTH // 4, SCREEN_HEIGHT // 4, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), width=2,
                             border_radius=15)

            # Dynamically render instructions text
            y_offset = SCREEN_HEIGHT // 4 + 30
            for line in instructions_text:
                text_surface = instructions_font.render(line, True, WHITE)
                text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
                screen.blit(text_surface, text_rect)
                y_offset += 40  # Adjust vertical spacing for each line of text

            back_button.draw(screen)
        elif not show_difficulty_buttons:
            screen.blit(logo_image, logo_rect)
            start_button.draw(screen)
            instructions_button.draw(screen)
            exit_button.draw(screen)
        else:
            easy_color = (255, 0, 0) if selected_difficulty == "EASY" else (50, 50, 50)
            medium_color = (255, 0, 0) if selected_difficulty == "MEDIUM" else (50, 50, 50)
            hard_color = (255, 0, 0) if selected_difficulty == "HARD" else (50, 50, 50)

            pygame.draw.rect(screen, easy_color, easy_button.rect, border_radius=10)
            pygame.draw.rect(screen, medium_color, medium_button.rect, border_radius=10)
            pygame.draw.rect(screen, hard_color, hard_button.rect, border_radius=10)

            easy_button.draw(screen)
            medium_button.draw(screen)
            hard_button.draw(screen)
            back_button.draw(screen)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if show_instructions:
                if back_button.is_clicked(event):
                    show_instructions = False
            elif not show_difficulty_buttons:
                if start_button.is_clicked(event):
                    show_difficulty_buttons = True
                elif instructions_button.is_clicked(event):
                    show_instructions = True
                elif exit_button.is_clicked(event):
                    pygame.quit()
                    sys.exit()
            else:
                if easy_button.is_clicked(event):
                    selected_difficulty = "EASY"
                    game.main_game(difficulty=selected_difficulty, screen_mode=screen_mode)
                    return
                elif medium_button.is_clicked(event):
                    selected_difficulty = "MEDIUM"
                    game.main_game(difficulty=selected_difficulty, screen_mode=screen_mode)
                    return
                elif hard_button.is_clicked(event):
                    selected_difficulty = "HARD"
                    game.main_game(difficulty=selected_difficulty, screen_mode=screen_mode)
                    return
                elif back_button.is_clicked(event):
                    show_difficulty_buttons = False
                    selected_difficulty = None

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f:
                    screen_mode = pygame.FULLSCREEN if screen_mode == pygame.RESIZABLE else pygame.RESIZABLE
                    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), screen_mode)
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        clock.tick(60)
