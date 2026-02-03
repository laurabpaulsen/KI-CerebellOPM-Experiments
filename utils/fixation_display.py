import pygame

class FixationDisplay:
    def __init__(self, size=(800, 600)):
        pygame.init()
        self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
        self.white = (255, 255, 255)
        self.black = (0, 0, 0)
        self.center = (size[0] // 2, size[1] // 2)

    def show_fixation(self, color=(255, 255, 255)):
        self.screen.fill(self.black)
        x, y = self.center
        pygame.draw.line(self.screen, color, (x, y-20), (x, y+20), 4)
        pygame.draw.line(self.screen, color, (x-20, y), (x+20, y), 4)
        pygame.display.flip()

    def show_text(self, text):
        font = pygame.font.SysFont(None, 40)
        surf = font.render(text, True, self.white)
        rect = surf.get_rect(center=self.center)
        self.screen.fill(self.black)
        self.screen.blit(surf, rect)
        pygame.display.flip()

    def close(self):
        pygame.quit()
