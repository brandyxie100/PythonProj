import pygame
import random

class Enemy:
    def __init__(self):
        self.img = pygame.image.load('asset/enemy.png')
        self.img = pygame.transform.scale(self.img, (80,80))
        self.x = random.randint(10,750)
        self.y = random.randint(0,10)
        self.step = random.uniform(1,1.5)
        
    def show_ememy(self):    
        return self.img
    
    def reset(self):    
        self.x = random.randint(10,750)
        self.y = random.randint(0,10)
    
    def get_enemy_x(self):
        return self.x
    
    def get_enemy_y(self):
        return self.y
    
    def change_x(self):
        self.x += self.step
        
    def change_y(self):       
        self.y += 0.2
    
    def change_step(self):
        self.step *= -1
