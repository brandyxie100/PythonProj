import pygame
from pygame.locals import*
import random

pygame.init()

clock = pygame.time.Clock()
fps=60



screen_width=864
screen_height=768
bg = pygame.image.load('img/bg.png')
ground_img = pygame.image.load('img/ground.png')
screen=pygame.display.set_mode((screen_width,screen_height))
pygame.display.set_caption("Flapy Bird")

ground_scroll=0
scroll_speed = 6
flying = False
game_over = False
auto_play = False
pipe_gap = 200
pipe_spawn_timer = 0
pipe_spawn_interval = 90
class Bird (pygame.sprite.Sprite):
    def __init__(self,x,y):
        pygame.sprite.Sprite.__init__(self)
        self. images = []
        self.index = 0
        self.counter = 0
        for i in range(1, 4):
            # img = pygame.image.load(f'C:/Code/flappybird/img/bird{num}.png')
            img = pygame.image.load(f'./img/bird{i}.png')
            self.images.append(img)
        self.image=self.images[self.index]
        self.rect=self.image.get_rect()
        self.rect.center=[x,y]
        self.vel=0
        self.clicked = False
    def update(self):
        if flying ==True:
        
            self.vel += 0.5
            if self.vel > 8:
                self.vel = 8
            # debug print disabled
        
            if self.rect.bottom < 650:
                self.rect.y += int(self.vel)
            
        if game_over == False:
            # handle input: either autoplayer or manual mouse click
            flap = False
            if auto_play:
                # simple heuristic: flap when falling fast or below screen center
                if self.vel > 3 or self.rect.centery > int(screen_height/2) + 30:
                    flap = True
            else:
                if pygame.mouse.get_pressed()[0] == 1 and self.clicked==False:
                    flap = True

            if flap:
                self.clicked = True
                self.vel = -10

            if not auto_play:
                if pygame.mouse.get_pressed()[0] == 0:
                    self.clicked = False
            self.counter+= 1
            flap_cooldown = 5
            
            if self.counter > flap_cooldown:
                self.counter = 0
                self.index+=1
                if self.index >= len(self.images):
                    self.index = 0
            self.image = pygame.transform.rotate(self.images[self.index], self.vel*-5)
            self.rect = self.image.get_rect(center=self.rect.center)
        else:
            self.image = pygame.transform.rotate(self.images[self.index], -90)
            self.rect = self.image.get_rect(center=self.rect.center)
        
       
class Pipe(pygame.sprite.Sprite):
    def __init__(self, x, y,position):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('img/pipe.png')
        self.rect = self.image.get_rect()
        if position == 1:
            self.image = pygame.transform.flip(self.image,False,True)
            self.rect.bottomleft = [x,y]
        if position == -1:     
            self.rect.topleft = [x,y]
    def update(self):
        # move pipe left and remove when off-screen
        if not game_over:
            self.rect.x -= scroll_speed
        if self.rect.right < 0:
            self.kill()
        
         
bird_group = pygame.sprite.Group()
pipe_group = pygame.sprite.Group()
flappy=Bird(100, int(screen_height/2))
bird_group.add(flappy)

def spawn_pipes(x, gap):
    # choose a random center for the gap
    center_y = random.randint(200, 450)
    top_y = center_y - gap // 2
    bottom_y = center_y + gap // 2
    top = Pipe(x, top_y, 1)
    bottom = Pipe(x, bottom_y, -1)
    pipe_group.add(top)
    pipe_group.add(bottom)

# initial pipes
spawn_pipes(300, pipe_gap)

def restart_game(extra_distance=400):
    global game_over, flying, pipe_spawn_timer, pipe_spawn_interval
    # reset flags
    game_over = False
    flying = False
    # reset bird
    flappy.rect.center = [100, int(screen_height/2)]
    flappy.vel = 0
    flappy.index = 0
    flappy.counter = 0
    # clear pipes and reset timers
    pipe_group.empty()
    pipe_spawn_timer = 0
    pipe_spawn_interval = random.randint(80, 120)
    # spawn first pipe farther ahead so there's more distance
    spawn_pipes(screen_width + extra_distance, pipe_gap)

run=True
while run:
    clock.tick(fps)
    screen.blit(bg,(0,0))
    
    bird_group.draw(screen)
    bird_group.update()
    pipe_group.draw(screen)
    pipe_group.update()

    # collision: end game when bird hits any pipe
    if pygame.sprite.spritecollide(flappy, pipe_group, False):
        game_over = True
        flying = False
    
    
    
    screen.blit(ground_img,(ground_scroll,650))
    
    
    
    if flappy.rect.bottom > 650:
        game_over = True
        flying = False
   #screen.blit(ground_img,(ground_scroll,650))
    if game_over == False:
        ground_scroll -= scroll_speed
        if abs(ground_scroll) > 35:
            ground_scroll=0
        # pipe spawning timer (spawn when running)
        pipe_spawn_timer += 1
        if pipe_spawn_timer > pipe_spawn_interval:
            # randomize gap and interval slightly
            gap = pipe_gap + random.randint(-40, 40)
            spawn_x = screen_width + 50
            spawn_pipes(spawn_x, gap)
            pipe_spawn_timer = 0
            pipe_spawn_interval = random.randint(80, 120)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run= False
        if event .type == pygame.MOUSEBUTTONDOWN and flying == False and game_over == False:
            flying = True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                # restart game and place next pipes further ahead
                restart_game(extra_distance=400)
            if event.key == pygame.K_d:
                # delete the first (nearest upcoming) pipe pair
                if len(pipe_group) > 0:
                    # consider only pipes still on-screen (or ahead)
                    candidates = [p for p in pipe_group.sprites() if p.rect.right > 0]
                    if candidates:
                        first_x = min(candidates, key=lambda p: p.rect.x).rect.x
                        for p in pipe_group.sprites():
                            if p.rect.x == first_x:
                                p.kill()
            
    pygame.display.update()            
pygame.quit()