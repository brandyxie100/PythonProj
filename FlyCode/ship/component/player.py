import pygame

class Player:
    def __init__(self):
        self.health=100
        self.max_health=100
        self.x=400
        self.y=450
        self.img = pygame.image.load('asset/player-removebg-preview.png')
        self.step=1.5
         
    def show_player(self):
        return self.img
    
    def change_x(self, step):
        self.x += step
    
    def get_player_x(self):
        return self.x
        
    def get_player_y(self):    
        return self.y
    
    def move_left(self):
        self.x -= self.step    
    
    def move_right(self):
        self.x += self.step   
    
    
    def draw_health_bar(self, surface):
        # Position the bar just above the player
        bar_x = self.x + 50  
        bar_y = self.y - 15
        bar_width = 100
        bar_height = 10

        # Calculate health ratio
        health_ratio = self.health / self.max_health

        # Draw red background
        pygame.draw.rect(surface, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        # Draw green foreground (current health)
        pygame.draw.rect(surface, (0, 255, 0), (bar_x, bar_y, bar_width * health_ratio, bar_height))

        # Optional: draw border
        pygame.draw.rect(surface, (0, 0, 0), (bar_x, bar_y, bar_width, bar_height), 2)    



