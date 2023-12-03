from functools import wraps
import json
import os
from typing import List
from urllib.parse import urlparse
from urllib.request import urlopen
from bs4 import BeautifulSoup

def _parse_html_files(root_directory, parse):
    def outer_wrapper(func):
        @wraps(func)
        def inner_wrapper(*args, **kargs):
            for root, dirs, files in os.walk(root_directory):
                for filename in files:
                    if filename.endswith(".html"):
                        # 构建HTML文件的完整路径
                        html_file_path = os.path.join(root, filename)
                        
                        # 使用BeautifulSoup解析HTML文件
                        with open(html_file_path, 'r', encoding='utf-8') as html_file:
                            
                            # 获取相对路径（相对于根目录
                            relative_path: str = os.path.relpath(html_file_path, root_directory)
                            structures: List[str] = relative_path.split(os.path.sep)

                            # 提取HTML内容
                            if parse:
                                soup = BeautifulSoup(html_file, 'html.parser')
                                html_content = soup.get_text('\n')
                            else:
                                html_content =  html_file.read()
                            # Inject args into the decorated function
                            kargs['structures'] = structures
                            kargs['html_content'] = html_content
                            func(*args, **kargs)
        return inner_wrapper
    return outer_wrapper

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

"""
    示例用法
    root_directory = '/Users/panyanlong/workspace/gwy_exam_info/articles'  # 替换为要搜索的根目录的路径
    extract_html_to_doc(root_directory, 'beautified_and_parsed.doc', beautify=True)
    extract_html_to_doc(root_directory, 'beautified_but_unparsed.doc', beautify=True, parse=False)
    extract_html_to_doc(root_directory, 'not_beautified_and_unparsed.doc', beautify=False, parse=False)
"""
def extract_html_to_doc(root_directory, output_doc_file, beautify: bool=False, parse: bool=True):
    # 打开输出的.doc文件
    with open(output_doc_file, 'a', encoding='utf-8') as doc_file:
        @_parse_html_files(root_directory, parse)
        def write_content(structures, html_content):
            # 将标题和HTML内容写入.doc文件
            if beautify:
                # 在标题前添加分页符
                doc_file.write('\f')
            doc_file.write(f"标题: {structures[-1].strip('.html')}\n")
            doc_file.write(f"省份: {structures[0]}\n")
            doc_file.write(f"考试类型: {structures[1]}\n")
            doc_file.write(f"资讯类型: {structures[2]}\n")
            doc_file.write(f"采集日期: {structures[3].replace('_', '-')}\n")
            doc_file.write(html_content)
            doc_file.write('\n')
            
            # print(f"{'/'.join(structures)} is processed")
        write_content()
