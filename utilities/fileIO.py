import os


def write_content_to_file(directory: str, file_name: str, content):
    """
     Write content to file. If file doesn't exist it will be created. This is to avoid overwriting files that are already in the file system
     
     Args:
     	 directory: Directory where to create the file
     	 file_name: Name of the file to create.
     	 content: Content to write to file as utf - 8
    """
    # Create a directory if it doesn't exist.
    if not os.path.exists(directory):
        os.makedirs(directory)
    file_path = f'{directory}/{file_name}'
    # Write the content to file only if it doesn't exist.
    if not os.path.exists(file_path):
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)