# This program calculates the area of a circle given its radius.
# radius = float(input("Enter the radius of the circle: "))
# area = 3.14 * (radius ** 2)
# print("The area of the circle is: ", area)

# please draw a pyramid using asterisks (*)
# height = int(input("Enter the height of the pyramid: "))
# for i in range(1, height + 1):
#     print(" " * (height - i) + "*" * (2 * i - 1))

import random

answer = random.randint(1, 100)
counter = 0
while True:
    counter += 1
    number = int(input("Guess the number between 1 and 100: "))
    if number < answer:
        print("Too low! Try again.")
    elif number > answer:
        print("Too high! Try again.")
    else:
        print(f"Congratulations! You've guessed the number {answer} in {counter} attempts.")
        break
print("Thank you for playing!")

