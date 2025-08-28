import pygame
import math
import random
import time
import json

# --- Configuration ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 500
GRID_ROWS = 3
GRID_COLS = 8
CLOCK_RADIUS = 25
CLOCK_PADDING = 30
HAND_LENGTH_H = 18
HAND_LENGTH_M = 23
BACKGROUND_COLOR = (240, 240, 240)
CLOCK_FACE_COLOR = (220, 220, 220)
HAND_COLOR = (20, 20, 20)
TEXT_COLOR = (50, 50, 50)
FPS = 60

# --- Digit Definitions (Ported from your code) ---
# Fractional position of the pointer, 0.0 at 12 o'clock, 0.5 at 6 o'clock
digits_pointer_pos_frac = [
    [[[0.5, 0.5, 0.5, 0.5, 0.25, 0.75], [0.25, 0.75, 0, 0, 0, 0]]],  # 0
    [[[0.625, 0.5, 0.125, 0, 0.625, 0], [0.625, 0.625, 0.125, 0.5, 0.625, 0]]], # 1
    [[[0.25, 0.75, 0.5, 0.75, 0.25, 0.75], [0.25, 0.5, 0.25, 0, 0, 0.75]]],  # 2
    [[[0.25, 0.75, 0.25, 0, 0.25, 0.75], [0.25, 0.5, 0.25, 0.75, 0.25, 0]]],  # 3
    [[[0.5, 0.5, 0, 0, 0.625, 0], [0.5, 0.5, 0.25, 0.5, 0.625, 0]]],  # 4
    [[[0.25, 0.75, 0, 0.5, 0.25, 0], [0.5, 0.75, 0.25, 0.75, 0.25, 0.75]]],  # 5
    [[[0.5, 0.75, 0, 0.75, 0, 0], [0.25, 0.75, 0.5, 0.5, 0.25, 0.75]]],  # 6
    [[[0.25, 0.5, 0.625, 0.5, 0.625, 0], [0.25, 0.75, 0.625, 0, 0.625, 0]]],  # 7
    [[[0.5, 0.5, 0, 0, 0, 0], [0.25, 0.75, 0.25, 0.75, 0.25, 0.75]]],  # 8
    [[[0.5, 0.5, 0.25, 0.5, 0.25, 0], [0.25, 0.75, 0, 0, 0.25, 0.75]]]  # 9
]

# --- Helper Functions ---
def frac_to_rad(frac):
    """Converts fractional rotation (0.0-1.0) to radians."""
    return frac * 2 * math.pi

def lerp_angle(start, end, t):
    """Smoothly interpolate between two angles, handling wraparound."""
    diff = (end - start + math.pi) % (2 * math.pi) - math.pi

    # if its really close to the target snap
    if abs(diff) < 0.01:
        return end
    return start + diff * t

# --- Classes ---
class ClockHand:
    """Represents a single hand of a clock."""
    def __init__(self, length):
        self.length = length
        self.current_angle_rad = 0.0
        self.target_angle_rad = 0.0
        self.easing_factor = 0.1 # Controls animation speed

    def set_target_frac(self, frac):
        self.target_angle_rad = frac_to_rad(frac)

    def update(self):
        """Smoothly moves the hand towards its target angle."""
        self.current_angle_rad = lerp_angle(self.current_angle_rad, self.target_angle_rad, self.easing_factor)

    def draw(self, surface, center_x, center_y):
        end_x = center_x + self.length * math.sin(self.current_angle_rad)
        end_y = center_y - self.length * math.cos(self.current_angle_rad)
        pygame.draw.line(surface, HAND_COLOR, (center_x, center_y), (end_x, end_y), 4)
        pygame.draw.circle(surface, HAND_COLOR, (center_x, center_y), 3)

class Clock:
    """Represents one of the 24 clocks."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.hour_hand = ClockHand(HAND_LENGTH_H)
        self.minute_hand = ClockHand(HAND_LENGTH_M)

    def update(self):
        self.hour_hand.update()
        self.minute_hand.update()

    def draw(self, surface):
        pygame.draw.circle(surface, CLOCK_FACE_COLOR, (self.x, self.y), CLOCK_RADIUS)
        pygame.draw.circle(surface, HAND_COLOR, (self.x, self.y), CLOCK_RADIUS, 1) # Border
        self.hour_hand.draw(surface, self.x, self.y)
        self.minute_hand.draw(surface, self.x, self.y)

class Simulator:
    """Manages the entire simulation and animation logic."""
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("ClockClock24 Simulator")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 24)
        self.font_small = pygame.font.SysFont("Arial", 16)
        
        self.clocks = []
        self.digit_display_indices = [[0, 1, 8, 9, 16, 17], [2, 3, 10, 11, 18, 19], [4, 5, 12, 13, 20, 21], [6, 7, 14, 15, 22, 23]]
        self.column_indices = [[r * 8 + c for r in range(GRID_ROWS)] for c in range(GRID_COLS)]
        self.row_indices = [[r * 8 + c for c in range(GRID_COLS)] for r in range(GRID_ROWS)]

        self.current_animation = None
        self.animation_generator = None
        self.digits_to_display = [0, 0, 0, 0]
        self.animation_name = "Shortest Path"

        self._setup_clocks()
        self.set_digits([1, 2, 3, 4]) # Initial time

        self.hamiltonian_paths = []
        self._load_paths()

        # ... (rest of your __init__ code) ...

    def _load_paths(self):
        """Loads pre-generated paths from a file."""
        try:
            with open("hamiltonian_paths.json", 'r') as f:
                self.hamiltonian_paths = json.load(f)
            print(f"Loaded {len(self.hamiltonian_paths)} Hamiltonian paths.")
        except FileNotFoundError:
            print("Warning: hamiltonian_paths.json not found. Hamiltonian animation will not work.")
            self.hamiltonian_paths = [] # Ensure it's an empty list if file not found
    

    def _setup_clocks(self):
        """Creates and positions the 24 clock objects."""
        grid_width = (GRID_COLS - 1) * (2 * CLOCK_RADIUS + CLOCK_PADDING)
        grid_height = (GRID_ROWS - 1) * (2 * CLOCK_RADIUS + CLOCK_PADDING)
        start_x = (SCREEN_WIDTH - grid_width) / 2
        start_y = (SCREEN_HEIGHT - grid_height) / 2

        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                x = start_x + c * (2 * CLOCK_RADIUS + CLOCK_PADDING)
                y = start_y + r * (2 * CLOCK_RADIUS + CLOCK_PADDING)
                self.clocks.append(Clock(x, y))

    def set_digits(self, digits):
        """Sets the target positions for all clocks based on the desired digits."""
        self.digits_to_display = digits
        for field, digit in enumerate(digits):
            if not (0 <= digit < len(digits_pointer_pos_frac)): continue
            
            digit_data = digits_pointer_pos_frac[digit][0] # Using first style for each digit
            hour_positions = digit_data[0]
            minute_positions = digit_data[1]

            for sub_index, clk_index in enumerate(self.digit_display_indices[field]):
                self.clocks[clk_index].hour_hand.set_target_frac(hour_positions[sub_index])
                self.clocks[clk_index].minute_hand.set_target_frac(minute_positions[sub_index])

    def _get_digit_positions(self, digits):
        """Returns the target positions for all clocks based on the desired digits."""
        new_positions_h = [0.0] * len(self.clocks)
        new_positions_m = [0.0] * len(self.clocks)

        for field, digit in enumerate(digits):
            if not (0 <= digit < len(digits_pointer_pos_frac)): continue
            
            digit_data = digits_pointer_pos_frac[digit][0] # Using first style for each digit
            hour_positions = digit_data[0]
            minute_positions = digit_data[1]

            for sub_index, clk_index in enumerate(self.digit_display_indices[field]):
                new_positions_h[clk_index] = hour_positions[sub_index]
                new_positions_m[clk_index] = minute_positions[sub_index]

        return new_positions_h, new_positions_m

    def run_animation(self, animation_func, new_digits, *args):
        """Starts a new animation using a generator."""
        pos_h, pos_m = self._get_digit_positions(new_digits)
        self.animation_generator = animation_func(pos_h, pos_m, *args)
        self.animation_name = animation_func.__name__.replace("animate_", " ").replace("_", " ").title()

    def run(self):
        """Main simulation loop."""
        running = True
        while running:
            # --- Event Handling ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                        running = False
                    # Set time with number keys
                    if pygame.K_0 <= event.key <= pygame.K_6:
                        num = event.key - pygame.K_0
                        self.digits_to_display = [num, num+1, num+2, num+3] # e.g., 04:40
                        self.run_animation(self.animate_shortest_path, self.digits_to_display)
                    # Trigger animations with letter keys
                    if event.key == pygame.K_s: self.run_animation(self.animate_shortest_path, self.digits_to_display)
                    if event.key == pygame.K_w: self.run_animation(self.animate_straight_wave, self.digits_to_display)
                    if event.key == pygame.K_o: self.run_animation(self.animate_opposing_pointers, self.digits_to_display)
                    if event.key == pygame.K_f: self.run_animation(self.animate_focus, self.digits_to_display)
                    if event.key == pygame.K_p: self.run_animation(self.animate_path_draw, self.digits_to_display)
                    if event.key == pygame.K_g: self.run_animation(self.animate_game_of_life, self.digits_to_display)
                    if event.key == pygame.K_z: self.run_animation(self.animate_zig_zag, self.digits_to_display)


            # --- Animation Logic ---
            if self.animation_generator:
                try:
                    next(self.animation_generator)
                except StopIteration:
                    self.animation_generator = None

            # --- Update ---
            for clock in self.clocks:
                clock.update()

            # --- Drawing ---
            self.screen.fill(BACKGROUND_COLOR)
            for clock in self.clocks:
                clock.draw(self.screen)
            self._draw_ui()
            pygame.display.flip()

            self.clock.tick(FPS)

        pygame.quit()

    def _draw_ui(self):
        """Draws informational text on the screen."""
        time_str = f"Displaying: {self.digits_to_display[0]}{self.digits_to_display[1]}:{self.digits_to_display[2]}{self.digits_to_display[3]}"
        anim_str = f"Animation: {self.animation_name}"
        controls_str = "Controls: [0-9] Set Time | [S,W,O,F,P,G] Animations | [Q] Quit"

        time_surf = self.font.render(time_str, True, TEXT_COLOR)
        anim_surf = self.font.render(anim_str, True, TEXT_COLOR)
        controls_surf = self.font_small.render(controls_str, True, TEXT_COLOR)

        self.screen.blit(time_surf, (20, 20))
        self.screen.blit(anim_surf, (20, 50))
        self.screen.blit(controls_surf, (20, SCREEN_HEIGHT - 40))

    # --- ANIMATION GENERATORS ---
    # Each animation is a generator that yields control back to the main loop each frame.
    
    def animate_shortest_path(self, pos_h, pos_m):
        """Animation: Instantly sets targets for smooth interpolation."""
        for clock_idx in range(len(self.clocks)):
            self.clocks[clock_idx].hour_hand.set_target_frac(pos_h[clock_idx])
            self.clocks[clock_idx].minute_hand.set_target_frac(pos_m[clock_idx])
        yield

    def animate_straight_wave(self, pos_h, pos_m):
        """Animation: Aligns hands, then moves in a wave."""
        start_ang_frac = 0.875
        
        # 1. Move all hands to starting line
        for clock in self.clocks:
            clock.hour_hand.set_target_frac(start_ang_frac - 0.5)
            clock.minute_hand.set_target_frac(start_ang_frac)
        yield from self._wait_for_clocks_to_settle(1.5)

        # 2. Set final targets and trigger wave


        for col in self.column_indices:
            for clk_index in col:
                self.clocks[clk_index].hour_hand.set_target_frac(pos_h[clk_index])
                self.clocks[clk_index].minute_hand.set_target_frac(pos_m[clk_index])
            yield from self._wait_for_duration(0.1) # Delay between columns
        yield

    def animate_opposing_pointers(self, pos_h, pos_m):
        """Animation: All hands meet, then move out in opposite directions."""
        start_ang_frac = 0.5 # 6 o'clock

        # 1. Move all hands to the bottom
        for clock in self.clocks:
            clock.hour_hand.set_target_frac(start_ang_frac)
            clock.minute_hand.set_target_frac(start_ang_frac)
        yield from self._wait_for_clocks_to_settle(1.5)

        for clk_index in range(len(self.clocks)):
            self.clocks[clk_index].hour_hand.set_target_frac(pos_h[clk_index])
            self.clocks[clk_index].minute_hand.set_target_frac(pos_m[clk_index])
        yield

    def animate_focus(self, pos_h, pos_m):
        """Animation: All hands point to the center of the grid."""
        center_x = SCREEN_WIDTH / 2
        center_y = SCREEN_HEIGHT / 2

        # 1. Point all hands to the center
        for clock in self.clocks:
            dx = center_x - clock.x
            dy = center_y - clock.y
            angle_rad = math.atan2(dx, -dy) # atan2(x, -y) for graphical angle
            angle_frac = (angle_rad / (2 * math.pi)) % 1.0
            clock.hour_hand.set_target_frac(angle_frac)
            clock.minute_hand.set_target_frac(angle_frac)
        yield from self._wait_for_clocks_to_settle(2.0)

        for clk_index in range(len(self.clocks)):
            self.clocks[clk_index].hour_hand.set_target_frac(pos_h[clk_index])
            self.clocks[clk_index].minute_hand.set_target_frac(pos_m[clk_index])
        yield

    def animate_path_draw(self, pos_h, pos_m):
        """Animation: Draws a continuous snake-like path."""
        path = random.choice(self.hamiltonian_paths)
        
        direction_to_frac = {-8: 0.0, 8: 0.5, -1: 0.75, 1: 0.25}

        for i, clk_index in enumerate(path):
            in_dir = path[i-1] - clk_index if i > 0 else path[i+1] - clk_index
            out_dir = path[i+1] - clk_index if i < len(path) - 1 else path[i-1] - clk_index

            pos_h_frac = direction_to_frac.get(in_dir, 0.0)
            pos_m_frac = direction_to_frac.get(out_dir, 0.5)

            self.clocks[clk_index].hour_hand.set_target_frac(pos_h_frac)
            self.clocks[clk_index].minute_hand.set_target_frac(pos_m_frac)
            yield from self._wait_for_duration(0.07)
        
        yield from self._wait_for_duration(1.0) # Pause on the full path

        for i, clk_index in enumerate(path):
            pos_h_t = pos_h[clk_index]
            pos_m_t = pos_m[clk_index]
            self.clocks[clk_index].hour_hand.set_target_frac(pos_h_t)
            self.clocks[clk_index].minute_hand.set_target_frac(pos_m_t)
            yield from self._wait_for_duration(0.07)

        yield

    def animate_game_of_life(self, pos_h, pos_m):
        """Animation: Runs Conway's Game of Life."""
        num_generations = 10
        alive_frac = (0.0, 0.5) # Pointing up
        dead_frac = (0.25, 0.75) # Horizontal

        grid = [[random.choice([True, False]) for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]

        for _ in range(num_generations):
            # Display current grid
            for r in range(GRID_ROWS):
                for c in range(GRID_COLS):
                    clk_index = r * GRID_COLS + c
                    h_frac, m_frac = alive_frac if grid[r][c] else dead_frac
                    self.clocks[clk_index].hour_hand.set_target_frac(h_frac)
                    self.clocks[clk_index].minute_hand.set_target_frac(m_frac)
            
            yield from self._wait_for_clocks_to_settle(0.6)

            # Calculate next state
            new_grid = [[False] * GRID_COLS for _ in range(GRID_ROWS)]
            for r in range(GRID_ROWS):
                for c in range(GRID_COLS):
                    live_neighbors = 0
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0: continue
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < GRID_ROWS and 0 <= nc < GRID_COLS and grid[nr][nc]:
                                live_neighbors += 1
                    
                    if grid[r][c] and live_neighbors in [2, 3]: new_grid[r][c] = True
                    elif not grid[r][c] and live_neighbors == 3: new_grid[r][c] = True

            # check if stable
            if new_grid == grid:
                yield from self._wait_for_clocks_to_settle(1.0)
                break
            grid = new_grid

        # Move to final positions
        for clk_index in range(len(self.clocks)):
            self.clocks[clk_index].hour_hand.set_target_frac(pos_h[clk_index])
            self.clocks[clk_index].minute_hand.set_target_frac(pos_m[clk_index])
        yield

    def animate_zig_zag(self, pos_h, pos_m):
        zig_zag_pose_h = [
            0.125, 0.125, 0.375, 0.875, 0.875, 0.125, 0.125, 0.125,
            0.125, 0.125, 0.375, 0.875, 0.875, 0.125, 0.125, 0.125,
            0.125, 0.125, 0.375, 0.875, 0.875, 0.125, 0.125, 0.125
        ]
        zig_zag_pose_m = [
            0.625, 0.625, 0.625, 0.375, 0.375, 0.875, 0.625, 0.625,
            0.625, 0.625, 0.625, 0.375, 0.375, 0.875, 0.625, 0.625,
            0.625, 0.625, 0.625, 0.375, 0.375, 0.875, 0.625, 0.625
        ]

        for clk_index in range(len(self.clocks)):
            self.clocks[clk_index].hour_hand.set_target_frac(zig_zag_pose_h[clk_index])
            self.clocks[clk_index].minute_hand.set_target_frac(zig_zag_pose_m[clk_index])

    def _wait_for_clocks_to_settle(self, duration_s):
        """Helper generator to wait for a fixed duration."""
        start_time = time.time()
        while time.time() - start_time < duration_s:
            yield

    def _wait_for_duration(self, duration_s):
        """Helper generator to wait for a fixed duration."""
        start_time = time.time()
        while time.time() - start_time < duration_s:
            yield

if __name__ == "__main__":
    sim = Simulator()
    sim.run()
