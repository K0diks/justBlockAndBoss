import pygame
import sys
import math
import random
from pygame import gfxdraw
from pygame import mixer
import json
import os

# Инициализация Pygame
pygame.init()

# Константы
WIDTH, HEIGHT = 800, 600
FPS = 60

# Состояния игры
MENU = 0
SETTINGS = 1
GAME_RUNNING = 2
GAME_OVER = 3
GAME_WIN = 4

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)


# Настройки по умолчанию
try:
    with open('settings.json', 'r') as f:
        settings = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    settings = {
        'music_volume': 0.5,
        'sound_volume': 0.7,
        'difficulty': 'normal'
    }
    # Если использовались настройки по умолчанию, сохраним их в файл
if not os.path.exists('settings.json'):
    with open('settings.json', 'w') as f:
        json.dump(settings, f, indent=4)

# Инициализация экрана
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Just Block and Boss")
clock = pygame.time.Clock()

# Загрузка музыки
try:
    mixer.init()
    menu_music = "menu.mp3"  # Замените на свой файл
    game_music = "music.mp3"  # Замените на свой файл
    
    # Загрузка звуков
    shoot_sound = mixer.Sound("shoot.wav")
    hit_sound = mixer.Sound("hit.wav")
    button_sound = mixer.Sound("button.wav")
    sound_enabled = True
except:
    sound_enabled = False
    print("Звуковая система не загружена!")

# Класс кнопки
class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.font = pygame.font.Font(None, 36)
        
    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=10)
        
        text_surf = self.font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered
        
    def is_clicked(self, pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False

# Класс слайдера для настроек
class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, initial_val):
        self.rect = pygame.Rect(x, y, width, height)
        self.min = min_val
        self.max = max_val
        self.val = initial_val
        self.dragging = False
        self.handle_rect = pygame.Rect(x, y - 5, 20, height + 10)
        
    def draw(self, surface):
        # Фон слайдера
        pygame.draw.rect(surface, (50, 50, 50), self.rect, border_radius=5)
        
        # Заполненная часть
        filled_width = int((self.val - self.min) / (self.max - self.min) * self.rect.width)
        filled_rect = pygame.Rect(self.rect.x, self.rect.y, filled_width, self.rect.height)
        pygame.draw.rect(surface, GREEN, filled_rect, border_radius=5)
        
        # Контур
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=5)
        
        # Ползунок
        self.handle_rect.x = self.rect.x + filled_width - 10
        pygame.draw.rect(surface, RED, self.handle_rect, border_radius=5)
        
    def update(self, pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.handle_rect.collidepoint(pos) or self.rect.collidepoint(pos):
                self.dragging = True
                
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
            
        if self.dragging and event.type == pygame.MOUSEMOTION:
            rel_x = pos[0] - self.rect.x
            rel_x = max(0, min(rel_x, self.rect.width))
            self.val = self.min + (rel_x / self.rect.width) * (self.max - self.min)
            return True
        return False

# Класс пули
class Projectile:
    def __init__(self, x, y, angle=0, speed=5, size=10, color=(255,0,0)):
        self.x = x
        self.y = y
        self.speed = speed
        self.angle = angle
        self.size = size
        self.color = color
        self.glow_size = size * 2
        self.glow_surface = pygame.Surface((self.glow_size*2, self.glow_size*2), pygame.SRCALPHA)
        pygame.draw.circle(self.glow_surface, (*color[:3], 50), (self.glow_size, self.glow_size), self.glow_size)
    
    def update(self):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
    
    def draw(self):
        # Тень пули
        shadow = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
        pygame.draw.circle(shadow, (0,0,0,150), (self.size, self.size), self.size//2)
        screen.blit(shadow, (int(self.x) - self.size, int(self.y) - self.size))
        
        # Свечение
        screen.blit(self.glow_surface, (int(self.x) - self.glow_size, int(self.y) - self.glow_size))
        # Сама пуля
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size//2)

# Класс частиц
class Particle:
    def __init__(self, x, y, color, particle_type="normal"):
        self.x = x
        self.y = y
        self.base_color = color
        self.color = color
        self.size = random.randint(2, 8) if particle_type == "normal" else random.randint(1, 15)
        self.life = random.randint(30, 90) if particle_type == "normal" else random.randint(10, 150)
        self.max_life = self.life
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-3, 3)
        self.gravity = random.uniform(-0.05, 0.1)
        self.fade = random.uniform(0.8, 0.99)
        self.type = particle_type
        self.angle = 0
        self.rotation_speed = random.uniform(-0.1, 0.1)
        
        # Для эффектных частиц
        if self.type == "special":
            self.size = random.randint(5, 20)
            self.shape = random.choice(["circle", "rect", "star"])
            self.color = (
                random.randint(max(0, color[0]-50), min(255, color[0]+50)),
                random.randint(max(0, color[1]-50), min(255, color[1]+50)),
                random.randint(max(0, color[2]-50), min(255, color[2]+50))
            )
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.life -= 1
        self.angle += self.rotation_speed
        self.vx *= self.fade
        self.vy *= self.fade
        
        if self.type == "special":
            self.color = (
                min(255, self.color[0] + random.randint(-5, 5)),
                min(255, self.color[1] + random.randint(-5, 5)),
                min(255, self.color[2] + random.randint(-5, 5))
            )
    
    def draw(self):
        alpha = min(255, self.life * 3)
        current_size = max(1, self.size * (self.life/self.max_life))
        
        try:
            if self.type == "normal":
                pygame.gfxdraw.filled_circle(
                    screen, int(self.x), int(self.y), int(current_size), 
                    (*self.color, alpha)
                )
                # Добавляем свечение
                glow_size = current_size * 2
                glow_surf = pygame.Surface((glow_size*2, glow_size*2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*self.color, alpha//3), 
                                (glow_size, glow_size), glow_size)
                screen.blit(glow_surf, (int(self.x-glow_size), int(self.y-glow_size)))
                
            elif self.type == "special":
                if self.shape == "circle":
                    pygame.gfxdraw.filled_circle(
                        screen, int(self.x), int(self.y), int(current_size), 
                        (*self.color, alpha)
                    )
                elif self.shape == "rect":
                    # Исправленная версия для прямоугольников
                    s = pygame.Surface((int(current_size*2), int(current_size*2)), pygame.SRCALPHA)
                    pygame.draw.rect(
                        s, 
                        (self.color[0], self.color[1], self.color[2], alpha), 
                        (0, 0, int(current_size*2), int(current_size*2))
                    )
                    s = pygame.transform.rotate(s, self.angle)
                    screen.blit(s, (int(self.x-current_size), int(self.y-current_size)))
                elif self.shape == "star":
                    points = []
                    for i in range(5):
                        angle = self.angle + math.pi * 2 * i / 5
                        points.append((
                            self.x + math.cos(angle) * current_size,
                            self.y + math.sin(angle) * current_size
                        ))
                        angle += math.pi / 5
                        points.append((
                            self.x + math.cos(angle) * current_size * 0.5,
                            self.y + math.sin(angle) * current_size * 0.5
                        ))
                    pygame.gfxdraw.filled_polygon(screen, points, (*self.color, alpha))
        except:
            # Если произошла ошибка при отрисовке, просто пропускаем эту частицу
            pass

# Функции меню
def main_menu():
    play_button = Button(WIDTH//2 - 100, HEIGHT//2 - 80, 200, 50, "Играть", BLUE, PURPLE)
    settings_button = Button(WIDTH//2 - 100, HEIGHT//2, 200, 50, "Настройки", BLUE, PURPLE)
    quit_button = Button(WIDTH//2 - 100, HEIGHT//2 + 80, 200, 50, "Выход", BLUE, PURPLE)
    
    if sound_enabled:
        pygame.mixer.music.load(menu_music)
        pygame.mixer.music.set_volume(settings['music_volume'])
        pygame.mixer.music.play(-1)
    
    while True:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            play_button.check_hover(mouse_pos)
            settings_button.check_hover(mouse_pos)
            quit_button.check_hover(mouse_pos)
            
            if play_button.is_clicked(mouse_pos, event):
                if sound_enabled:
                    button_sound.play()
                    pygame.mixer.music.fadeout(500)
                return GAME_RUNNING
                
            if settings_button.is_clicked(mouse_pos, event):
                if sound_enabled:
                    button_sound.play()
                return SETTINGS
                
            if quit_button.is_clicked(mouse_pos, event):
                if sound_enabled:
                    button_sound.play()
                    pygame.time.delay(200)
                pygame.quit()
                sys.exit()
        
        # Отрисовка
        screen.fill(BLACK)
        
        # Фоновые звезды
        
        # Заголовок
        title_font = pygame.font.Font(None, 72)
        title_text = title_font.render("Just Block and Boss", True, WHITE)
        screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, 100))
        
        # Кнопки
        play_button.draw(screen)
        settings_button.draw(screen)
        quit_button.draw(screen)
        
        pygame.display.flip()
        clock.tick(FPS)

# Функция настроек
def settings_menu():
    music_slider = Slider(WIDTH//2 - 100, HEIGHT//2 - 60, 200, 20, 0, 1, settings['music_volume'])
    sound_slider = Slider(WIDTH//2 - 100, HEIGHT//2, 200, 20, 0, 1, settings['sound_volume'])
    eazy_button = Button(WIDTH//2 - 100, HEIGHT//2 + 80,200,50,"Легкая",BLUE,PURPLE)
    normal_button = Button(WIDTH//2 - 100, HEIGHT//2 + 80,200,50,"Нормальная",BLUE,PURPLE)
    hard_button = Button(WIDTH//2 - 100,HEIGHT//2 + 80,200,50,"Сложная",BLUE,PURPLE)
    back_button = Button(WIDTH//2 - 100, HEIGHT//2 + 80, 200, 50, "Назад", BLUE, PURPLE)
    
    while True:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            music_changed = music_slider.update(mouse_pos, event)
            sound_changed = sound_slider.update(mouse_pos, event)
            
            if music_changed:
                settings['music_volume'] = music_slider.val
                pygame.mixer.music.set_volume(settings['music_volume'])
                
            if sound_changed:
                settings['sound_volume'] = sound_slider.val
                if sound_enabled:
                    shoot_sound.set_volume(settings['sound_volume'])
                    hit_sound.set_volume(settings['sound_volume'])
                    button_sound.set_volume(settings['sound_volume'])
            
            back_button.check_hover(mouse_pos)
            
            if back_button.is_clicked(mouse_pos, event):
                if sound_enabled:
                    button_sound.play()
                with open('settings.json', 'w') as f:
                    json.dump(settings, f, indent=4)  # indent для красивого форматирования
                return MENU
        
        # Отрисовка
        screen.fill(BLACK)
        

        
        # Заголовок
        title_font = pygame.font.Font(None, 72)
        title_text = title_font.render("Настройки", True, WHITE)
        screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, 100))
        
        # Текст слайдеров
        font = pygame.font.Font(None, 36)
        music_text = font.render("Громкость музыки:", True, WHITE)
        sound_text = font.render("Громкость звуков:", True, WHITE)
        
        screen.blit(music_text, (WIDTH//2 - 100, HEIGHT//2 - 100))
        screen.blit(sound_text, (WIDTH//2 - 100, HEIGHT//2 - 40))
        
        # Слайдеры
        music_slider.draw(screen)
        sound_slider.draw(screen)
        
        # Кнопка назад
        back_button.draw(screen)
        eazy_button.draw(screen)
        normal_button.draw(screen)
        hard_button.draw(screen)
        
        pygame.display.flip()
        clock.tick(FPS)

# Инициализация игры
def init_game():
    # Создаем фоновую поверхность
    background = pygame.Surface((WIDTH, HEIGHT))
    background.fill((10, 5, 20))
    for _ in range(200):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        size = random.randint(1, 3)
        pygame.draw.circle(background, (random.randint(50, 150), random.randint(50, 150), random.randint(50, 150)), (x, y), size)
    
    # Загружаем игровую музыку
    if sound_enabled:
        pygame.mixer.music.load(game_music)
        pygame.mixer.music.set_volume(settings['music_volume'])
        pygame.mixer.music.play(-1)
    
    return {
        'background': background,
        'player_x': WIDTH // 2,
        'player_y': HEIGHT - 50,
        'player_size': 30,
        'player_speed': 5,
        'player_health': 100,
        'max_player_health': 100,
        'boss_x': WIDTH // 2,
        'boss_y': 60,
        'boss_size': 100,
        'boss_speed_x': 3,
        'boss_speed_y': 2,
        'boss_health': 100,
        'max_boss_health': 100,
        'boss_phase': 1,
        'health_decay_rate': 1.1,
        'projectiles': [],
        'attack_timer': 0,
        'attack_interval': 45,
        'special_attack_timer': 0,
        'special_attack_interval': 300,
        'particles': [],
        'w_pressed': False,
        'a_pressed': False,
        's_pressed': False,
        'd_pressed': False
    }

# Функции игры
def draw_health_bar(x, y, width, height, current, max_, is_player=False):
    ratio = current/max_
    fill_width = int(width * ratio)
    display_current = int(round(current))
    display_max = int(round(max_))
    
    color = (100, 255, 100) if (ratio > 0.6 and is_player) or (ratio <= 0.6 and not is_player) else \
           (255, 255, 100) if ratio > 0.3 else (255, 100, 100)
    
    bg_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(screen, (50, 50, 50), bg_rect, border_radius=height//2)
    
    shadow_rect = pygame.Rect(x+2, y+2, fill_width, height-4)
    pygame.draw.rect(screen, (0, 0, 0, 100), shadow_rect, border_radius=(height-4)//2)
    
    fill_rect = pygame.Rect(x, y, fill_width, height)
    pygame.draw.rect(screen, color, fill_rect, border_radius=height//2)
    
    outline_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(screen, (200, 200, 200), outline_rect, 2, border_radius=height//2)
    
    font = pygame.font.Font(None, 20)
    text = f"{display_current}/{display_max}"
    text_surface = font.render(text, True, WHITE)
    text_rect = text_surface.get_rect(center=(x + width//2, y + height//2))
    
    text_shadow = font.render(text, True, (0, 0, 0))
    screen.blit(text_shadow, (text_rect.x+1, text_rect.y+1))
    screen.blit(text_surface, text_rect)

def draw_text(text, size, x, y, color=(255,255,255)):
    font = pygame.font.Font(None, size)
    text_surface = font.render(text, True, color)
    shadow = font.render(text, True, (0,0,0,150))
    for i in range(3):
        screen.blit(shadow, (x-text_surface.get_width()//2 + i, y-text_surface.get_height()//2 + i))
    screen.blit(text_surface, (x-text_surface.get_width()//2, y-text_surface.get_height()//2))

def draw_player(x, y, size):
    glow = pygame.Surface((size+30, size+30), pygame.SRCALPHA)
    pygame.draw.rect(glow, (0,255,0,80), (0,0,size+30,size+30), border_radius=10)
    screen.blit(glow, (x-15, y-15))
    
    shadow = pygame.Surface((size+10, size+10), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0,0,0,150), (5,5,size,size), border_radius=5)
    screen.blit(shadow, (x-5, y-5))
    
    player_surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.rect(player_surf, (0,255,0), (0,0,size,size), border_radius=5)
    pygame.draw.rect(player_surf, (0,200,0), (5,5,size-10,size-10), border_radius=3)
    screen.blit(player_surf, (x, y))

def draw_boss(x, y, size, phase, health_ratio):
    if health_ratio <= 0:
        return
    
    pulse = math.sin(pygame.time.get_ticks() / 300) * 5
    glow_size = int(size * 1.5 + pulse)
    glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
    
    glow_colors = [
        (255, 100, 100, 30),
        (255, 50, 50, 60),
        (255, 0, 0, 90)
    ]
    
    for i, (r, g, b, a) in enumerate(glow_colors):
        radius = int(glow_size//2 - i*10)
        if radius > 0:
            pygame.draw.circle(glow, (r, g, b, a), (glow_size//2, glow_size//2), radius)
    
    screen.blit(glow, (x - glow_size//2, y - glow_size//2))
    
    core_glow = pygame.Surface((size+20, size+20), pygame.SRCALPHA)
    pygame.draw.circle(core_glow, (255, 100, 100, 120), (size//2+10, size//2+10), size//2+5)
    screen.blit(core_glow, (x - size//2-10, y - size//2-10))
    
    shadow = pygame.Surface((size+15, size+15), pygame.SRCALPHA)
    pygame.draw.circle(shadow, (0, 0, 0, 100), (size//2+7, size//2+7), size//2+5)
    screen.blit(shadow, (x - size//2-7, y - size//2-7))
    
    boss_surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(boss_surf, (255, 50, 50), (size//2, size//2), size//2)
    
    if phase >= 2:
        pygame.draw.circle(boss_surf, (255, 180, 50), (size//2, size//2), size//3)
    if phase >= 3:
        pygame.draw.circle(boss_surf, (255, 255, 100), (size//2, size//2), size//4)
    
    if phase >= 2:
        hot_core = pygame.Surface((size//3, size//3), pygame.SRCALPHA)
        pygame.draw.circle(hot_core, (255, 255, 200, 150), (size//6, size//6), size//6)
        boss_surf.blit(hot_core, (size//3, size//3))
    
    screen.blit(boss_surf, (x - size//2, y - size//2))

def shoot(boss_x, boss_y, boss_size, phase, projectiles):
    if phase == 1:
        projectiles.append(Projectile(boss_x, boss_y+boss_size//2, angle=math.pi/2))
    elif phase == 2:
        for angle in [math.pi/2-0.3, math.pi/2, math.pi/2+0.3]:
            projectiles.append(Projectile(boss_x, boss_y+boss_size//2, angle=angle))
    else:
        for i in range(8):
            angle = i*(2*math.pi/8)
            projectiles.append(Projectile(boss_x, boss_y, angle=angle, speed=4))
    if sound_enabled:
        shoot_sound.play()

def special_attack(boss_x, boss_y, boss_size, phase, projectiles):
    if phase == 1:
        for i in range(12):
            angle = i*(2*math.pi/12) + (pygame.time.get_ticks()/500)
            projectiles.append(Projectile(boss_x, boss_y, angle=angle, speed=3, size=8, color=(255,165,0)))
    elif phase == 2:
        for i in range(16):
            angle = math.pi/2 + math.sin(i/2)*0.5
            offset = (i%4)*10 - 15
            projectiles.append(Projectile(boss_x+offset, boss_y+boss_size//2, angle=angle, speed=4, size=8, color=(255,0,255)))
    else:
        for i in range(4):
            angle = i*(math.pi/2)
            for j in range(1,4):
                projectiles.append(Projectile(boss_x, boss_y, angle=angle, speed=3+j, size=10-j*2, color=(0,255,255)))
    if sound_enabled:
        shoot_sound.play()

def create_explosion(x, y, color, particles, count=50, particle_type="special"):
    for _ in range(count):
        particles.append(Particle(x, y, color, particle_type))

def reset_game(game_data):
    game_data.update({
        'player_x': WIDTH // 2,
        'player_y': HEIGHT - 50,
        'player_health': 100,
        'boss_x': WIDTH // 2,
        'boss_y': 60,
        'boss_health': 100,
        'boss_phase': 1,
        'projectiles': [],
        'particles': [],
        'attack_timer': 0,
        'special_attack_timer': 0,
        'w_pressed': False,
        'a_pressed': False,
        's_pressed': False,
        'd_pressed': False
    })
    if sound_enabled:
        pygame.mixer.music.load(game_music)
        pygame.mixer.music.set_volume(settings['music_volume'])
        pygame.mixer.music.play(-1)

# Основной игровой цикл
def run_game(game_data):
    game_state = GAME_RUNNING
    
    while True:
        dt = clock.tick(FPS)/1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if game_state == GAME_RUNNING:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_w: game_data['w_pressed'] = True
                    elif event.key == pygame.K_a: game_data['a_pressed'] = True
                    elif event.key == pygame.K_s: game_data['s_pressed'] = True
                    elif event.key == pygame.K_d: game_data['d_pressed'] = True
                    elif event.key == pygame.K_SPACE:
                        dash_x = 20 * (game_data['d_pressed'] - game_data['a_pressed'])
                        dash_y = 20 * (game_data['s_pressed'] - game_data['w_pressed'])
                        if dash_x == 0 and dash_y == 0:
                            dash_y = -20
                        game_data['player_x'] += dash_x
                        game_data['player_y'] += dash_y
                        create_explosion(
                            game_data['player_x'] + game_data['player_size']//2,
                            game_data['player_y'] + game_data['player_size']//2,
                            (0, 255, 255),
                            game_data['particles'],
                            count=20
                        )
                    elif event.key == pygame.K_ESCAPE:
                        return MENU
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_w: game_data['w_pressed'] = False
                    elif event.key == pygame.K_a: game_data['a_pressed'] = False
                    elif event.key == pygame.K_s: game_data['s_pressed'] = False
                    elif event.key == pygame.K_d: game_data['d_pressed'] = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and (game_state == GAME_OVER or game_state == GAME_WIN):
                    reset_game(game_data)
                    game_state = GAME_RUNNING
                elif event.key == pygame.K_ESCAPE:
                    return MENU
        
        if game_state == GAME_RUNNING:
            # Движение игрока
            move_x = (game_data['d_pressed'] - game_data['a_pressed']) * game_data['player_speed']
            move_y = (game_data['s_pressed'] - game_data['w_pressed']) * game_data['player_speed']
            
            if move_x != 0 and move_y != 0:
                move_x *= 0.7071
                move_y *= 0.7071
            
            game_data['player_x'] += move_x
            game_data['player_y'] += move_y
            
            # Границы игрока
            game_data['player_x'] = max(0, min(WIDTH-game_data['player_size'], game_data['player_x']))
            game_data['player_y'] = max(0, min(HEIGHT-game_data['player_size'], game_data['player_y']))
            
            # Движение босса
            game_data['boss_x'] += game_data['boss_speed_x']
            game_data['boss_y'] += game_data['boss_speed_y']
            
            # Отражение от границ
            if game_data['boss_x'] > WIDTH-game_data['boss_size']//2 or game_data['boss_x'] < game_data['boss_size']//2:
                game_data['boss_speed_x'] *= -1
            if game_data['boss_y'] > HEIGHT//3 or game_data['boss_y'] < game_data['boss_size']//2:
                game_data['boss_speed_y'] *= -1
            
            # Обновление здоровья босса
            game_data['boss_health'] -= game_data['health_decay_rate'] * dt
            if game_data['boss_health'] <= 0:
                game_data['boss_health'] = 0
                game_state = GAME_WIN
                create_explosion(
                    game_data['boss_x'],
                    game_data['boss_y'],
                    (0, 255, 0),
                    game_data['particles'],
                    count=100
                )
            
            # Фазы босса
            if game_data['boss_health'] < game_data['max_boss_health']*0.66:
                game_data['boss_phase'] = 2
            if game_data['boss_health'] < game_data['max_boss_health']*0.33:
                game_data['boss_phase'] = 3
            
            # Атаки босса
            game_data['attack_timer'] += 1
            if game_data['attack_timer'] >= game_data['attack_interval']:
                game_data['attack_timer'] = 0
                shoot(
                    game_data['boss_x'],
                    game_data['boss_y'],
                    game_data['boss_size'],
                    game_data['boss_phase'],
                    game_data['projectiles']
                )
            
            game_data['special_attack_timer'] += 1
            if game_data['special_attack_timer'] >= game_data['special_attack_interval']:
                game_data['special_attack_timer'] = 0
                special_attack(
                    game_data['boss_x'],
                    game_data['boss_y'],
                    game_data['boss_size'],
                    game_data['boss_phase'],
                    game_data['projectiles']
                )
            
            # Обновление пуль
            game_data['projectiles'][:] = [p for p in game_data['projectiles'] if 0 <= p.x <= WIDTH and 0 <= p.y <= HEIGHT]
            for p in game_data['projectiles']:
                p.update()
                
                # Столкновение с игроком
                if (abs(p.x - (game_data['player_x']+game_data['player_size']//2)) < game_data['player_size']//2 + p.size//2 and 
                   abs(p.y - (game_data['player_y']+game_data['player_size']//2)) < game_data['player_size']//2 + p.size//2):
                    game_data['player_health'] -= 10
                    if sound_enabled:
                        hit_sound.play()
                    game_data['projectiles'].remove(p)
                    
                    create_explosion(
                        game_data['player_x'] + game_data['player_size']//2,
                        game_data['player_y'] + game_data['player_size']//2,
                        (255, 0, 0),
                        game_data['particles'],
                        count=15
                    )
                    
                    if game_data['player_health'] <= 0:
                        game_data['player_health'] = 0
                        game_state = GAME_OVER
            
            # Обновление частиц
            game_data['particles'][:] = [p for p in game_data['particles'] if p.life > 0]
            for p in game_data['particles']:
                p.update()
        
        # Отрисовка
        screen.blit(game_data['background'], (0, 0))
        
        # Частицы
        for p in game_data['particles']:
            p.draw()
        
        if game_state == GAME_RUNNING:
            # Здоровье
            draw_health_bar(50, HEIGHT-40, 200, 20, game_data['player_health'], game_data['max_player_health'], True)
            draw_health_bar(WIDTH//2-150, 20, 300, 25, game_data['boss_health'], game_data['max_boss_health'])
            
            # Игрок
            draw_player(game_data['player_x'], game_data['player_y'], game_data['player_size'])
            
            # Босс
            draw_boss(
                game_data['boss_x'],
                game_data['boss_y'],
                game_data['boss_size'],
                game_data['boss_phase'],
                game_data['boss_health'] / game_data['max_boss_health']
            )
            
            # Пули
            for p in game_data['projectiles']:
                p.draw()
        
        elif game_state == GAME_OVER:
            draw_text("GAME OVER", 72, WIDTH//2, HEIGHT//2, (255,50,50))
            draw_text("Press R to restart", 36, WIDTH//2, HEIGHT//2+60, (200,200,200))
            draw_text("ESC to menu", 36, WIDTH//2, HEIGHT//2+100, (200,200,200))
        
        elif game_state == GAME_WIN:
            draw_text("VICTORY!", 72, WIDTH//2, HEIGHT//2, (50,255,50))
            draw_text("Press R to restart", 36, WIDTH//2, HEIGHT//2+60, (200,200,200))
            draw_text("ESC to menu", 36, WIDTH//2, HEIGHT//2+100, (200,200,200))
        
        pygame.display.flip()

# Функции завершения игры
def game_over():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return GAME_RUNNING
                elif event.key == pygame.K_ESCAPE:
                    return MENU
        
        clock.tick(FPS)

def game_win():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return GAME_RUNNING
                elif event.key == pygame.K_ESCAPE:
                    return MENU
        
        clock.tick(FPS)

# Основной цикл приложения
def main():
    current_state = MENU
    game_data = None
    
    while True:
        if current_state == MENU:
            current_state = main_menu()
            if current_state == GAME_RUNNING:
                game_data = init_game()
        elif current_state == SETTINGS:
            current_state = settings_menu()
        elif current_state == GAME_RUNNING:
            current_state = run_game(game_data)
        elif current_state == GAME_OVER:
            current_state = game_over()
        elif current_state == GAME_WIN:
            current_state = game_win()
        else:
            break

if __name__ == "__main__":
    main()
    pygame.quit()
    sys.exit()
