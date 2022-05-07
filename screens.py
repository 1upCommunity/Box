import pygame
import opensimplex
import random
import logging
import os, sys
pygame.init()
logging.basicConfig(level=logging.ERROR)

from terrain import *

BUTTON_COLOR_NORMAL = (170, 170, 170)
BUTTON_COLOR_HOVER = (100, 100, 100)
BUTTON_COLOR_PRESSED = (50, 50, 50)
assets = {}

GSTATE = 'LoadingScreen'

pygame.mouse.set_cursor(*pygame.cursors.arrow)

def set_gstate(gstate):
    global GSTATE
    GSTATE = gstate

mouse_pos = (0, 0)
mouse_down = False

class button():
    def __init__(self, color, x, y, width, height, text=''):
        self.color = color
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.font = pygame.font.Font("assets/press_start.ttf", 20)
        self.callback = None

    def draw(self, win):
        pygame.draw.rect(win, self.color, (self.x,self.y,self.width,self.height),0)
    
        if self.text != '':
            text = self.font.render(self.text, 1, (255,255,255))
            win.blit(text, (self.x + (self.width/2 - text.get_width()/2), self.y + (self.height/2 - text.get_height()/2)))

    def is_over(self, pos):
        #Pos is the mouse position or a tuple of (x,y) coordinates
        if pos[0] > self.x and pos[0] < self.x + self.width:
            if pos[1] > self.y and pos[1] < self.y + self.height:
                pygame.mouse.set_cursor(*pygame.cursors.tri_left)
                self.color = BUTTON_COLOR_HOVER
                if mouse_down:
                    self.color = BUTTON_COLOR_PRESSED
                    if self.callback != None:
                        self.callback()
                return True
        self.color = BUTTON_COLOR_NORMAL
        pygame.mouse.set_cursor(*pygame.cursors.arrow)
        return False

    def on_click(self, callback):
        self.callback = callback

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
        
        self.current_index = 0
        self.assets_to_load = os.listdir("assets")

    def load_asset_current(self):
        if self.current_index >= len(self.assets_to_load):
            self.gstate_setter('MenuScreen')
            logging.info("Loaded all assets")
            return

        asset_name = self.assets_to_load[self.current_index]
        if asset_name not in assets:
            if '.' in asset_name:
                asset_type = asset_name.split('.')[1]
                if asset_type == 'png':
                    assets[asset_name] = pygame.image.load('./assets/'+asset_name)
                elif asset_type == 'wav' or asset_type == 'mp3':
                    assets[asset_name] = pygame.mixer.Sound('./assets/'+asset_name)
                elif asset_type == 'ttf':
                    assets[asset_name] = pygame.font.Font('./assets/'+asset_name, 20)
                else:
                    logging.error("Unknown asset type: " + asset_type)
            else:
                if os.isdir(asset_name):
                    logging.warn("Asset name has no extension: " + asset_name)
        self.current_index += 1

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

        self.load_asset_current()

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

class MenuScreen:
    def __init__(self, window, gstate_setter):
        self.window = window
        self.gstate_setter = gstate_setter
        self.buttons = []
        self.opensimplex = opensimplex.OpenSimplex(seed=random.randint(0, 1000000))
        self.frame = 0

        self.buttons.extend([
            button(
                (0, 0, 0),
                self.window.get_width() / 2,
                self.window.get_height() / 3 * 2,
                200,
                50,
                "Play",
            ),
            button(
                (0, 0, 0),
                self.window.get_width() / 2,
                self.window.get_height() / 4 * 3.5,
                200,
                50,
                "Quit",
            )
        ])
        self.buttons[0].on_click(self.play_game)
        self.buttons[1].on_click(self.quit_game)

        self.music = False

    def play_game(self):
        self.gstate_setter('PlayScreen')
        pygame.mixer.stop()

    def quit_game(self):
        pygame.mixer.stop()
        pygame.quit()
        sys.exit()
    
    def update(self):
        if not self.music:
            #pygame.mixer.Sound.play(assets['music_slow.mp3'])
            self.music = True

        for i in self.buttons:
            i.is_over(mouse_pos)
            if i.text == "Play":
                i.x, i.y = self.window.get_width() / 2 - 100, self.window.get_height() / 3 * 2
            elif i.text == "Quit":
                i.x, i.y = self.window.get_width() / 2 - 100, self.window.get_height() / 4 * 3.5
        
        self.frame += 1

    def draw(self):
        self.box_icon = assets['Box.png']
        xnoise = self.opensimplex.noise2(self.frame, -self.frame)
        ynoise = self.opensimplex.noise2(-self.frame, self.frame)
        self.window.blit(self.box_icon, (self.window.get_width() / 2 - self.box_icon.get_width() / 2 + xnoise, self.window.get_height() / 3 * 1 - self.box_icon.get_height() / 2 + ynoise))

        for i in self.buttons:
            i.draw(self.window)

class PlayScreen:
    def __init__(self, window, gstate_setter):
        self.window = window
        self.gstate_setter = gstate_setter
        self.textures = assets
        self.generated = False
        self.x_speed = 0
        self.x_move = 0.5
        self.x = 0
        self.y_speed = 0
        self.y_move = 0.5
        self.y = 0
        self.terminal_velocity = 5

        
    def update(self):
        if not self.generated:
            self.world = World(self.window, assets, self)
            self.world.generate()
            self.generated = True
            #pygame.mixer.Sound.play(assets['music_fast.mp3'])
        self.world.update()

        # Camera movement
        if pygame.key.get_pressed()[pygame.K_LEFT]:
            self.x_speed -= self.x_move
        if pygame.key.get_pressed()[pygame.K_RIGHT]:
            self.x_speed += self.x_move
        if pygame.key.get_pressed()[pygame.K_UP]:
            self.y_speed -= self.y_move
        if pygame.key.get_pressed()[pygame.K_DOWN]:
            self.y_speed += self.y_move

        # Camera bounds
        if self.x_speed < 0 and self.x_speed < -self.terminal_velocity:
            self.x_speed = -self.terminal_velocity
        if self.x_speed > 0 and self.x_speed > self.terminal_velocity:
            self.x_speed = self.terminal_velocity
        if self.y_speed < 0 and self.y_speed < -self.terminal_velocity:
            self.y_speed = -self.terminal_velocity
        if self.y_speed > 0 and self.y_speed > self.terminal_velocity:
            self.y_speed = self.terminal_velocity

        self.x_speed *= .96
        self.x += self.x_speed
        self.y_speed *= .96
        self.y += self.y_speed

    def draw(self):
        if self.generated:
            self.world.draw()

def load_screens(window, gstate_setter=set_gstate):
    screens = {}
    screens['LoadingScreen'] = LoadingScreen(window, gstate_setter)
    screens['MenuScreen'] = MenuScreen(window, gstate_setter)
    screens['PlayScreen'] = PlayScreen(window, gstate_setter)
    return screens

def draw_current_screen(screens, window):
    if not GSTATE == PlayScreen:
        window.fill((0, 0, 0))
    screens[GSTATE].draw()
    screens[GSTATE].update()
    global mouse_pos, mouse_down
    mouse_pos = pygame.mouse.get_pos()
    mouse_down = pygame.mouse.get_pressed()[0]
