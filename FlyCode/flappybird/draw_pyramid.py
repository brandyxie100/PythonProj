# please draw pyramid wiht "*" in python

# def draw_pyramid(height):
#     for i in range(height):
#         print(" " * (height - i - 1) + "*" * (2 * i + 1))

# draw_pyramid(10)

# Draw a hollow square (only border stars)
# size = 5
# for i in range(size):
#     for j in range(size):
#         # Print star only for first/last row or first/last column
#         if i == 0 or i == size-1 or j == 0 or j == size-1:
#             print("*", end=" ")
#         else:
#             print(" ", end=" ")
#     print()  # New line
    
    # Hollow pyramid (only outline stars)
# height = 10
# for i in range(height):
#     for j in range(height - i - 1):
#         print(" ", end="")
#     for k in range(2 * i + 1):
#         # Star only for first/last row or first/last position
#         if k == 0 or k == 2*i or i == height-1:
#             print("*", end="")
#         else:
#             print(" ", end="")
#     print()
    
    # Diamond = Upward Pyramid + Inverted Pyramid
height = 5
# Top half (upward)
for i in range(height):
    print(" " * (height - i - 1) + "*" * (2 * i + 1))
# Bottom half (inverted)
for i in range(height-2, -1, -1):
    print(" " * (height - i - 1) + "*" * (2 * i + 1))

# Simple Christmas Tree (easy version)
# height = 5
# # Tree top (pyramid)
# for i in range(height):
#     print(" " * (height - i - 1) + "*" * (2 * i + 1))
# # Tree trunk
# for i in range(2):
#     print(" " * (height - 1) + "*")
    
# 打印乘法口诀表
# for i in range(1, 10):
#     for j in range(1, i + 1):
#         print(f'{i}*{j}={i * j}', end='\t')
#     print()
    
# items = [1,2,3,4,5,6,7,8,9]
# string = ""
# for i in items:
#     string += str(i)
# print(string)

