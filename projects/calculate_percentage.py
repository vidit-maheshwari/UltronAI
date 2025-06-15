# Calculate the percentage of 10 subject marks

total_marks = 0

for i in range(10):
    subject_mark = float(input(f"Enter mark for subject {i+1}: "))
    total_marks += subject_mark

percentage = (total_marks / 10) * 100

print(f"Total Marks: {total_marks:.2f}")
print(f"Percentage: {percentage:.2f}%")