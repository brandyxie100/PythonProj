# please draw pyramid wiht "*" in python

def draw_pyramid(height):
    for i in range(height):
        print(" " * (height - i - 1) + "*" * (2 * i + 1))

draw_pyramid(100)