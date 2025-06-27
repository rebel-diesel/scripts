import pygame as pg
import random
import sys
import os

class MatrixLetters:
    def __init__(self, app):
        self.app = app
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        font_path = os.path.join(base_path, 'MS_Mincho.ttf')
        self.letters = [chr(int('0x30a0', 16) + i) for i in range(1, 95)]
        self.font_size = 20
        self.font = pg.font.Font(font_path, self.font_size)
        self.font.set_bold(False)
        self.columns = app.WIDTH // self.font_size
        self.drops = [1 for i in range(0, self.columns)]

    def draw(self):
        for i in range(0, len(self.drops)):
            char = random.choice(self.letters)
            char_render = self.font.render(char, False, (28, 161, 82))
            pos = i * self.font_size, (self.drops[i] - 1) * self.font_size
            self.app.surface.blit(char_render, pos)
            if self.drops[i] * self.font_size > app.HEIGHT and random.uniform(0,1) > 0.975:
                self.drops[i] = 0
            self.drops[i] = self.drops[i] + 1

    def run(self):
        self.draw()


class MatrixApp:
    def __init__(self): # инициализация приложения
        pg.init()
        self.RES = self.WIDTH, self.HEIGHT = 3440, 1440

        self.screen = pg.display.set_mode((0, 0), pg.FULLSCREEN)
        # self.screen = pg.display.set_mode(self.RES) # отображаемый экран
        self.surface = pg.Surface(self.RES, pg.SRCALPHA) # поверхность отрисовки
        self.clock = pg.time.Clock() # для отслеживания времени
        self.matrixLetters = MatrixLetters(self) # экземпляр класса наших букв

    def draw(self): # закраска раб. поверхности и нанесем на гл. экран
        self.surface.fill((0,0,0,10))
        self.matrixLetters.run()
        self.screen.blit(self.surface, (0,0))

    def run(self): # главн. цикл программы
        running = True
        while running:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        running = False  # Set running to False to end the while loop.
            self.draw() # отрисовка экрана
            pg.display.flip() # обновление поверхности
            self.clock.tick(25) # установка кадров

if __name__ == '__main__':
    app = MatrixApp()
    app.run()
