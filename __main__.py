import time
import pygame
from pygame.locals import *
import sys

from screens import load_screens

BOXICON = pygame.image.load("assets/Box.png")
GSTATE = 'LoadingScreen'

def set_gstate(gstate):
    global GSTATE
    GSTATE = gstate

pygame.init()
window = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
pygame.display.set_caption("Box")
pygame.display.set_icon(BOXICON)
min_size = (800, 600)

screens = load_screens(window, set_gstate)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == VIDEORESIZE:
            width, height = event.size
            if width < min_size[0] or height < min_size[1]:
                width, height = min_size
            window = pygame.display.set_mode((width, height), pygame.RESIZABLE)

    screens[GSTATE].draw()
    screens[GSTATE].update()

    pygame.display.update()
    time.sleep(0.001)
