# maze_generator.py
import random

class Maze:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.maze = []
        self.start = None
        self.exit = None
        self.key_pos = None
        self.flashlight_pos = None
        self.item_cells = []

    def generate(self):
        # Algoritmo: DFS recursivo para gerar labirinto perfeito
        def carve(x, y, visited, maze):
            visited.add((x, y))
            dirs = [(0,2), (0,-2), (2,0), (-2,0)]
            random.shuffle(dirs)
            for dx, dy in dirs:
                nx, ny = x+dx, y+dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows and (nx, ny) not in visited:
                    # Remove parede entre (x,y)-(nx,ny)
                    maze[y + dy//2][x + dx//2] = 1
                    carve(nx, ny, visited, maze)

        # 0 = parede, 1 = caminho
        maze = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        # Início no centro de uma borda
        start_y = random.choice(range(1, self.rows, 2))
        start_x = 1
        maze[start_y][start_x] = 1
        self.start = (start_x, start_y)

        carve(start_x, start_y, set(), maze)

        # Saída: oposta ao início
        exit_x = self.cols - 2
        exit_y = random.choice(range(1, self.rows, 2))
        # Abrir caminho até saída
        maze[exit_y][exit_x] = 1
        # Garantir conexão entre início e fim (se não já conectados)
        # (Labirinto perfeito já garante conexão única)

        self.maze = maze
        self.exit = (exit_x, exit_y)

        # Colocar itens em caminhos livres, longe do início e da saída
        free = []
        for y in range(1, self.rows, 2):
            for x in range(1, self.cols, 2):
                if maze[y][x] == 1:
                    # Distância mínima do início e saída
                    d_start = abs(x - start_x) + abs(y - start_y)
                    d_exit = abs(x - exit_x) + abs(y - exit_y)
                    if d_start > 6 and d_exit > 6:
                        free.append((x, y))
        random.shuffle(free)
        self.key_pos = free.pop(0) if free else None
        self.flashlight_pos = free.pop(0) if free and len(free) > 0 else None

        self.item_cells = []
        if self.key_pos:
            self.item_cells.append(('key', self.key_pos))
        if self.flashlight_pos:
            self.item_cells.append(('flashlight', self.flashlight_pos))

    def is_wall(self, x, y):
        if 0 <= x < self.cols and 0 <= y < self.rows:
            return self.maze[y][x] == 0
        return True  # fora dos limites = parede

    def cell_center(self, x, y, cell_size, margin_x=0, margin_y=0):
        return (margin_x + x * cell_size + cell_size // 2,
                margin_y + y * cell_size + cell_size // 2)
