# Function to calculate percentage of 10 subjects

def calculate_percentage():
    total = 0
    for i in range(10):
        while True:
            try:
                mark = float(input(f"Enter mark for subject {i+1}: "))
                total += mark
                break
            except ValueError:
                print("Invalid input. Please enter a valid number.")
    percentage = total / 10
    return round(percentage, 2)

# Main function

def main():
    print("Enter marks for 10 subjects:")
    percentage = calculate_percentage()
    print(f"\nTotal Marks: {round(percentage * 10, 2)}")
    print(f"Percentage: {percentage}%")

if __name__ == "__main__":
    main()