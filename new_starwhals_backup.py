# -*- coding: utf-8 -*-
import pygame
import math
import numpy as np
import random
# pip install pygame numpy # Make sure these are installed

# Initialize Pygame
pygame.init()

# Get the screen info
screen_info = pygame.display.Info()
WINDOW_WIDTH = screen_info.current_w * 2.5  # Increased map width for obstacles
WINDOW_HEIGHT = (screen_info.current_h - 30) * 2.5 # Increased map height for obstacles
SCREEN_WIDTH = screen_info.current_w
SCREEN_HEIGHT = screen_info.current_h - 30
MIN_ZOOM = 0.35  # Allow slightly more zoom out
MAX_ZOOM = 1.3   # Allow slightly more zoom in
PADDING = 150    # Increased padding
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 120, 255) # Slightly brighter blue
PINK = (255, 120, 255) # Slightly brighter pink
RED = (255, 0, 0)
GRAY = (120, 120, 120) # Slightly darker gray
LIGHT_BLUE = (180, 210, 255)  # Adjusted water color
OBSTACLE_COLOR = (50, 70, 90) # Dark blue/gray for obstacles

# Game Settings
NUM_OBSTACLES = 15
MIN_OBSTACLE_RADIUS = 40
MAX_OBSTACLE_RADIUS = 100

class Obstacle:
    def __init__(self, pos, radius):
        self.pos = np.array(pos, dtype=float)
        self.radius = radius
        # Create slightly irregular shape points
        self.points = []
        num_points = random.randint(7, 12)
        for i in range(num_points):
            angle = (i / num_points) * 2 * math.pi
            dist = random.uniform(0.8, 1.1) * self.radius
            self.points.append([
                self.pos[0] + math.cos(angle) * dist,
                self.pos[1] + math.sin(angle) * dist
            ])

    def draw(self, screen, camera_pos, zoom):
        # Calculate screen position and points
        screen_pos = (self.pos - camera_pos) * zoom + np.array([SCREEN_WIDTH/2, SCREEN_HEIGHT/2])
        
        # Check if obstacle is roughly on screen before drawing detailed points
        on_screen_radius = self.radius * zoom
        if (screen_pos[0] + on_screen_radius < 0 or 
            screen_pos[0] - on_screen_radius > SCREEN_WIDTH or
            screen_pos[1] + on_screen_radius < 0 or
            screen_pos[1] - on_screen_radius > SCREEN_HEIGHT):
            return # Don't draw if completely off-screen

        screen_points = [
            (np.array(p) - camera_pos) * zoom + np.array([SCREEN_WIDTH/2, SCREEN_HEIGHT/2])
            for p in self.points
        ]
        
        # Draw the irregular polygon
        pygame.draw.polygon(screen, OBSTACLE_COLOR, screen_points)
        # Optional outline
        pygame.draw.polygon(screen, GRAY, screen_points, int(max(1, 3 * zoom)))

class Player:
    def __init__(self, pos, angle, color, controls):
        self.pos = np.array(pos, dtype=float)
        self.vel = np.array([0.0, 0.0])
        self.angle = angle
        self.color = color
        self.controls = controls
        self.length = 250  # Slightly longer
        self.width = 65    # Slightly wider
        self.horn_length = 110 # Slightly longer horn
        self.horn_width = 12   # Slightly wider horn
        self.rotation_speed = 4.8 # Slightly increased rotation
        self.thrust = 0.6    # Increased thrust slightly
        self.rotation_momentum = 0.92
        self.max_speed = 14  # Increased max speed
        self.health = 3
        self.max_health = 3
        self.tail_angle = 0
        self.target_tail_angle = 0
        self.tail_length = self.length * 0.75 # Longer tail
        self.tail_response = 0.15
        self.angular_velocity = 0
        self.collision_timer = 0 # Timer to prevent rapid health loss

    def move(self, obstacles, other_player=None):
        if self.health > 0:
            # Cooldown timer
            if self.collision_timer > 0:
                self.collision_timer -= 1
                
            # --- Movement Physics (Rotation, Thrust, Resistance) ---
            # (Keep the existing smoothed movement logic from the previous step)
            # Rotate with momentum
            keys = pygame.key.get_pressed()
            
            # Update angular velocity based on input
            if keys[self.controls[0]]:  # Left
                self.angular_velocity -= 0.85 * (1 + abs(np.linalg.norm(self.vel)) * 0.08) # Slight increase
            elif keys[self.controls[1]]:  # Right
                self.angular_velocity += 0.85 * (1 + abs(np.linalg.norm(self.vel)) * 0.08) # Slight increase
            
            # Apply rotation momentum
            self.angular_velocity *= self.rotation_momentum
            self.angle += self.angular_velocity * self.rotation_speed
            
            # Calculate tail physics with smoother movement
            turn_amount = self.angular_velocity
            self.target_tail_angle = np.clip(turn_amount * -15, -60, 60)
            
            # Tail responds more smoothly to velocity
            if np.linalg.norm(self.vel) > 0.01:
                vel_angle = math.degrees(math.atan2(self.vel[1], self.vel[0]))
                angle_diff = (vel_angle - self.angle) % 360
                if angle_diff > 180: angle_diff -= 360
                self.target_tail_angle += np.clip(angle_diff * 0.4, -45, 45)
            
            # Add natural swaying
            sway_amount = 6 * (1 + min(np.linalg.norm(self.vel) * 0.15, 1.0))
            self.target_tail_angle += math.sin(pygame.time.get_ticks() * 0.003) * sway_amount
            
            # Smoothly interpolate tail angle
            self.tail_angle += (self.target_tail_angle - self.tail_angle) * self.tail_response
            
            # Move forward with momentum
            direction = np.array([math.cos(math.radians(self.angle)), math.sin(math.radians(self.angle))])
            self.vel += direction * self.thrust
            
            # Apply improved water resistance
            speed = np.linalg.norm(self.vel)
            if speed > 0:
                base_resistance = 0.98 # Slightly less resistance
                speed_factor = min(speed / self.max_speed, 1.0)
                resistance = base_resistance - speed_factor * 0.02
                self.vel *= resistance
                if speed > self.max_speed:
                    self.vel = self.vel * (self.max_speed / speed)
            # --- End Movement Physics ---

            # Update position
            new_pos = self.pos + self.vel

            # --- Obstacle Collision ---
            collided = False
            for obs in obstacles:
                dist_vec = new_pos - obs.pos
                distance = np.linalg.norm(dist_vec)
                min_dist = obs.radius + self.width / 3 # Approximate collision radius

                if distance < min_dist:
                    collided = True
                    # Simple bounce effect
                    # Move player back slightly
                    overlap = min_dist - distance
                    new_pos += (dist_vec / distance) * overlap * 1.1 # Move back along collision normal
                    
                    # Reflect velocity (simple perpendicular bounce)
                    normal = dist_vec / distance
                    self.vel = self.vel - 2 * np.dot(self.vel, normal) * normal
                    self.vel *= 0.7 # Dampen velocity after hitting obstacle
                    
                    # Apply slight angular velocity change based on impact side
                    impact_angle_offset = math.degrees(math.atan2(normal[1], normal[0])) - self.angle
                    impact_angle_offset = (impact_angle_offset + 180) % 360 - 180 # Normalize to -180, 180
                    self.angular_velocity += np.sign(impact_angle_offset) * 0.1 # Small spin
                    break # Only handle one collision per frame
            
            self.pos = new_pos
            # --- End Obstacle Collision ---

            # Keep player in bounds (bounce off edges)
            bounce_damping = 0.7
            if self.pos[0] < self.width / 2:
                self.pos[0] = self.width / 2
                self.vel[0] *= -bounce_damping
            elif self.pos[0] > WINDOW_WIDTH - self.width / 2:
                self.pos[0] = WINDOW_WIDTH - self.width / 2
                self.vel[0] *= -bounce_damping
                
            if self.pos[1] < self.width / 2:
                self.pos[1] = self.width / 2
                self.vel[1] *= -bounce_damping
            elif self.pos[1] > WINDOW_HEIGHT - self.width / 2:
                self.pos[1] = WINDOW_HEIGHT - self.width / 2
                self.vel[1] *= -bounce_damping

            # Check collision with other player (only if cooldown finished)
            if other_player and other_player.health > 0 and self.collision_timer <= 0:
                self.check_collision(other_player)

    def check_collision(self, other):
        # Get horn tip position
        horn_tip = self.get_horn_tip()
        
        # Get other player's heart position
        heart_pos = other.get_heart_pos()
        heart_radius = 25 # Effective heart radius for collision
        
        # Check if horn tip hits heart
        distance = np.linalg.norm(horn_tip - heart_pos)
        if distance < heart_radius:
            if other.collision_timer <= 0: # Check if other player is vulnerable
                other.health -= 1
                other.collision_timer = 30 # 0.5 second invulnerability
                self.collision_timer = 15 # Short cooldown for attacker too
                
                # Knockback effect
                knockback_dir = (other.pos - self.pos)
                knockback_dir_norm = knockback_dir / (np.linalg.norm(knockback_dir) + 1e-6) # Avoid division by zero
                knockback_force = 8.0 # Stronger knockback
                
                other.vel += knockback_dir_norm * knockback_force
                self.vel -= knockback_dir_norm * knockback_force * 0.4 # Less knockback for attacker

    def get_horn_tip(self):
        angle_rad = math.radians(self.angle)
        # Calculate horn tip position slightly ahead of the visual tip for better feel
        effective_horn_length = self.length/2 + self.horn_length * 1.1 
        return self.pos + np.array([
            math.cos(angle_rad) * effective_horn_length,
            math.sin(angle_rad) * effective_horn_length
        ])

    def get_heart_pos(self):
        angle_rad = math.radians(self.angle)
        # Position heart slightly further back
        offset_factor = self.length * 0.4 
        return self.pos + np.array([
            -math.cos(angle_rad) * offset_factor,
            -math.sin(angle_rad) * offset_factor
        ])

    def draw(self, screen, camera_pos, zoom):
        if self.health <= 0: return

        # Calculate screen position
        screen_pos = (self.pos - camera_pos) * zoom + np.array([SCREEN_WIDTH/2, SCREEN_HEIGHT/2])
        
        # Don't draw if completely off-screen (approximation)
        render_radius = (self.length / 2 + self.tail_length) * zoom
        if (screen_pos[0] + render_radius < 0 or 
            screen_pos[0] - render_radius > SCREEN_WIDTH or
            screen_pos[1] + render_radius < 0 or
            screen_pos[1] - render_radius > SCREEN_HEIGHT):
            return

        angle_rad = math.radians(self.angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        # --- Refined Narwhal Body Shape ---
        body_front = screen_pos + zoom * np.array([cos_a * self.length/2, sin_a * self.length/2])
        body_rear = screen_pos - zoom * np.array([cos_a * self.length/2, sin_a * self.length/2])
        
        # Wider at the middle, tapering towards front and back
        mid_offset1 = zoom * np.array([-sin_a * self.width * 0.5, cos_a * self.width * 0.5])
        mid_offset2 = zoom * np.array([-sin_a * self.width * 0.4, cos_a * self.width * 0.4]) # Slightly narrower rear middle
        
        # Body points (more curved shape)
        body_points = [
            body_front + zoom * np.array([-sin_a * self.width * 0.1, cos_a * self.width * 0.1]), # Narrow front point 1
            screen_pos + mid_offset1 * 0.8 + zoom * np.array([cos_a * self.length * 0.2, sin_a * self.length * 0.2]), # Mid front curve 1
            screen_pos + mid_offset2 + zoom * np.array([-cos_a * self.length * 0.1, -sin_a * self.length * 0.1]), # Mid rear curve 1
            body_rear + zoom * np.array([-sin_a * self.width * 0.2, cos_a * self.width * 0.2]), # Rear base point 1
            body_rear - zoom * np.array([-sin_a * self.width * 0.2, cos_a * self.width * 0.2]), # Rear base point 2
            screen_pos - mid_offset2 + zoom * np.array([-cos_a * self.length * 0.1, -sin_a * self.length * 0.1]), # Mid rear curve 2
            screen_pos - mid_offset1 * 0.8 + zoom * np.array([cos_a * self.length * 0.2, sin_a * self.length * 0.2]), # Mid front curve 2
            body_front - zoom * np.array([-sin_a * self.width * 0.1, cos_a * self.width * 0.1]), # Narrow front point 2
        ]
        pygame.draw.polygon(screen, self.color, body_points)
        # Optional body outline
        pygame.draw.polygon(screen, tuple(max(0, c-50) for c in self.color), body_points, int(max(1, 2 * zoom)))
        # --- End Refined Body ---

        # --- Draw Tail Fluke ---
        tail_angle_rad = math.radians(self.angle + self.tail_angle)
        cos_t = math.cos(tail_angle_rad)
        sin_t = math.sin(tail_angle_rad)
        tail_base = body_rear # Start fluke from body rear
        
        fluke_width = self.width * 0.8 * zoom
        fluke_length = self.tail_length * 0.5 * zoom # Make fluke part of tail length
        
        # Points for a crescent-like fluke shape
        fluke_p1 = tail_base + np.array([-cos_t * fluke_length * 0.5, -sin_t * fluke_length * 0.5]) + np.array([-sin_t * fluke_width / 2, cos_t * fluke_width / 2])
        fluke_p2 = tail_base + np.array([-cos_t * fluke_length, -sin_t * fluke_length]) # Tip of the fluke indent
        fluke_p3 = tail_base + np.array([-cos_t * fluke_length * 0.5, -sin_t * fluke_length * 0.5]) - np.array([-sin_t * fluke_width / 2, cos_t * fluke_width / 2])
        
        pygame.draw.polygon(screen, self.color, [tail_base, fluke_p1, fluke_p2, fluke_p3])
        # Optional fluke outline
        pygame.draw.polygon(screen, tuple(max(0, c-50) for c in self.color), [tail_base, fluke_p1, fluke_p2, fluke_p3], int(max(1, 2*zoom)))
        # --- End Tail Fluke ---

        # --- Draw Horn ---
        horn_base = body_front # Horn starts from the body front
        horn_tip = horn_base + zoom * np.array([cos_a * self.horn_length, sin_a * self.horn_length])
        # Tapered horn using a thin polygon
        horn_p1 = horn_base + zoom * np.array([-sin_a * self.horn_width * 0.5, cos_a * self.horn_width * 0.5])
        horn_p2 = horn_base - zoom * np.array([-sin_a * self.horn_width * 0.5, cos_a * self.horn_width * 0.5])
        horn_p3 = horn_tip # Tip is a single point
        pygame.draw.polygon(screen, WHITE, [horn_p1, horn_p2, horn_p3])
        # Optional horn outline
        pygame.draw.polygon(screen, GRAY, [horn_p1, horn_p2, horn_p3], int(max(1, 1 * zoom)))
        # --- End Horn ---

        # --- Draw Heart (Polygon Shape) ---
        heart_screen_pos = (self.get_heart_pos() - camera_pos) * zoom + np.array([SCREEN_WIDTH/2, SCREEN_HEIGHT/2])
        heart_size = 15 * zoom # Base size of the heart
        
        # Points for a basic heart shape relative to heart_screen_pos
        heart_points = [
            heart_screen_pos + np.array([0, -0.6 * heart_size]), # Top indent
            heart_screen_pos + np.array([-0.5 * heart_size, -1.1 * heart_size]), # Top left curve point
            heart_screen_pos + np.array([-1.0 * heart_size, -0.6 * heart_size]), # Left middle point
            heart_screen_pos + np.array([0, 1.2 * heart_size]), # Bottom tip
            heart_screen_pos + np.array([1.0 * heart_size, -0.6 * heart_size]), # Right middle point
            heart_screen_pos + np.array([0.5 * heart_size, -1.1 * heart_size]), # Top right curve point
        ]
        
        # Pulsating effect when vulnerable (collision_timer > 0)
        pulse_scale = 1.0
        if self.collision_timer > 0:
             pulse_scale = 1.0 + 0.2 * abs(math.sin(pygame.time.get_ticks() * 0.02))
             # Recalculate points with pulse
             center = heart_screen_pos
             heart_points_pulsed = []
             for p in heart_points:
                 vec = p - center
                 heart_points_pulsed.append(center + vec * pulse_scale)
             heart_points = heart_points_pulsed

        heart_color = RED if self.collision_timer <= 0 else (255, 100, 100) # Lighter red when invulnerable
        
        pygame.draw.polygon(screen, heart_color, heart_points)
        # --- End Heart ---
        
        # --- Draw Health Bar ---
        health_width = 70 * zoom # Slightly wider
        health_height = 12 * zoom # Slightly taller
        health_pos = screen_pos + np.array([-health_width/2, -(self.length / 2 + 40) * zoom]) # Position above narwhal
        
        # Background
        pygame.draw.rect(screen, GRAY, (*health_pos, health_width, health_height), border_radius=int(3*zoom))
        # Health fill
        if self.health > 0:
            health_percent = self.health / self.max_health
            fill_color = (0, 200, 0) # Green health
            pygame.draw.rect(screen, fill_color, 
                (*health_pos, health_width * health_percent, health_height), border_radius=int(3*zoom))
        # Border
        pygame.draw.rect(screen, BLACK, (*health_pos, health_width, health_height), int(max(1, 2*zoom)), border_radius=int(3*zoom))
        # --- End Health Bar ---

# --- Game Setup ---
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Starwhals Evolved")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 48)
font_small = pygame.font.SysFont(None, 32)

# Create players
player1 = Player([WINDOW_WIDTH*0.3, WINDOW_HEIGHT/2], 0, BLUE, [pygame.K_a, pygame.K_d])
player2 = Player([WINDOW_WIDTH*0.7, WINDOW_HEIGHT/2], 180, PINK, [pygame.K_LEFT, pygame.K_RIGHT])
players = [player1, player2]

# Create obstacles, ensuring they don't spawn too close to players
obstacles = []
spawn_area_padding = 300 # Don't spawn obstacles near initial player positions
player_positions = [p.pos for p in players]

while len(obstacles) < NUM_OBSTACLES:
    radius = random.uniform(MIN_OBSTACLE_RADIUS, MAX_OBSTACLE_RADIUS)
    pos = [random.uniform(radius, WINDOW_WIDTH - radius), 
           random.uniform(radius, WINDOW_HEIGHT - radius)]
    
    # Check distance from players
    too_close_to_player = False
    for p_pos in player_positions:
        if np.linalg.norm(np.array(pos) - p_pos) < spawn_area_padding:
            too_close_to_player = True
            break
    if too_close_to_player:
        continue

    # Check distance from other obstacles
    too_close_to_obstacle = False
    for obs in obstacles:
        if np.linalg.norm(np.array(pos) - obs.pos) < obs.radius + radius + 50: # Ensure spacing
             too_close_to_obstacle = True
             break
    if too_close_to_obstacle:
        continue
        
    obstacles.append(Obstacle(pos, radius))

game_state = "playing" # Can be "playing", "game_over"
winner = None

# --- Game Loop ---
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if game_state == "game_over" and event.key == pygame.K_r:
                # Reset game (basic reset)
                player1 = Player([WINDOW_WIDTH*0.3, WINDOW_HEIGHT/2], 0, BLUE, [pygame.K_a, pygame.K_d])
                player2 = Player([WINDOW_WIDTH*0.7, WINDOW_HEIGHT/2], 180, PINK, [pygame.K_LEFT, pygame.K_RIGHT])
                players = [player1, player2]
                game_state = "playing"
                winner = None

    # --- Game Logic ---
    if game_state == "playing":
        # Move players
        player1.move(obstacles, player2)
        player2.move(obstacles, player1)
        
        # Check for game over
        if player1.health <= 0 and player2.health <= 0:
            winner = "Draw!"
            game_state = "game_over"
        elif player1.health <= 0:
            winner = "Player 2 Wins!"
            game_state = "game_over"
        elif player2.health <= 0:
            winner = "Player 1 Wins!"
            game_state = "game_over"

    # --- Camera Calculation ---
    active_players = [p for p in players if p.health > 0]
    
    if len(active_players) == 2:
        # Position camera between players
        camera_pos = (active_players[0].pos + active_players[1].pos) / 2
        
        # Calculate required zoom to keep players in view
        distance = np.linalg.norm(active_players[0].pos - active_players[1].pos) + 1e-6 # Add epsilon
        
        # Calculate zoom based on X and Y distance separately
        required_zoom_x = (SCREEN_WIDTH - 2*PADDING) / (abs(active_players[0].pos[0] - active_players[1].pos[0]) + 1e-6)
        required_zoom_y = (SCREEN_HEIGHT - 2*PADDING) / (abs(active_players[0].pos[1] - active_players[1].pos[1]) + 1e-6)
        
        # Use the smaller zoom level to ensure both axes fit
        target_zoom = min(required_zoom_x, required_zoom_y)
        
        zoom = np.clip(target_zoom, MIN_ZOOM, MAX_ZOOM) # Clamp zoom
        
    elif len(active_players) == 1:
        # Focus on the surviving player
        camera_pos = active_players[0].pos
        zoom = MAX_ZOOM * 0.8 # Zoom in slightly on winner
    else:
        # Both players out, center camera roughly
        camera_pos = np.array([WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2])
        zoom = MIN_ZOOM # Zoom out

    # --- Drawing ---
    screen.fill(LIGHT_BLUE) # Clear screen with water color
    
    # Draw obstacles first (behind players)
    for obs in obstacles:
        obs.draw(screen, camera_pos, zoom)
        
    # Draw players
    for player in players:
        player.draw(screen, camera_pos, zoom)

    # Draw Game Over message
    if game_state == "game_over":
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180)) # Semi-transparent black overlay
        screen.blit(overlay, (0, 0))
        
        winner_text = font.render(winner, True, WHITE)
        winner_rect = winner_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 30))
        screen.blit(winner_text, winner_rect)
        
        restart_text = font_small.render("Press 'R' to Restart or ESC to Quit", True, WHITE)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 30))
        screen.blit(restart_text, restart_rect)
        
    # Update display
    pygame.display.flip()
    clock.tick(FPS)

# Quit game
pygame.quit() 