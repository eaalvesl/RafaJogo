# main.py
import pygame
import sys
from assets import *
from game import Game, GameState

def draw_initial_screen(screen):
    screen.fill(BLACK)
    # Sombra para o título
    font = pygame.font.SysFont(FONT_TITLE, 100, True)
    title = font.render("The Silent", True, (60,60,60))
    rect = title.get_rect(center=(SCREEN_WIDTH//2 + 4, SCREEN_HEIGHT//2 + 4))
    screen.blit(title, rect)
    # Título principal
    title2 = font.render("The Silent", True, WHITE)
    rect2 = title2.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
    screen.blit(title2, rect2)

    # Botão "Jogar"
    btn_w, btn_h = 220, 60
    btn_x = (SCREEN_WIDTH - btn_w)//2
    btn_y = SCREEN_HEIGHT//2 + 100
    mouse = pygame.mouse.get_pos()
    clicked = pygame.mouse.get_pressed()[0]
    hover = btn_x <= mouse[0] <= btn_x+btn_w and btn_y <= mouse[1] <= btn_y+btn_h

    color_btn = tuple(min(255, c+40) for c in YELLOW) if hover else YELLOW
    pygame.draw.rect(screen, color_btn, (btn_x, btn_y, btn_w, btn_h), border_radius=16)
    pygame.draw.rect(screen, WHITE, (btn_x, btn_y, btn_w, btn_h), 3, border_radius=16)
    font_btn = pygame.font.SysFont(FONT_REGULAR, 36, True)
    txt = font_btn.render("Jogar", True, BLACK)
    rect_btn = txt.get_rect(center=(btn_x+btn_w//2, btn_y+btn_h//2))
    screen.blit(txt, rect_btn)

    return hover and clicked

def main():
    pygame.init()
    pygame.display.set_caption("The Silent")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    # Inicializar mixer para sons
    try:
        pygame.mixer.init(frequency=22050, size=-16, channels=1)
    except Exception:
        pass

    # Estado do jogo
    game = Game(screen)
    in_initial_screen = True

    running = True
    while running:
        if in_initial_screen:
            # Tela inicial
            start_pressed = draw_initial_screen(screen)
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if start_pressed:
                        in_initial_screen = False
                        game.state = GameState.INTRO
                elif event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    in_initial_screen = False
                    game.state = GameState.INTRO
            clock.tick(40)
            continue

        # --- Lógica do jogo ---
        if game.state == GameState.INTRO:
            running = game.run_intro()
        elif game.state == GameState.MAZE:
            running = game.run_maze()
        elif game.state == GameState.WIN:
            running = game.run_win()

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
