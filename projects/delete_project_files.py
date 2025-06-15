# ⚠️ WARNING: This script will PERMANENTLY DELETE files in the specified directory!

import os
import shutil
from send2trash import send2trash

def delete_project_files(directory):
    try:
        # Get the absolute path of the directory
        directory = os.path.abspath(directory)
        
        # List all files and directories in the directory
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            
            # Check if the item is a file
            if os.path.isfile(item_path):
                try:
                    # Option 1: Permanently delete the file
                    # os.remove(item_path)
                    # print(f"Permanently deleted file: {item_path}")

                    # Option 2: Send file to trash (safer option)
                    send2trash(item_path)
                    print(f"Moved file to trash: {item_path}")
                except Exception as e:
                    print(f"Failed to delete file: {item_path} - {str(e)}")

    except Exception as e:
        print(f"Error accessing directory: {directory} - {str(e)}")

# Specify the directory you want to clear
projects_dir = "Projects"

# Confirmation before deletion
if input(f"Are you sure you want to delete all files in {projects_dir}? (y/n): ").lower() == 'y':
    delete_project_files(projects_dir)
    print("File deletion process completed")
else:
    print("Operation cancelled")