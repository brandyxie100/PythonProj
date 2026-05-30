#wWA
from random import randint

money = 10000000
while money > 0:
    print(f'你现在有{money}元')
    bet = int(input('请输入你要下注的金额：'))
    if bet > money:
        print('你没有足够的钱下注，请重新输入。')
        continue
    # roll the dice
    first = randint(1, 6)+randint(1, 6)
    print(f'你掷出了{first}点')
    if first in [7, 11]:
        print('你赢了！')
        money += bet
    elif first in [2, 3, 12]:
        print('你输了！')
        money -= bet
    else:
        point = first
        print(f'你的点数是{point}，继续掷骰子...')
        while True:
            next_roll = randint(1, 6)+randint(1, 6)
            print(f'你掷出了{next_roll}点')
            if next_roll == point:
                print('你赢了！')
                money += bet
                break
            elif next_roll == 7:
                print('你输了！')
                money -= bet
                break
