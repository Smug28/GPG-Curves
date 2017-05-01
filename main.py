"""
bezier.py - Calculates a bezier curve from control points. 

2007 Victor Blomqvist
Released to the Public Domain
"""
import pygame
import os
from pygame.locals import *
from pygame.compat import geterror

main_dir = os.path.split(os.path.abspath(__file__))[0]
data_dir = os.path.join(main_dir, 'data')

def load_image(name, colorkey=None):
    fullname = os.path.join(data_dir, name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error:
        print ('Cannot load image:', fullname)
        raise SystemExit(str(geterror()))
    image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0,0))
        image.set_colorkey(colorkey, RLEACCEL)
    return image, image.get_rect()

class vec2d(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Car(pygame.sprite.Sprite):
    """moves a clenched fist on the screen, following the mouse"""
    def __init__(self):
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer
        self.image, self.rect = load_image('car.png', -1)
        self.curve_pos = 0

    def update(self, new_pos):
        "move the fist based on the mouse position"
        center = self.rect.center
        self.rect.center = (new_pos[0] - center[0], new_pos[1] - center[1])


class BezierCurve(object):
    def __init__(self, control_points, car=None):
        self.vertices = control_points
        self.car = car

    def add_point(self, point):
        self.vertices.append(point)

    def num_points(self):
        return len(self.vertices)

    def move_car(self):
        if self.car is not None:
            pts = self.compute_points(num_points=100)
            try:
                self.car.update(pts[int(self.car.curve_pos)])
                self.car.curve_pos += 0.1
            except IndexError:
                self.car.update(pts[0])
                self.car.curve_pos = 0

    def draw_car(self, screen):
        if self.car is not None:
            self.move_car()
            screen.blit(self.car.image, self.car.rect.center)

    def compute_points(self, num_points=32):
        vertices = [(x.x, x.y) for x in self.vertices]
        if num_points < 2 or len(vertices) != 4:
            return None

        result = []

        b0x = vertices[0][0]
        b0y = vertices[0][1]
        b1x = vertices[1][0]
        b1y = vertices[1][1]
        b2x = vertices[2][0]
        b2y = vertices[2][1]
        b3x = vertices[3][0]
        b3y = vertices[3][1]

        # Compute polynomial coefficients from Bezier points
        ax = -b0x + 3 * b1x + -3 * b2x + b3x
        ay = -b0y + 3 * b1y + -3 * b2y + b3y

        bx = 3 * b0x + -6 * b1x + 3 * b2x
        by = 3 * b0y + -6 * b1y + 3 * b2y

        cx = -3 * b0x + 3 * b1x
        cy = -3 * b0y + 3 * b1y

        dx = b0x
        dy = b0y

        # Set up the number of steps and step size
        numSteps = num_points - 1  # arbitrary choice
        h = 1.0 / numSteps  # compute our step size

        # Compute forward differences from Bezier points and "h"
        pointX = dx
        pointY = dy

        firstFDX = ax * (h * h * h) + bx * (h * h) + cx * h
        firstFDY = ay * (h * h * h) + by * (h * h) + cy * h

        secondFDX = 6 * ax * (h * h * h) + 2 * bx * (h * h)
        secondFDY = 6 * ay * (h * h * h) + 2 * by * (h * h)

        thirdFDX = 6 * ax * (h * h * h)
        thirdFDY = 6 * ay * (h * h * h)

        # Compute points at each step
        result.append((int(pointX), int(pointY)))

        for i in range(numSteps):
            pointX += firstFDX
            pointY += firstFDY

            firstFDX += secondFDX
            firstFDY += secondFDY

            secondFDX += thirdFDX
            secondFDY += thirdFDY

            result.append((int(pointX), int(pointY)))

        return result

gray = (0xee, 0xee, 0xee)
lightgray = (200, 200, 200)
red = (255, 0, 0)
green = (0, 255, 0)
blue = (0, 0, 255)
X, Y, Z = 0, 1, 2

def main():
    pygame.init()
    screen = pygame.display.set_mode((1024, 768))

    # The currently selected point
    selected = None

    clock = pygame.time.Clock()

    curves = [BezierCurve([vec2d(100, 100), vec2d(150, 500), vec2d(450, 500), vec2d(500, 150)], car=Car()), BezierCurve([])]
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN and event.key == K_RETURN:
                curves = [BezierCurve([], car=Car()), ]
            elif event.type == MOUSEBUTTONDOWN and event.button == 1:
                for curve in curves:
                    for p in curve.vertices:
                        if abs(p.x - event.pos[X]) < 10 and abs(p.y - event.pos[Y]) < 10:
                            selected = p
            elif event.type == MOUSEBUTTONDOWN and event.button == 3:
                x,y = pygame.mouse.get_pos()
                if curves[-1].num_points() < 4:
                    curves[-1].add_point(vec2d(x, y))
                else:
                    curves.append(BezierCurve([vec2d(x, y), ]))
            elif event.type == MOUSEBUTTONUP and event.button == 1:
                selected = None

        # Draw stuff
        screen.fill(gray)

        if selected is not None:
            selected.x, selected.y = pygame.mouse.get_pos()
            pygame.draw.circle(screen, green, (selected.x, selected.y), 10)

        for curve in curves:
            # Draw control points
            for p in curve.vertices:
                pygame.draw.circle(screen, blue, (int(p.x), int(p.y)), 4)

            if curve.num_points() < 2:
                continue

            # Draw control "lines"
            pygame.draw.lines(screen, lightgray, False, [(x.x, x.y) for x in curve.vertices])

            if curve.num_points() != 4:
                continue

            # Draw bezier curve
            b_points = curve.compute_points()
            pygame.draw.lines(screen, pygame.Color("red"), False, b_points, 2)

            # curve.draw_car(screen)

        # Flip screen
        pygame.display.flip()
        clock.tick(100)
        # print clock.get_fps()


if __name__ == '__main__':
    main()