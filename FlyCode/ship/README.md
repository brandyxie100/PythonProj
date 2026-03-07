def draw_health_bar(x, y, health, max_health):
    # Draw background (red bar)
    pygame.draw.rect(screen, (255, 0, 0), (x, y, 200, 20))
    
    # Calculate current health width
    health_width = int(200 * (health / max_health))
    
    # Draw current health (green bar)
    pygame.draw.rect(screen, (0, 255, 0), (x, y, health_width, 20))
    
    # Optional: Add health text
    health_text = font.render(f"HP: {health}", True, (255, 255, 255))
    screen.blit(health_text, (x + 210, y - 2))


Step 3: Call it in Your Game Loop
Inside your main while running: loop, after drawing the background and before pygame.display.update():

python
复制
编辑
draw_health_bar(10, 50, player_health, max_health)

Step 4: Subtract Health on Enemy Collision (Optional)
You can detect if an enemy hits the player and reduce health:

python
复制
编辑
for e in enemys:
    if distance(playerX, playerY, e.x, e.y) < 40:
        player_health -= 10
        e.reset()
        if player_health <= 0:
            print("Game Over")
            running = False  # or trigger game over screen