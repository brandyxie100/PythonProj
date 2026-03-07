import pygame
import math

class Bullet:
    def __init__(self,playerX,playerY):
        self.img=pygame.image.load('asset/bullet_resized.png')
        self.img = pygame.transform.scale(self.img, (40,40))
        self.x =playerX+75
        self.y=playerY - 2
        self.step=2
        
    def show_bullet(self):
        return self.img    
    
    def get_bullet_x(self):
        return self.x
    
    def get_bullet_y(self):
        return self.y
    
    def move_bullet(self):
        self.y -= self.step
        
    def hit(self,enemies):
        for e in enemies:
            dist = math.dist((self.x,self.y), (e.get_enemy_x() , e.get_enemy_y()))
            if dist <30:
                return e
        return None
    
    def bao_sound(self):
        bao_sound=pygame.mixer.Sound("asset/minecraft-tnt-explosion.mp3")
        bao_sound.play()    
    
    # def hit(self):
    #     global score, player_health
    #     for e in enemys:
    #         if (distance(self.x, self.y, e.x, e.y)<30):
    #             bao_sound.play()
    #             player_health -=10
    #             e.reset()
    #             score+=1
    #             if player_health<=0:
    #                 print("Game Over ")
    #             print(score)
    #             return True
    #     return False