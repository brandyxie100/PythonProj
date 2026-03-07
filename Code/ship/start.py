import pygame
import random
import math



from component.player import Player
from component.enemy  import Enemy
from component.bullet import Bullet

pygame.init()
bg = pygame.image.load('asset/bg3.jpg')
screen = pygame.display.set_mode((800,600))

pygame.mixer.music.load('asset/background-music.mp3')
pygame.mixer.music.play(-1) 


number_of_enemies=1000
playerStep = 0
running = True

player = Player()
# create enemies
enemys=[]
bullets = []

for i in range(number_of_enemies):
    enemy = Enemy()
    enemys.append(enemy)

def show_enemies():
    for e in enemys:
        screen.blit(e.show_ememy(), (e.get_enemy_x(), e.get_enemy_y()))
        # e.change_x()
        # if e.get_enemy_x() > 740 or e.get_enemy_x() < -30:
        #     e.change_step()
        #     e.change_y()
        e.change_y()
        if e.get_enemy_y() > 600:
            e.reset()
            
        if is_collision(e.get_enemy_x(), e.get_enemy_y(), player.get_player_x(), player.get_player_y()):
            player.health -= 10  
            print("Player hit! Health:", player.health)
            e.reset()     

def is_collision(x1, y1, x2, y2, radius=40):
    return math.dist((x1, y1), (x2, y2)) < radius    
            
def show_bullet(screen, bullets, enemys):
    for b in bullets[:]:
        b.move_bullet()
        screen.blit(b.show_bullet(),(b.get_bullet_x(), b.get_bullet_y()))
        
        if b.get_bullet_y() < -40:
           bullets.remove(b)
           continue
        
        hit_enemy = b.hit(enemys)
        if hit_enemy:
            b.bao_sound()
            enemys.remove(hit_enemy)
            bullets.remove(b )

        
      
def main():
    running = True
    while running:
        screen.blit(bg,(1,2))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_SPACE:
                    bullet = Bullet(playerX=player.get_player_x(),playerY=player.get_player_y())
                    bullets.append(bullet)
                    print('shoot')
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHT]:
            player.move_right()
        if keys[pygame.K_LEFT]:
            player.move_left()            
        
        
        screen.blit(player.show_player(), (player.get_player_x(), player.get_player_y())) 
        player.draw_health_bar(screen)

        
        if player.get_player_x()>645:  
            player.x =645
        if player.get_player_x()<-45:
            player.x = -45  
            
        show_enemies()    
        show_bullet(screen=screen, bullets=bullets, enemys=enemys)
        
        if player.health <= 0:
            print("Game Over")
            running = False
        pygame.display.update()
    

if __name__ == "__main__":
    main()












# screen = pygame.display.set_mode((800,600))
# pygame.display.set_caption('pygame plane')
# icon = pygame.image.load('ufo.webp')
# pygame.display.set_icon(icon)
# bg = pygame.image.load('bg3.jpg')

# player = Player
# playerImg = player.show_player()
# # playerImg = pygame.image.load('player-removebg-preview.png')


# pygame.mixer.music.load('background-music.mp3')
# pygame.mixer.music.play(-1) 
# bao_sound=pygame.mixer.Sound("minecraft-tnt-explosion.mp3")

# score=0
# font=pygame.font.Font('freesansbold.ttf',32)


# number_of_enemies=100

# player_health=100
# max_health=100

            

    

# def draw_health_bar(x,y,health,max_health):
#     pygame.draw.rect(screen,(255,0,0),(x,y,200,20))
#     health_width = int(200*(health/max_health))
#     pygame.draw.rect(screen,(0,255, 0),(x,y, health_width,20))
#     health_text=font.render(f"hp:{health}",True,(255,255,255))
#     screen.blit(health_text,(x+210,y-2))

    
    
       
# def show_score():
#     text=f"score:{score} "
#     score_render=font.render(text,True,(0,255,0) )
#     screen.blit(score_render,(10,10))






# class Enemy():
#     def __init__(self):
#         self.img=pygame.image.load('enemy.png')
#         self.img = pygame.transform.scale(self.img, (80,80))
#         self.x = random.randint(300,400)
#         self.y=random.randint(75,250)
#         self.step=random.uniform(1,1.5)
#     def reset(self):    
#         self.x=random.randint(300,400)
#         self.y=random.randint(75,250)
        
# enemys=[]
# for i in range(number_of_enemies):
#     enemys.append(Enemy())


# def distance(bx,by,ex,ey):
#     a=bx-ex
#     b=by-ey
#     return math.sqrt(a*a+b*b) 
# class Bullet():
#     def __init__(self):
#         self.img=pygame.image.load('bullet_resized.png')
#         self.img = pygame.transform.scale(self.img, (40,40))
#         self.x =playerX+75
#         self.y=playerY - 2
#         self.step=2
    
#     def hit(self):
#         global score, player_health
#         for e in enemys:
#             if (distance(self.x, self.y, e.x, e.y)<30):
#                 bao_sound.play()
#                 player_health -=10
#                 e.reset()
#                 score+=1
#                 if player_health<=0:
#                     print("Game Over ")
#                 print(score)
#                 return True
#         return False
# bullets = []        
    
    
# def show_bullets():
#     global bullets
#     new_bullets=[]
#     for b in bullets:
        
#         hit=b.hit()
#         b.y-=b.step
#         if not hit and b.y>0:
#             new_bullets.append(b)
#         screen.blit(b.img,(b.x, b.y))    
#     bullets=new_bullets
    
        
        
# def show_enemy():
   
#     for e in enemys:    
#         screen.blit(e.img,(e.x, e.y))
#         e.x+=e.step
#         if (e.x>655 or e.x<-30 ):
#             e.step *= -1 
#             e.y += 30 
            


      
    

# while running:

#     screen.blit(bg,(1,2))
#     show_score()
#     draw_health_bar(10, 50, player_health, max_health)

#     # process_event()
#     for event in pygame.event.get():
#         if event.type == pygame.QUIT:
#             running = False
#         if event.type==pygame.KEYDOWN:
#             if event.key==pygame.K_RIGHT:
#                  playerStep=1.5
#             elif event.key == pygame.K_LEFT:      
#                 playerStep =-1.5
#             elif event.key==pygame.K_SPACE:
#                 print('shoot')
#                 bullets.append(Bullet())
#         if event.type==pygame.KEYUP:
#             playerStep=0   
#     screen.blit(playerImg, (playerX,playerY)) 
#     playerX += playerStep
    
#     if playerX>645:  
#         playerX =645
#     if playerX<-45:
#         playerX = -45    
#     show_bullets()   
#     show_enemy() 
#     pygame.display.update()
    
        
        
        
        
        
        
        
        
        
        
        
        
        
        