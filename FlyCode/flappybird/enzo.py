# This program calculates the area of a circle given its radius.
# radius = float(input("Enter the radius of the circle: "))
# area = 3.14 * (radius ** 2)
# print("The area of the circle is: ", area)

# please draw a pyramid using asterisks (*)
height = int(input("Enter the height of the pyramid: "))
for i in range(1, height + 1):
    print(" " * (height - i) + "*" * (2 * i - 1))