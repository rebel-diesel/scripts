import pygame as pg
import random
import sys
import os
import ctypes

# ===================== Получение физического разрешения =====================
def get_physical_resolution():
    # Используется WinAPI для получения физического (не масштабированного) разрешения экрана
    user32 = ctypes.windll.user32
    user32.SetProcessDPIAware()
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

# ===================== Отрисовка символов матрицы =====================
def draw_matrix(surface, WIDTH, HEIGHT, font, letters, drops, prev_drops, speeds, font_size):
    # Отрисовка "падающих" символов матрицы по столбцам с индивидуальной скоростью
    for i in range(len(drops)):
        current_row = int(drops[i])
        if current_row >= 0 and current_row != prev_drops[i]:
            char = random.choice(letters)
            char_render = font.render(char, False, (28, 161, 82))
            x = int(i * font_size)
            y = int(current_row * font_size)
            if y < HEIGHT:
                surface.blit(char_render, (x, y))
            prev_drops[i] = current_row

        if drops[i] * font_size > HEIGHT and random.random() > 0.975:
            # Сброс падения с вероятностью
            drops[i] = -random.randint(5, 25)
            prev_drops[i] = -1
        else:
            drops[i] += speeds[i]

# ===================== Отрисовка отладочной информации =====================
def draw_debug_info(screen, WIDTH, HEIGHT, font):
    # Вывод текущего разрешения экрана в верхнем левом углу
    # res_text = f"{WIDTH}x{HEIGHT}"
    # debug_surface = font.render(res_text, True, (0, 255, 0))
    # screen.blit(debug_surface, (10, 10))
    pass

# ===================== Отрисовка рамки по краям экрана =====================
def draw_border(screen):
    # Отрисовка зелёной рамки по границе экрана
    # pg.draw.rect(screen, (0, 255, 0), screen.get_rect(), 1)
    pass
# ===================== Основной цикл отрисовки =====================
def run_matrix_txt():
    pg.init()

    # Получение реального разрешения экрана
    WIDTH, HEIGHT = get_physical_resolution()
    screen = pg.display.set_mode((WIDTH, HEIGHT), pg.FULLSCREEN)
    surface = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
    clock = pg.time.Clock()

    # Загрузка шрифта
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    font_path = os.path.join(base_path, 'input/MS_Mincho.ttf')
    font_size = 20
    font = pg.font.Font(font_path, font_size)
    font.set_bold(False)
    debug_font = pg.font.SysFont('consolas', 18)

    # Генерация символов катаканы (юникод-блок 0x30a0)
    letters = [chr(int('0x30a0', 16) + i) for i in range(1, 95)]

    # Вычисление количества столбцов и строк
    columns = (WIDTH + font_size - 1) // font_size
    rows = (HEIGHT + font_size - 1) // font_size

    # Начальные позиции падений для каждого столбца и скорости
    drops = [-random.randint(5, 25) for _ in range(columns)]
    prev_drops = [-1 for _ in range(columns)]
    base_speed = 1
    speeds = [base_speed * random.uniform(0.2, 1.0) for _ in range(columns)]

    # Главный цикл
    running = True
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                running = False

        surface.fill((0, 0, 0, 10))  # Полупрозрачное затухание следов
        draw_matrix(surface, WIDTH, HEIGHT, font, letters, drops, prev_drops, speeds, font_size)
        screen.blit(surface, (0, 0))
        draw_border(screen)
        draw_debug_info(screen, WIDTH, HEIGHT, debug_font)

        pg.display.flip()
        clock.tick(25)
