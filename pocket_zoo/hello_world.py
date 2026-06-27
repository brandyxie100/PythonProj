# I want to create times table for a given number. The function will take an integer as input and print the multiplication table for that number up to 10.
def times_table(number):
    for i in range(1, 19):
        result = number * i
        print(f"{number} x {i} = {result}")

# Example usage:
if __name__ == "__main__":
    num = int(input("Enter a number to generate its times table: "))
    times_table(num)