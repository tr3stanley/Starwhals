# -*- coding: utf-8 -*-
import pygame
import math
import numpy as np
import random

# Initialize Pygame
pygame.init()

# Get the screen info
screen_info = pygame.display.Info()
WINDOW_WIDTH = screen_info.current_w * 2  # Doubled map width
WINDOW_HEIGHT = (screen_info.current_h - 30) * 2  # Doubled map height
SCREEN_WIDTH = screen_info.current_w
SCREEN_HEIGHT = screen_info.current_h - 30
MIN_ZOOM = 0.4  # Maximum zoom out (smaller number = more zoomed out)
MAX_ZOOM = 1.2  # Maximum zoom in
PADDING = 100   # Minimum pixels from narwhal to screen edge
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 100, 255)
PINK = (255, 100, 255)
RED = (255, 0, 0)
GRAY = (100, 100, 100)
LIGHT_BLUE = (200, 230, 255)  # Lighter water color

# Camera class to handle zooming and panning
class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.zoom = 1.0
        self.target_zoom = 1.0
        self.zoom_speed = 0.1
    
    def update(self, player1_pos, player2_pos):
        # Calculate the box that contains both players
        min_x = min(player1_pos[0], player2_pos[0])
        max_x = max(player1_pos[0], player2_pos[0])
        min_y = min(player1_pos[1], player2_pos[1])
        max_y = max(player1_pos[1], player2_pos[1])
        
        # Calculate the box dimensions
        box_width = max_x - min_x + PADDING * 2
        box_height = max_y - min_y + PADDING * 2
        
        # Calculate required zoom to fit the box
        zoom_x = SCREEN_WIDTH / box_width
        zoom_y = SCREEN_HEIGHT / box_height
        self.target_zoom = min(zoom_x, zoom_y)
        
        # Clamp zoom to limits
        self.target_zoom = np.clip(self.target_zoom, MIN_ZOOM, MAX_ZOOM)
        
        # Smoothly interpolate current zoom to target zoom
        self.zoom += (self.target_zoom - self.zoom) * self.zoom_speed
        
        # Calculate center position of players
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        # Calculate camera position (centered on players)
        self.x = center_x - SCREEN_WIDTH / (2 * self.zoom)
        self.y = center_y - SCREEN_HEIGHT / (2 * self.zoom)
        
        # Keep camera within map bounds
        self.x = np.clip(self.x, 0, WINDOW_WIDTH - SCREEN_WIDTH / self.zoom)
        self.y = np.clip(self.y, 0, WINDOW_HEIGHT - SCREEN_HEIGHT / self.zoom)
    
    def apply(self, pos):
        # Convert world coordinates to screen coordinates
        screen_x = (pos[0] - self.x) * self.zoom
        screen_y = (pos[1] - self.y) * self.zoom
        return np.array([screen_x, screen_y])
    
    def apply_rect(self, rect):
        # Convert world rectangle to screen rectangle
        screen_x = (rect.x - self.x) * self.zoom
        screen_y = (rect.y - self.y) * self.zoom
        screen_width = rect.width * self.zoom
        screen_height = rect.height * self.zoom
        return pygame.Rect(screen_x, screen_y, screen_width, screen_height)

# Function to check if position is clear of obstacles and other spawn points
def is_position_clear(x, y, obstacles, spawn_points, min_distance=400):  # Increased safe distance
    # Check distance from other spawn points
    for sx, sy in spawn_points:
        if math.dist((x, y), (sx, sy)) < min_distance:
            return False
    
    # Check if position overlaps with any obstacle
    test_rect = pygame.Rect(x - 160, y - 160, 320, 320)  # Larger safe area
    for obstacle in obstacles:
        if test_rect.colliderect(obstacle.rect):
            return False
    return True

# Obstacle class
class Obstacle:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        
    def draw(self, screen):
        pygame.draw.rect(screen, GRAY, self.rect)

# Player class
class Player:
    def __init__(self, x, y, color, controls):
        self.pos = np.array([float(x), float(y)])
        self.vel = np.array([0.0, 0.0])
        self.angle = 0
        self.color = color
        # Calculate lighter belly color (30% lighter for more contrast)
        self.belly_color = tuple(min(c + 75, 255) for c in color)
        self.controls = controls
        self.length = 240  # Slightly longer body
        self.width = 60    # Slightly wider body
        self.horn_length = 100  # Longer horn
        self.horn_width = 10    # Slightly wider horn
        self.rotation_speed = 4.5  # Reduced for smoother turning
        self.thrust = 0.5    # Reduced for better control
        self.rotation_momentum = 0.92  # New: maintains some rotation after key release
        self.max_speed = 12  # New: maximum speed cap
        self.health = 3    
        self.max_health = 3
        # Tail joint properties
        self.tail_angle = 0
        self.target_tail_angle = 0
        self.tail_length = self.length * 0.7  # Longer tail
        self.tail_response = 0.15  # Reduced for smoother tail movement
        self.angular_velocity = 0  # New: for smooth rotation
        
    def move(self, obstacles, other_player=None):
        try:
            prev_pos = self.pos.copy()
            prev_angle = self.angle
            
            # Rotate with momentum
            keys = pygame.key.get_pressed()
            
            # Update angular velocity based on input
            if keys[self.controls[0]]:  # Left
                self.angular_velocity -= 0.8 * (1 + abs(np.linalg.norm(self.vel)) * 0.08)
            elif keys[self.controls[1]]:  # Right
                self.angular_velocity += 0.8 * (1 + abs(np.linalg.norm(self.vel)) * 0.08)
            
            # Apply rotation momentum
            self.angular_velocity *= self.rotation_momentum
            self.angle += self.angular_velocity * self.rotation_speed
            
            # Calculate tail physics with smoother movement
            turn_amount = self.angular_velocity
            self.target_tail_angle = np.clip(turn_amount * -15, -60, 60)  # More natural tail movement
            
            # Tail responds more smoothly to velocity
            if np.linalg.norm(self.vel) > 0.01:
                vel_angle = math.degrees(math.atan2(self.vel[1], self.vel[0]))
                angle_diff = (vel_angle - self.angle) % 360
                if angle_diff > 180:
                    angle_diff -= 360
                self.target_tail_angle += np.clip(angle_diff * 0.4, -45, 45)  # Gentler response
            
            # Add natural swaying with smoother velocity influence
            sway_amount = 6 * (1 + min(np.linalg.norm(self.vel) * 0.15, 1.0))
            self.target_tail_angle += math.sin(pygame.time.get_ticks() * 0.003) * sway_amount
            
            # Smoothly interpolate tail angle
            self.tail_angle += (self.target_tail_angle - self.tail_angle) * self.tail_response
            
            # Move forward with momentum
            direction = np.array([math.cos(math.radians(self.angle)), 
                                math.sin(math.radians(self.angle))])
            self.vel += direction * self.thrust
            
            # Apply improved water resistance
            speed = np.linalg.norm(self.vel)
            if speed > 0:
                # Progressive resistance (more at higher speeds)
                base_resistance = 0.985
                speed_factor = min(speed / self.max_speed, 1.0)
                resistance = base_resistance - speed_factor * 0.02
                
                # Apply resistance
                self.vel *= resistance
                
                # Cap maximum speed
                if speed > self.max_speed:
                    self.vel = self.vel * (self.max_speed / speed)
            
            # Update position
            self.pos += self.vel
            
            # Keep narwhal on screen with bounce
            bounce_factor = 0.8
            if self.pos[0] < self.length/2:
                self.pos[0] = self.length/2
                self.vel[0] = abs(self.vel[0]) * bounce_factor
            elif self.pos[0] > WINDOW_WIDTH - self.length/2:
                self.pos[0] = WINDOW_WIDTH - self.length/2
                self.vel[0] = -abs(self.vel[0]) * bounce_factor
            if self.pos[1] < self.length/2:
                self.pos[1] = self.length/2
                self.vel[1] = abs(self.vel[1]) * bounce_factor
            elif self.pos[1] > WINDOW_HEIGHT - self.length/2:
                self.pos[1] = WINDOW_HEIGHT - self.length/2
                self.vel[1] = -abs(self.vel[1]) * bounce_factor
            
            # Obstacle collision detection and response with improved physics
            narwhal_radius = self.width * 0.6
            for obstacle in obstacles:
                # Calculate closest point on obstacle to narwhal center
                closest_x = max(obstacle.rect.left, min(self.pos[0], obstacle.rect.right))
                closest_y = max(obstacle.rect.top, min(self.pos[1], obstacle.rect.bottom))
                
                # Calculate distance to closest point
                distance_x = self.pos[0] - closest_x
                distance_y = self.pos[1] - closest_y
                distance = math.sqrt(distance_x**2 + distance_y**2)
                
                # Check for collision
                if distance < narwhal_radius:
                    # Calculate collision normal
                    if distance > 0:
                        normal = np.array([distance_x, distance_y]) / distance
                    else:
                        normal = np.array([1, 0])
                    
                    # Move narwhal out of obstacle
                    overlap = narwhal_radius - distance
                    self.pos += normal * overlap * 1.1  # Slight extra push to prevent sticking
                    
                    # Calculate bounce response with angular momentum
                    dot_product = np.dot(self.vel, normal)
                    self.vel -= 2.0 * dot_product * normal  # Perfect reflection
                    self.vel *= 0.85  # Energy loss
                    
                    # Add spin based on collision angle
                    collision_angle = math.degrees(math.atan2(normal[1], normal[0]))
                    angle_diff = (collision_angle - self.angle) % 360
                    if angle_diff > 180:
                        angle_diff -= 360
                    self.angle += angle_diff * 0.15  # More pronounced rotation effect
                    
                    # Add some randomness to prevent getting stuck
                    self.vel += np.array([random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2)])
            
            # Player collision with improved physics
            if other_player:
                dist = math.dist(self.pos, other_player.pos)
                if dist > 0:  # Prevent division by zero
                    min_dist = (self.width + other_player.width) * 0.6  # Slightly reduced collision radius
                    
                    if dist < min_dist:
                        # Calculate collision normal
                        normal = (self.pos - other_player.pos) / dist
                        
                        # Calculate relative velocity
                        rel_vel = self.vel - other_player.vel
                        
                        # Calculate impulse
                        impulse = -1.8 * np.dot(rel_vel, normal)  # More bouncy collision
                        
                        # Apply impulse
                        self.vel += normal * impulse * 0.5
                        
                        # Add some spin based on collision angle
                        collision_angle = math.degrees(math.atan2(normal[1], normal[0]))
                        angle_diff = (collision_angle - self.angle) % 360
                        if angle_diff > 180:
                            angle_diff -= 360
                        self.angle += angle_diff * 0.1
                        
                        # Move apart to prevent sticking
                        overlap = min_dist - dist
                        self.pos += normal * (overlap * 0.6)  # Move more to prevent sticking
                        
                        # Add slight random movement to prevent getting stuck
                        self.vel += np.array([random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3)])
        except Exception as e:
            print(f"Error in move: {e}")
            # Restore previous position if there's an error
            self.pos = prev_pos
    
    def get_horn_tip(self):
        angle_rad = math.radians(self.angle)
        tip_x = self.pos[0] + math.cos(angle_rad) * (self.length/2 + self.horn_length)
        tip_y = self.pos[1] + math.sin(angle_rad) * (self.length/2 + self.horn_length)
        return (tip_x, tip_y)
        
    def draw_heart(self, screen, pos, size):
        try:
            x, y = pos
            radius = size // 3
            
            # Draw the heart with a gradient effect
            for i in range(3):  # Multiple layers for depth
                scale = 1 - i * 0.15  # Each layer slightly smaller
                current_radius = int(radius * scale)
                current_x = x
                current_y = y + i * 2  # Slight vertical offset for depth
                
                # Create darker red for depth
                dark_red = (max(200 - i * 30, 120), 0, 0)
                
                # Draw two circles for the top of the heart
                pygame.draw.circle(screen, dark_red, 
                                 (current_x - current_radius//2, current_y), 
                                 current_radius)
                pygame.draw.circle(screen, dark_red, 
                                 (current_x + current_radius//2, current_y), 
                                 current_radius)
                
                # Draw triangle for bottom of heart
                points = [
                    (current_x - current_radius, current_y + current_radius//2),
                    (current_x + current_radius, current_y + current_radius//2),
                    (current_x, current_y + int(size * 0.7 * scale))
                ]
                pygame.draw.polygon(screen, dark_red, points)
            
            # Add highlight effect
            highlight_pos = (x - radius//4, y - radius//4)
            highlight_radius = radius // 4
            pygame.draw.circle(screen, (255, 180, 180), highlight_pos, highlight_radius)
            
            # Add outline for better definition
            outline_points = [
                (x - radius, y + radius//2),
                (x + radius, y + radius//2),
                (x, y + int(size * 0.7))
            ]
            pygame.draw.circle(screen, (100, 0, 0), 
                             (x - radius//2, y), 
                             radius, 
                             2)  # Left circle outline
            pygame.draw.circle(screen, (100, 0, 0), 
                             (x + radius//2, y), 
                             radius, 
                             2)  # Right circle outline
            pygame.draw.polygon(screen, (100, 0, 0), outline_points, 2)  # Bottom outline
            
        except Exception as e:
            print(f"Error drawing heart: {e}")
            # Fallback to simple circle if there's an error
            try:
                pygame.draw.circle(screen, RED, pos, size // 2)
            except:
                pass

    def draw(self, screen):
        try:
            angle_rad = math.radians(self.angle)
            tail_angle_rad = math.radians(self.angle + self.tail_angle)
            
            # Calculate key positions and dimensions
            total_body_length = self.length
            body_length = total_body_length * 0.66
            tail_length = total_body_length * 0.34
            first_tail_length = tail_length * 0.85
            second_tail_length = tail_length * 0.15
            
            # Adjust positions for better overlap
            body_center = self.pos + np.array([math.cos(angle_rad), math.sin(angle_rad)]) * (body_length * 0.2)
            # Move tail start further inside the body for better overlap
            tail_start = self.pos - np.array([math.cos(angle_rad), math.sin(angle_rad)]) * (body_length * 0.2)
            tail_joint = tail_start - np.array([math.cos(tail_angle_rad), math.sin(tail_angle_rad)]) * first_tail_length
            tail_end = tail_joint - np.array([math.cos(tail_angle_rad), math.sin(tail_angle_rad)]) * second_tail_length
            
            # 1. Draw oval body with wider front and lighter belly
            body_points_top = []
            body_points_bottom = []
            num_points = 32
            
            for i in range(num_points):
                try:
                    t = i / (num_points - 1) * 2 * math.pi
                    # Create oval shape with wider front
                    x = math.cos(t) * (body_length * 0.5)
                    # Modify width based on position (wider at front, normal at back)
                    width_factor = 1.0 + 0.15 * math.cos(t)  # 15% wider at front
                    y = math.sin(t) * (self.width * 0.5 * width_factor)
                    
                    # Rotate the point
                    rotated_x = x * math.cos(angle_rad) - y * math.sin(angle_rad)
                    rotated_y = x * math.sin(angle_rad) + y * math.cos(angle_rad)
                    
                    # Translate to body center
                    point = body_center + np.array([rotated_x, rotated_y])
                    
                    # Ensure point is within screen bounds
                    point[0] = np.clip(point[0], 0, WINDOW_WIDTH)
                    point[1] = np.clip(point[1], 0, WINDOW_HEIGHT)
                    
                    # Split points into top and bottom for different colors
                    if t <= math.pi:
                        body_points_top.append(point)
                    else:
                        body_points_bottom.append(point)
                except Exception as e:
                    print(f"Error calculating body point {i}: {e}")
                    continue
            
            # Draw bottom (belly) part first
            if len(body_points_bottom) >= 2:
                points = [body_center] + body_points_bottom + [body_center]
                pygame.draw.polygon(screen, self.belly_color, points)
            
            # Draw top part
            if len(body_points_top) >= 2:
                points = [body_center] + body_points_top + [body_center]
                pygame.draw.polygon(screen, self.color, points)
            
            # 2. Draw first tail triangle with thinner base and better overlap
            try:
                tail_width_start = self.width * 0.72  # 20% thinner (0.9 * 0.8)
                tail_width_middle = self.width * 0.24  # Keep proportional
                
                # Draw an overlap circle at the connection point for smoother transition
                overlap_radius = tail_width_start * 0.6
                pygame.draw.circle(screen, self.color, 
                                 (int(tail_start[0]), int(tail_start[1])), 
                                 int(overlap_radius))
                
                first_tail_points = [
                    tail_start + np.array([math.cos(tail_angle_rad + math.pi/2), math.sin(tail_angle_rad + math.pi/2)]) * tail_width_start/2,
                    tail_joint + np.array([math.cos(tail_angle_rad + math.pi/2), math.sin(tail_angle_rad + math.pi/2)]) * tail_width_middle/2,
                    tail_joint + np.array([math.cos(tail_angle_rad - math.pi/2), math.sin(tail_angle_rad - math.pi/2)]) * tail_width_middle/2,
                    tail_start + np.array([math.cos(tail_angle_rad - math.pi/2), math.sin(tail_angle_rad - math.pi/2)]) * tail_width_start/2
                ]
                first_tail_points = [(np.clip(p[0], 0, WINDOW_WIDTH), np.clip(p[1], 0, WINDOW_HEIGHT)) for p in first_tail_points]
                pygame.draw.polygon(screen, self.color, first_tail_points)
            except Exception as e:
                print(f"Error drawing first tail: {e}")
            
            # 3. Draw second tail triangle with better overlap
            try:
                tail_width_end = self.width * 1.4
                
                # Draw an overlap circle at the joint for smoother transition
                overlap_radius = tail_width_middle * 0.8
                pygame.draw.circle(screen, self.color, 
                                 (int(tail_joint[0]), int(tail_joint[1])), 
                                 int(overlap_radius))
                
                second_tail_points = [
                    tail_joint + np.array([math.cos(tail_angle_rad + math.pi/2), math.sin(tail_angle_rad + math.pi/2)]) * tail_width_middle/2,
                    tail_end + np.array([math.cos(tail_angle_rad + math.pi/2), math.sin(tail_angle_rad + math.pi/2)]) * tail_width_end/2,
                    tail_end + np.array([math.cos(tail_angle_rad - math.pi/2), math.sin(tail_angle_rad - math.pi/2)]) * tail_width_end/2,
                    tail_joint + np.array([math.cos(tail_angle_rad - math.pi/2), math.sin(tail_angle_rad - math.pi/2)]) * tail_width_middle/2
                ]
                second_tail_points = [(np.clip(p[0], 0, WINDOW_WIDTH), np.clip(p[1], 0, WINDOW_HEIGHT)) for p in second_tail_points]
                pygame.draw.polygon(screen, self.color, second_tail_points)
            except Exception as e:
                print(f"Error drawing second tail: {e}")
            
            # 4. Draw straight horn
            try:
                horn_base = body_center + np.array([math.cos(angle_rad), math.sin(angle_rad)]) * (body_length * 0.5)
                horn_tip = horn_base + np.array([math.cos(angle_rad), math.sin(angle_rad)]) * self.horn_length
                
                horn_points = [
                    horn_base + np.array([math.cos(angle_rad + math.pi/2), math.sin(angle_rad + math.pi/2)]) * self.horn_width,
                    horn_tip + np.array([math.cos(angle_rad + math.pi/2), math.sin(angle_rad + math.pi/2)]) * (self.horn_width * 0.3),
                    horn_tip + np.array([math.cos(angle_rad - math.pi/2), math.sin(angle_rad - math.pi/2)]) * (self.horn_width * 0.3),
                    horn_base + np.array([math.cos(angle_rad - math.pi/2), math.sin(angle_rad - math.pi/2)]) * self.horn_width
                ]
                # Clip points to screen
                horn_points = [(np.clip(p[0], 0, WINDOW_WIDTH), np.clip(p[1], 0, WINDOW_HEIGHT)) for p in horn_points]
                pygame.draw.polygon(screen, self.color, horn_points)
            except Exception as e:
                print(f"Error drawing horn: {e}")
            
            # 5. Draw angry eyes
            try:
                # Calculate eye position
                eye_pos = body_center + np.array([
                    math.cos(angle_rad + math.pi/4) * self.width * 0.4,
                    math.sin(angle_rad + math.pi/4) * self.width * 0.4
                ])
                eye_pos = (int(np.clip(eye_pos[0], 6, WINDOW_WIDTH-6)), 
                          int(np.clip(eye_pos[1], 6, WINDOW_HEIGHT-6)))
                
                # Draw white of eye
                pygame.draw.circle(screen, WHITE, eye_pos, 8)
                
                # Draw black pupil (slightly offset downward for angry look)
                pupil_pos = (eye_pos[0], eye_pos[1] + 1)
                pygame.draw.circle(screen, BLACK, pupil_pos, 4)
                
                # Draw angry eyebrow
                brow_length = 12
                brow_thickness = 3
                
                # Calculate eyebrow angle (angled down towards center)
                brow_angle = angle_rad + math.pi/4 - math.pi/6  # Angled for angry look
                
                # Calculate eyebrow points
                brow_start = np.array([
                    eye_pos[0] - math.cos(brow_angle) * brow_length,
                    eye_pos[1] - math.sin(brow_angle) * brow_length - 4
                ])
                brow_end = np.array([
                    eye_pos[0] + math.cos(brow_angle) * brow_length,
                    eye_pos[1] + math.sin(brow_angle) * brow_length - 4
                ])
                
                # Draw thick eyebrow line
                pygame.draw.line(screen, self.color, brow_start, brow_end, brow_thickness)
                
                # Draw eyelid (curved line above eye)
                eyelid_points = []
                for i in range(5):
                    t = i / 4  # 0 to 1
                    lid_angle = brow_angle - math.pi/8 * math.sin(t * math.pi)  # Curved angle
                    lid_point = np.array([
                        eye_pos[0] + math.cos(lid_angle) * 8 * (t - 0.5),
                        eye_pos[1] + math.sin(lid_angle) * 8 * (t - 0.5) - 2
                    ])
                    eyelid_points.append(lid_point)
                
                # Draw eyelid
                if len(eyelid_points) >= 2:
                    pygame.draw.lines(screen, self.color, False, eyelid_points, 2)
                
            except Exception as e:
                print(f"Error drawing eyes: {e}")
            
            # 6. Draw heart
            try:
                heart_pos = (int(np.clip(self.pos[0], 24, WINDOW_WIDTH-24)), 
                           int(np.clip(self.pos[1], 24, WINDOW_HEIGHT-24)))
                self.draw_heart(screen, heart_pos, 28)  # Slightly larger heart
            except Exception as e:
                print(f"Error drawing heart: {e}")
                
        except Exception as e:
            print(f"Error in draw: {e}")
            # Draw a simple rectangle as fallback
            try:
                pygame.draw.rect(screen, self.color, (int(self.pos[0]-10), int(self.pos[1]-10), 20, 20))
            except:
                pass

# Game setup
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Narwhal Battle")
clock = pygame.time.Clock()

# Create camera
camera = Camera()

# Create spawn points list
spawn_points = []

# Create players with safe spawning
player1_x = WINDOW_WIDTH/4
player1_y = WINDOW_HEIGHT/2
spawn_points.append((player1_x, player1_y))

player2_x = 3*WINDOW_WIDTH/4
player2_y = WINDOW_HEIGHT/2
spawn_points.append((player2_x, player2_y))

# Create obstacles with safe distance from players
obstacles = []
max_attempts = 200  # More attempts for larger map
num_obstacles = 30  # More obstacles for larger map

while len(obstacles) < num_obstacles and max_attempts > 0:
    x = random.randint(400, WINDOW_WIDTH-400)
    y = random.randint(400, WINDOW_HEIGHT-400)
    width = random.randint(100, 200)
    height = random.randint(100, 200)
    
    if is_position_clear(x, y, obstacles, spawn_points):
        obstacles.append(Obstacle(x, y, width, height))
    max_attempts -= 1

# Create players
player1 = Player(player1_x, player1_y, BLUE, [pygame.K_a, pygame.K_d])
player2 = Player(player2_x, player2_y, PINK, [pygame.K_LEFT, pygame.K_RIGHT])

# Game loop
running = True
while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
    
    # Update
    player1.move(obstacles, player2)
    player2.move(obstacles, player1)
    
    # Update camera
    camera.update(player1.pos, player2.pos)
    
    # Collision detection
    p1_tip = player1.get_horn_tip()
    p2_tip = player2.get_horn_tip()
    
    # Check if player1's horn hits player2's heart
    if math.dist(p1_tip, player2.pos) < 15:
        player2.health -= 1
        # Add bounce effect
        direction = player2.pos - player1.pos
        direction = direction / np.linalg.norm(direction)  # Normalize
        player1.vel -= direction * 15  # Push player1 back
        player2.vel += direction * 15  # Push player2 away
        
    # Check if player2's horn hits player1's heart
    if math.dist(p2_tip, player1.pos) < 15:
        player1.health -= 1
        # Add bounce effect
        direction = player1.pos - player2.pos
        direction = direction / np.linalg.norm(direction)  # Normalize
        player2.vel -= direction * 15  # Push player2 back
        player1.vel += direction * 15  # Push player1 away
    
    # Draw
    screen.fill(LIGHT_BLUE)
    
    # Draw obstacles with camera transform
    for obstacle in obstacles:
        screen_rect = camera.apply_rect(obstacle.rect)
        pygame.draw.rect(screen, GRAY, screen_rect)
    
    # Draw players with camera transform
    for player in [player1, player2]:
        # Save original position
        orig_pos = player.pos.copy()
        # Apply camera transform
        player.pos = camera.apply(player.pos)
        # Scale the player size with zoom
        orig_length = player.length
        orig_width = player.width
        orig_horn_length = player.horn_length
        orig_horn_width = player.horn_width
        player.length *= camera.zoom
        player.width *= camera.zoom
        player.horn_length *= camera.zoom
        player.horn_width *= camera.zoom
        # Draw
        player.draw(screen)
        # Restore original values
        player.pos = orig_pos
        player.length = orig_length
        player.width = orig_width
        player.horn_length = orig_horn_length
        player.horn_width = orig_horn_width
    
    # Draw health bars (fixed to screen)
    for i in range(player1.max_health):
        x = 50 + i * 40
        color = BLUE if i < player1.health else (100, 100, 100)
        pygame.draw.circle(screen, color, (x, 50), 15)
    
    for i in range(player2.max_health):
        x = SCREEN_WIDTH - 150 + i * 40  # Adjusted for screen width
        color = PINK if i < player2.health else (100, 100, 100)
        pygame.draw.circle(screen, color, (x, 50), 15)
    
    # Check win condition
    if player1.health <= 0 or player2.health <= 0:
        winner = "Player 2" if player1.health <= 0 else "Player 1"
        font = pygame.font.Font(None, 74)
        text = font.render(f"{winner} Wins!", True, WHITE)
        screen.blit(text, (SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT/2))
        pygame.display.flip()
        pygame.time.wait(2000)
        running = False
    
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit() 