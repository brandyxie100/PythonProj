import random

answer = random.randint(1, 100)
while True:
    guess = int(input("请输入一个1-100之间的整数："))
    if guess < answer:
        print("太小了！")
    elif guess > answer:
        print("太大了！")
    else:
        print("恭喜你，猜对了！")
        break
    