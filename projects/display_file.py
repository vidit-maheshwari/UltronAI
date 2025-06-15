def display_file_content(file_name):
    """
    Displays the content of the specified file.
    
    Args:
        file_name (str): Name of the file to display
    """
    try:
        with open(file_name, 'r') as file:
            content = file.read()
            print("Content of", file_name, "\n", content)
    except FileNotFoundError:
        print(f"Error: The file {file_name} does not exist.")
    except IOError:
        print(f"Error: Unable to read {file_name}.")

# Example usage
if __name__ == "__main__":
    display_file_content("hello.pu")