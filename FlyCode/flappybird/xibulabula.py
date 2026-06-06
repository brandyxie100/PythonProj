# craps game

from random import randint

money = 90000000000000000000000000000000000000000000000000
while money > 0:
    print("You have $", money)
    bet = int(input("Enter your bet: "))
    if bet > money:
        print("You don't have enough money to bet that much.")
        continue
    # roll the dice
    first = randint(1, 6) + randint(1, 6)
    print("You rolled a", first) 
    if first in [7, 11]:
        print("You win!")
        money += bet
    elif first in [2, 3, 12]:
        print("You lose!")
        money -= bet
    else:
        point = first
        print("Your point is", point)
        while True:
            roll = randint(1, 6) + randint(1, 6)
            print("You rolled a", roll)
            if roll == point:
                print("You win!")
                money += bet
                break
            elif roll == 7:
                print("You lose!")
                money -= bet
                break