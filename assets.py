# assets.py
import pygame

# Dimensões
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Cores
BLACK = (0, 0, 0)
DARK_GRAY = (20, 20, 20)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
YELLOW = (220, 220, 40)
BLUE = (40, 120, 255)
GREEN = (40, 220, 80)
RED = (220, 40, 60)

# Fonte
FONT_TITLE = "Arial"
FONT_REGULAR = "Arial"

# Sons (usaremos sons sintetizados via pygame.mixer)
SOUND_CLICK = "click.wav"  # vamos gerar um arquivo de clique simples se necessário

# Configuração de ecolocalização
SONAR_PING_COOLDOWN = 600  # ms entre pings sonar
SONAR_RADIUS = 180         # alcance visual do sonar em pixels
SONAR_DECAY = 0.75         # fator de atenuação do eco

# Itens
ITEM_KEY = "key"
ITEM_FLASHLIGHT = "flashlight"
ITEM_KEY_COLOR = YELLOW
ITEM_FLASHLIGHT_COLOR = BLUE

# Nível
MAZE_ROWS = 11
MAZE_COLS = 17
CELL_SIZE = 50
MAZE_MARGIN = 40

# Jogador
PLAYER_FOV = 90            # graus
PLAYER_VIEW_DEPTH = 300    # pixels
