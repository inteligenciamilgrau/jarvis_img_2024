import pygame
import time
import random

description = "Jogar o jogo da cobrinha."
trigger = "O usuário pedir para jogar o jogo da cobrinha."
example = "{'type': 'snake_game', 'content': 'The response to the user'}"

def jogar():
    # Inicializa o Pygame
    pygame.init()

    # Cores
    white = (255, 255, 255)
    black = (0, 0, 0)
    red = (213, 50, 80)
    green = (0, 255, 0)
    blue = (50, 153, 213)

    # Tamanho da tela
    width = 600
    height = 400

    # Cria a tela
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption('Snake Game')

    # Variáveis da cobra
    snake_block = 10
    snake_speed = 15

    # Fonte do texto
    font_style = pygame.font.SysFont('bahnschrift', 25)
    score_font = pygame.font.SysFont('comicsansms', 35)

    # Função para mostrar a pontuação

    def your_score(score):
        value = score_font.render('Score: ' + str(score), True, white)
        screen.blit(value, [0, 0])

    # Função para a cobra

    def our_snake(snake_block, snake_list):
        for x in snake_list:
            pygame.draw.rect(screen, black, [x[0], x[1], snake_block, snake_block])

    # Função principal do jogo

    def gameLoop():
        game_over = False
        game_close = False

        x1 = width / 2
        y1 = height / 2

        x1_change = 0
        y1_change = 0

        snake_List = []
        Length_of_snake = 1

        foodx = round(random.randrange(0, width - snake_block) / 10.0) * 10.0
        foody = round(random.randrange(0, height - snake_block) / 10.0) * 10.0

        while not game_over:
            while game_close == True:
                screen.fill(blue)
                message = font_style.render('You Lost! Press C-Play Again or Q-Quit', True, red)
                screen.blit(message, [width / 6, height / 3])
                your_score(Length_of_snake - 1)
                pygame.display.update()

                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_q:
                            game_over = True
                            game_close = False
                        if event.key == pygame.K_c:
                            gameLoop()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_over = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        x1_change = -snake_block
                        y1_change = 0
                    elif event.key == pygame.K_RIGHT:
                        x1_change = snake_block
                        y1_change = 0
                    elif event.key == pygame.K_UP:
                        y1_change = -snake_block
                        x1_change = 0
                    elif event.key == pygame.K_DOWN:
                        y1_change = snake_block
                        x1_change = 0

            if x1 >= width or x1 < 0 or y1 >= height or y1 < 0:
                game_close = True

            x1 += x1_change
            y1 += y1_change
            screen.fill(blue)
            pygame.draw.rect(screen, green, [foodx, foody, snake_block, snake_block])
            snake_Head = []
            snake_Head.append(x1)
            snake_Head.append(y1)
            snake_List.append(snake_Head)
            if len(snake_List) > Length_of_snake:
                del snake_List[0]

            for x in snake_List[:-1]:
                if x == snake_Head:
                    game_close = True

            our_snake(snake_block, snake_List)
            your_score(Length_of_snake - 1)

            pygame.display.update()

            if x1 == foodx and y1 == foody:
                foodx = round(random.randrange(0, width - snake_block) / 10.0) * 10.0
                foody = round(random.randrange(0, height - snake_block) / 10.0) * 10.0
                Length_of_snake += 1

            clock.tick(snake_speed)

        pygame.quit()
        quit()

    # Clock
    clock = pygame.time.Clock()
    gameLoop()


# Executa o jogo
def execute(content):
    jogar()
    return "Jogada Excelente"
