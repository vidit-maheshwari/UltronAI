# Read and display contents of hello.pu

try:
    with open("hello.pu", "r") as file:
        content = file.read()
        print("Contents of hello.pu:\n" + content)
except FileNotFoundError:
    print("Error: The file hello.pu does not exist")