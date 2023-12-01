import json
import os
from urllib.parse import urlparse
from urllib.request import urlopen

def make_dir_if_not_exists(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

def get_file_extension_from_url(url):
    # 解析URL的路径部分
    path = urlparse(url).path
    # 获取文件扩展名
    _, extension = os.path.splitext(path)
    # 返回扩展名，如果不存在则返回空字符串
    return extension if extension else ''

def download_file_from_url(download_url, download_dir, file_name):
    make_dir_if_not_exists(download_dir)
    with urlopen(download_url) as response, open(f'{download_dir}/{file_name}', 'wb') as out_file:
        data = response.read()
        out_file.write(data)

def add_mapping_between_attachments_and_article(mapping_file_dir: str, mapping: dict):
    # 确保目录存在
    os.makedirs(mapping_file_dir, exist_ok=True)

    # 映射文件的路径
    mapping_file_path = os.path.join(mapping_file_dir, "title_attachment_mapping.json")

    # 尝试加载现有的映射文件，如果不存在则创建一个新的空字典
    try:
        title_attachment_map = load_json_file(mapping_file_path)
    except FileNotFoundError:
        title_attachment_map = {}

    # 将新的标题与附件映射添加到字典中
    for title, attachments in mapping.items():
        title_attachment_map[title] = attachments

    # 将更新后的映射保存回文件
    with open(mapping_file_path, "w") as file:
        json.dump(title_attachment_map, file, indent=4)  # 使用indent参数使JSON文件更易读

def load_json_file(file_path):
    with open(file_path, "r") as file:
        return json.load(file)
    
def write_content_to_file(directory: str, file_name: str, content):
    """
     Write content to file. If file doesn't exist it will be created. This is to avoid overwriting files that are already in the file system
     
     Args:
     	 directory: Directory where to create the file
     	 file_name: Name of the file to create.
     	 content: Content to write to file as utf - 8
    """
    # Create a directory if it doesn't exist.
    make_dir_if_not_exists(directory)
    file_path = f'{directory}/{file_name}'
    # Write the content to file only if it doesn't exist.
    if not os.path.exists(file_path):
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)

def get_subdirectories(depth, path='.'):
    """
    Get all subdirectories up to a specified depth.

    Args:
    depth (int): The depth to search for subdirectories.
    path (str): The starting directory path. Defaults to the current directory.

    Returns:
    list: A list of subdirectories.
    """
    subdirs = []
    def recurse(current_path, current_depth):
        if current_depth > depth:
            return
        for item in os.listdir(current_path):
            full_path = os.path.join(current_path, item)
            if os.path.isdir(full_path):
                subdirs.append(full_path)
                recurse(full_path, current_depth + 1)

    recurse(path, 1)
    return subdirs
