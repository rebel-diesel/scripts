import pygame as pg
import random
import sys
import os
import ctypes

# ===================== Класс для управления символами матрицы =====================
class MatrixLetters:
    def __init__(self, app):
        self.app = app
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        font_path = os.path.join(base_path, 'MS_Mincho.ttf')

        # Японские символы катаканы
        self.letters = [chr(int('0x30a0', 16) + i) for i in range(1, 95)]
        self.font_size = 20
        self.font = pg.font.Font(font_path, self.font_size)
        self.font.set_bold(False)

        # Количество столбцов и строк, чтобы покрыть экран полностью
        self.columns = (app.WIDTH + self.font_size - 1) // self.font_size
        self.rows = (app.HEIGHT + self.font_size - 1) // self.font_size

        # Начальные позиции "падений" для каждого столбца (начинаем выше экрана)
        self.drops = [-random.randint(5, 25) for _ in range(self.columns)]

        # Предыдущие целочисленные позиции, чтобы отслеживать смену строки (стартуем с -1)
        self.prev_drops = [-1 for _ in range(self.columns)]

        # Индивидуальная скорость для каждого столбца от 0.2x до 1x базовой (1.5)
        base_speed = 1
        self.speeds = [base_speed * random.uniform(0.2, 1.0) for _ in range(self.columns)]

    def draw(self):
        # Отрисовка символов матрицы только при переходе на следующую строку
        for i in range(len(self.drops)):
            current_row = int(self.drops[i])

            if current_row >= 0 and current_row != self.prev_drops[i]:
                char = random.choice(self.letters)
                char_render = self.font.render(char, False, (28, 161, 82))
                x = int(i * self.font_size)
                y = int(current_row * self.font_size)
                if y < self.app.HEIGHT:
                    self.app.surface.blit(char_render, (x, y))
                self.prev_drops[i] = current_row

            # Сброс столбца с небольшой вероятностью
            if self.drops[i] * self.font_size > self.app.HEIGHT and random.random() > 0.975:
                self.drops[i] = -random.randint(5, 25)
                self.prev_drops[i] = -1
            else:
                self.drops[i] += self.speeds[i]

    def run(self):
        self.draw()


# ===================== Класс основного приложения =====================
class MatrixApp:
    def __init__(self):
        pg.init()
        self.RES = self.get_physical_resolution()
        self.WIDTH, self.HEIGHT = self.RES

        # Полноэкранный режим с альфа-каналом
        self.screen = pg.display.set_mode(self.RES, pg.FULLSCREEN)
        self.surface = pg.Surface(self.RES, pg.SRCALPHA)
        self.clock = pg.time.Clock()
        self.matrixLetters = MatrixLetters(self)
        self.font = pg.font.SysFont('consolas', 18)

    def get_physical_resolution(self):
        # Получение физического разрешения экрана с учётом DPI
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

    def draw_debug_info(self):
        # Вывод текущего разрешения в левом верхнем углу
        # res_text = f"{self.WIDTH}x{self.HEIGHT}"
        # debug_surface = self.font.render(res_text, True, (0, 255, 0))
        # self.screen.blit(debug_surface, (10, 10))
        pass

    def draw_border(self):
        # Отрисовка зелёной рамки по границе экрана
        # pg.draw.rect(self.screen, (0, 255, 0), self.screen.get_rect(), 1)
        pass

    def draw(self):
        # Основной рендеринг: обновление матрицы, наложение поверхностей, отрисовка рамки и отладочной информации
        self.surface.fill((0, 0, 0, 10))
        self.matrixLetters.run()
        self.screen.blit(self.surface, (0, 0))
        self.draw_border()
        self.draw_debug_info()

    def run(self):
        # Главный цикл приложения
        running = True
        while running:
            for event in pg.event.get():
                if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                    running = False
            self.draw()
            pg.display.flip()
            self.clock.tick(25)


# ===================== Точка входа =====================
if __name__ == '__main__':
    app = MatrixApp()
    app.run()
