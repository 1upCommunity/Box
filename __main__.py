import time
import pygame
from pygame.locals import *
import sys

from screens import load_screens, draw_current_screen

BOXICON = pygame.image.load("assets/Box.png")

pygame.init()
window = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
pygame.display.set_caption("Box")
pygame.display.set_icon(BOXICON)
min_size = (800, 600)

screens = load_screens(window)

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

    draw_current_screen(screens, window)

    pygame.display.update()
    time.sleep(0.001)
