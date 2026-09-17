# game.py
import pygame, math, random
from assets import *
from maze_generator import Maze

class GameState:
    INTRO = "intro"        # sala inicial antes do labirinto
    MAZE = "maze"          # dentro do labirinto
    WIN = "win"            # saiu do labirinto

class Player:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle  # em graus
        self.speed = 3
        self.rotate_speed = 3
        self.has_key = False
        self.has_flashlight = False
        self.sonar_cooldown = 0

    def update(self, keys, maze, dt):
        # Movimento WASD / setas
        move = 0
        strafe = 0
        rotate = 0

        # Controles
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            move = 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            move = -1
        if keys[pygame.K_a]:
            strafe = -1
        if keys[pygame.K_d]:
            strafe = 1
        if keys[pygame.K_LEFT]:
            rotate -= self.rotate_speed
        if keys[pygame.K_RIGHT]:
            rotate += self.rotate_speed

        # Movimentação (frente/trás)
        if move != 0:
            angle_rad = math.radians(self.angle)
            dx = move * self.speed * math.cos(angle_rad)
            dy = move * self.speed * math.sin(angle_rad)
            nx = self.x + dx
            ny = self.y + dy
            # Checar colisão
            if not maze.is_wall(*maze.world_to_grid(nx, ny)):
                self.x, self.y = nx, ny

        # Strafe (lateral) — menos eficiente
        if strafe != 0:
            angle_rad = math.radians(self.angle + 90)
            dx = strafe * self.speed * 0.6 * math.cos(angle_rad)
            dy = strafe * self.speed * 0.6 * math.sin(angle_rad)
            nx = self.x + dx
            ny = self.y + dy
            if not maze.is_wall(*maze.world_to_grid(nx, ny)):
                self.x, self.y = nx, ny

        # Rotação
        if rotate != 0:
            self.angle += rotate

        # Normalizar ângulo
        self.angle %= 360

    def world_to_grid(self, wx, wy, cell_size=CELL_SIZE, margin_x=MAZE_MARGIN, margin_y=MAZE_MARGIN):
        # Converte coordenadas do mundo para índice de célula
        gx = int((wx - margin_x) // cell_size)
        gy = int((wy - margin_y) // cell_size)
        return gx, gy

    def can_use_sonar(self):
        # Retorna se pode emitir sonar (cooldown)
        return self.sonar_cooldown <= 0

    def ping_sonar(self, maze, screen, clock):
        # Emite um "ping" sonoro e desenha o eco na tela
        # (efeito visual + som sintetizado)
        self.sonar_cooldown = SONAR_PING_COOLDOWN
        # Som sintetizado simples
        try:
            # Gerar som curto via array
            freq = 6600
            duration = 0.12
            sample_rate = 22050
            samples = int(duration * sample_rate)
            wave = []
            for i in range(samples):
                t = i / sample_rate
                sample = 0.3 * math.sin(2 * math.pi * freq * t) * math.exp(-3.5 * t)
                wave.append(int(sample * 32767))
            sound = pygame.sndarray.make_sound(pygame.array.array(wave, dtype='int16'))
            sound.play()
        except Exception:
            pass

        # Ecos: raios em arco do FOV
        fov = PLAYER_FOV
        depth = PLAYER_VIEW_DEPTH
        rays = 32
        echoes = []
        for i in range(rays):
            angle_offset = (fov / 2) - (i * fov / (rays - 1))
            ray_angle = math.radians(self.angle + angle_offset)
            for d in range(1, depth+1, 4):
                wx = self.x + d * math.cos(ray_angle)
                wy = self.y + d * math.sin(ray_angle)
                gx, gy = self.world_to_grid(wx, wy)
                if maze.is_wall(gx, gy):
                    # Quanto mais longe, mais fraco
                    intensity = max(0, 1 - d/depth)
                    echoes.append((wx, wy, intensity))
                    break
        # Desenhar ecos como círculos desbotados
        for wx, wy, intensity in echoes:
            color = tuple(int(DARK_GRAY[i] * (0.5 + 0.5*intensity)) for i in range(3))
            px, py = self.world_to_screen(wx, wy, screen)
            pygame.draw.circle(screen, color, (int(px), int(py)), 6, 1)

    def world_to_screen(self, wx, wy, screen):
        # Primeira pessoa: projeta ponto para tela 2D (raycasting simples)
        # Tela virtual centrada
        cx, cy = SCREEN_WIDTH//2, SCREEN_HEIGHT//2
        # Offset do jogador para centro do labirinto
        margin_x, margin_y = MAZE_MARGIN, MAZE_MARGIN
        # Posição relativa
        rel_x = wx - self.x
        rel_y = wy - self.y
        # Rotacionar para o sistema de referência do jogador
        angle_rad = math.radians(self.angle)
        rx = rel_x * math.cos(-angle_rad) - rel_y * math.sin(-angle_rad)
        ry = rel_x * math.sin(-angle_rad) + rel_y * math.cos(-angle_rad)
        # Projeção perspectiva simples
        if rx <= 0.1:
            rx = 0.1  # evitar divisão por zero
        scale = 320 / rx
        sy = scale
        px = cx + int(ry * scale * 0.7)
        py = cy + int((rx - 80) * 0.6)  # ajuste vertical
        return px, py

def draw_text(screen, text, size, color, center):
    font = pygame.font.SysFont(FONT_REGULAR, size, True)
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=center)
    screen.blit(surf, rect)

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.state = GameState.INTRO
        self.maze = None
        self.player = None
        self.start_time = None
        self.elapsed = 0
        self.font_big = pygame.font.SysFont(FONT_TITLE, 72, True)
        self.font_norm = pygame.font.SysFont(FONT_REGULAR, 32, True)
        self.font_small = pygame.font.SysFont(FONT_REGULAR, 22, True)
        self.sonar_enabled = True

    def new_game(self):
        # Gera labirinto
        self.maze = Maze(MAZE_ROWS, MAZE_COLS)
        self.maze.generate()

        # Posição inicial do jogador (entrada)
        sx, sy = self.maze.start
        margin_x, margin_y = MAZE_MARGIN, MAZE_MARGIN
        cell_size = CELL_SIZE
        self.player = Player(
            x=margin_x + sx * cell_size + cell_size//2,
            y=margin_y + sy * cell_size + cell_size//2,
            angle=0
        )
        self.start_time = pygame.time.get_ticks()
        self.elapsed = 0
        self.player.has_key = False
        self.player.has_flashlight = False
        self.player.sonar_cooldown = 0

    def run_intro(self):
        # Sala escura com única porta
        self.screen.fill(BLACK)
        draw_text(self.screen, "Você está em uma sala isolada.", 32, GRAY, (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 60))
        draw_text(self.screen, "A única porta à sua frente leva ao desconhecido...", 28, GRAY, (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 15))
        draw_text(self.screen, "Pressione ESPAÇO para entrar no labirinto.", 24, YELLOW, (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 40))

        # Desenhar porta (luz fraca)
        door_x = SCREEN_WIDTH//2 - 60
        door_y = SCREEN_HEIGHT//2 + 100
        pygame.draw.rect(self.screen, GRAY, (door_x, door_y, 120, 100), border_radius=8)
        pygame.draw.rect(self.screen, WHITE, (door_x+15, door_y+10, 90, 30), border_radius=6)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.state = GameState.MAZE
                self.new_game()
                return True
        return True

    def run_maze(self):
        screen = self.screen
        maze = self.maze
        player = self.player
        dt = self.clock.get_time()
        keys = pygame.key.get_pressed()

        # Atualizar cooldown do sonar
        if player.sonar_cooldown > 0:
            player.sonar_cooldown -= dt

        # Controles
        player.update(keys, maze, dt)

        # Ecolocalização: tecla E ou barra de espaço
        if (keys[pygame.K_e] or keys[pygame.K_SPACE]) and player.can_use_sonar():
            player.ping_sonar(maze, screen, self.clock)

        # Verificar colisão com itens
        px, py = player.world_to_grid(player.x, player.y)
        # Coletar chave
        if not player.has_key and maze.key_pos and (px, py) == maze.key_pos:
            player.has_key = True
            # remover item
            maze.item_cells = [i for i in maze.item_cells if i[0] != 'key']
        # Coletar lanterna
        if not player.has_flashlight and maze.flashlight_pos and (px, py) == maze.flashlight_pos:
            player.has_flashlight = True
            maze.item_cells = [i for i in maze.item_cells if i[0] != 'flashlight']

        # Verificar saída (precisa da chave)
        ex, ey = maze.exit
        if (px, py) == (ex, ey) and player.has_key:
            self.state = GameState.WIN
            self.elapsed = (pygame.time.get_ticks() - self.start_time) // 1000
            return True

        # --- Renderização em primeira pessoa ---
        screen.fill(BLACK)

        # Renderizar "visão" do labirinto (raycasting simples)
        self.render_first_person(screen, maze, player)

        # Renderizar HUD (sonar, itens)
        self.render_hud(screen, player)

        # Mensagem se tentar abrir porta sem chave
        if (px, py) == (ex, ey) and not player.has_key:
            draw_text(screen, "Você precisa de uma chave para abrir esta porta.", 24, RED, (SCREEN_WIDTH//2, 30))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

        return True

    def render_first_person(self, screen, maze, player):
        # Raycasting simples para renderizar paredes em perspectiva
        fov = PLAYER_FOV
        depth = PLAYER_VIEW_DEPTH
        num_rays = SCREEN_WIDTH // 2  # 2 pixels por raio
        wall_height = 220

        # Se tem lanterna, aumenta o alcance e iluminação
        flashlight_range = 160 if player.has_flashlight else 90
        flashlight_intensity = 0.95 if player.has_flashlight else 0.35

        for col in range(num_rays):
            angle_offset = (fov / 2) - (col * fov / (num_rays - 1))
            ray_angle = math.radians(player.angle + angle_offset)
            hit_dist = None
            # Lançar raio
            for d in range(1, depth+1, 2):
                wx = player.x + d * math.cos(ray_angle)
                wy = player.y + d * math.sin(ray_angle)
                gx, gy = maze.world_to_grid(wx, wy)
                if maze.is_wall(gx, gy):
                    hit_dist = d
                    break
            # Desenhar coluna
            if hit_dist is not None:
                # Perspectiva: coluna mais alta quando mais perto
                scale = wall_height / (hit_dist + 0.01) * 140
                color_intensity = min(1.0, flashlight_range / (hit_dist+0.01)) * flashlight_intensity
                # Cor da parede (mais escura longe)
                base_color = DARK_GRAY if hit_dist < 120 else (50,50,50)
                color = tuple(int(base_color[i] * (0.35 + 0.65*color_intensity)) for i in range(3))
                x = col * 2
                y_top = int(SCREEN_HEIGHT//2 - scale//2)
                y_bot = int(SCREEN_HEIGHT//2 + scale//2)
                pygame.draw.rect(screen, color, (x, y_top, 2, y_bot-y_top))
                # Efeito de névoa/preto nas bordas
                if not player.has_flashlight or hit_dist > flashlight_range:
                    fade = max(0, min(1, (hit_dist - flashlight_range)/60))
                    overlay = pygame.Surface((2, y_bot-y_top), pygame.SRCALPHA)
                    overlay.fill((0,0,0, int(180*fade)))
                    screen.blit(overlay, (x, y_top))

        # Renderizar saída (luz branca na parede se visível)
        # Posição da saída
        ex, ey = maze.exit
        exit_cx, exit_cy = maze.cell_center(ex, ey, CELL_SIZE, MAZE_MARGIN, MAZE_MARGIN)
        # Verificar se está no FOV e sem parede no caminho
        dx = exit_cx - player.x
        dy = exit_cy - player.y
        dist = math.hypot(dx, dy)
        if dist < depth:
            angle_to_exit = math.degrees(math.atan2(dy, dx)) % 360
            rel_angle = (angle_to_exit - player.angle) % 360
            if rel_angle > 180:
                rel_angle -= 360
            if abs(rel_angle) < fov/2:
                # Traçar linha até saída para ver se há parede no meio
                blocked = False
                for d in range(1, int(dist), 6):
                    wx = player.x + dx * (d/dist)
                    wy = player.y + dy * (d/dist)
                    gx, gy = maze.world_to_grid(wx, wy)
                    if maze.is_wall(gx, gy):
                        blocked = True
                        break
                if not blocked:
                    # Projeção na tela
                    px, py = player.world_to_screen(exit_cx, exit_cy, screen)
                    # Só se estiver na tela
                    if 0 <= px <= SCREEN_WIDTH:
                        # Luz branca pulsante
                        radius = max(14, 36 * (0.8 + 0.2*math.sin(pygame.time.get_ticks()/250)))
                        light = pygame.Surface((int(radius*2), int(radius*2)), pygame.SRCALPHA)
                        pygame.draw.circle(light, (255,255,255,80), (int(radius), int(radius)), int(radius))
                        screen.blit(light, (int(px-radius), int(py-radius)))
                        # Texto "Saída"
                        draw_text(screen, "Saída", 22, WHITE, (int(px), int(py-40)))

        # Renderizar itens no campo de visão (se próximos)
        for item_type, (ix, iy) in maze.item_cells:
            item_cx, item_cy = maze.cell_center(ix, iy, CELL_SIZE, MAZE_MARGIN, MAZE_MARGIN)
            dx = item_cx - player.x
            dy = item_cy - player.y
            dist = math.hypot(dx, dy)
            if dist < (flashlight_range+40):
                angle_to = math.degrees(math.atan2(dy, dx)) % 360
                rel_angle = (angle_to - player.angle) % 360
                if rel_angle > 180:
                    rel_angle -= 360
                if abs(rel_angle) < fov/2:
                    px, py = player.world_to_screen(item_cx, item_cy, screen)
                    if 0 <= px <= SCREEN_WIDTH and 0 <= py <= SCREEN_HEIGHT:
                        color = YELLOW if item_type == 'key' else BLUE
                        pygame.draw.circle(screen, color, (int(px), int(py)), 10)
                        label = "Chave" if item_type == 'key' else "Lanterna"
                        draw_text(screen, label, 16, color, (int(px), int(py)+18))

    def render_hud(self, screen, player):
        # Barra de sonar (cooldown)
        bar_w = 220
        bar_h = 18
        bar_x = 20
        bar_y = SCREEN_HEIGHT - 40
        pygame.draw.rect(screen, GRAY, (bar_x, bar_y, bar_w, bar_h), border_radius=6)
        fill = max(0, 1 - player.sonar_cooldown/SONAR_PING_COOLDOWN)
        pygame.draw.rect(screen, YELLOW, (bar_x, bar_y, int(bar_w*fill), bar_h), border_radius=6)
        draw_text(screen, "Sonar", 18, WHITE, (bar_x + bar_w//2, bar_y - 18))

        # Itens coletados
        pad = 10
        y = 16
        if player.has_key:
            pygame.draw.circle(screen, YELLOW, (50, y+10), 10)
            draw_text(screen, "Chave", 22, YELLOW, (66, y+12))
            y += pad + 22
        if player.has_flashlight:
            # desenhar "lanterna" (retângulo)
            pygame.draw.rect(screen, BLUE, (50, y+4, 18, 14), border_radius=3)
            draw_text(screen, "Lanterna", 22, BLUE, (74, y+12))
            y += pad + 22

    def run_win(self):
        screen = self.screen
        screen.fill(BLACK)
        draw_text(screen, "Você escapou!", 64, GREEN, (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 40))
        draw_text(screen, f"Tempo: {self.elapsed}s", 32, WHITE, (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 10))
        draw_text(screen, "Pressione R para reiniciar ou ESC para sair.", 22, GRAY, (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.state = GameState.INTRO
                    return True
                if event.key == pygame.K_ESCAPE:
                    return False
        return True
