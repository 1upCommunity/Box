import pygame
import opensimplex
import random

class LoadingScreen:
    def __init__(self, window, gstate_setter):
        self.window = window
        self.box_icon = pygame.image.load("assets/Box.png")
        self.transparency = 255
        self.transparency_step = 5
        self.transparency_max = 255
        self.transparency_min = 100
        self.opensimplex = opensimplex.OpenSimplex(seed=random.randint(0, 1000000))
        self.font = pygame.font.Font("assets/press_start.ttf", 20)
        self.current_flashing_text = 0
        self.flashing_text = ['loading', '.loading.', '..loading..', '...loading...', '..loading..', '.loading.', 'loading']
        self.loading_text = self.font.render(self.flashing_text[self.current_flashing_text], True, (255, 255, 255))
        self.loading_text_rect = self.loading_text.get_rect()
        self.frame = 0
        self.gstate_setter = gstate_setter

    def update(self):
        self.transparency += self.transparency_step
        if self.transparency >= self.transparency_max:
            self.transparency_step = -5
        if self.transparency <= self.transparency_min:
            self.transparency_step = 5

        if self.frame % 10 == 0:
            self.current_flashing_text += 1
            if self.current_flashing_text >= len(self.flashing_text):
                self.current_flashing_text = 0

        self.loading_text = self.font.render(self.flashing_text[self.current_flashing_text], True, (255, 255, 255))
        self.loading_text_rect = self.loading_text.get_rect()

        self.frame += 1

    def draw(self):
        xnoise = self.opensimplex.noise2(self.transparency / self.transparency_step, -self.transparency)
        ynoise = self.opensimplex.noise2(-self.transparency / self.transparency_step, self.transparency)
        self.window.fill((0, 0, 0))
        self.box_icon.set_alpha(self.transparency)
        self.window.blit(self.box_icon, (self.window.get_width() / 2 - self.box_icon.get_width() / 2 + xnoise, self.window.get_height() / 2 - self.box_icon.get_height() / 2 + ynoise))
        self.loading_text_rect.center = (self.window.get_width() / 2, self.window.get_height() / 8 * 7)
        self.window.blit(self.loading_text, self.loading_text_rect)
        pygame.display.update()
        pygame.time.delay(100)

def load_screens(window, gstate_setter):
    screens = {}
    screens['LoadingScreen'] = LoadingScreen(window, gstate_setter)
    return screens
