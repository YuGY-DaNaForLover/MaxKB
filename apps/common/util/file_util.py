# coding=utf-8
"""
    @project: maxkb
    @Author：虎
    @file： file_util.py
    @date：2023/9/25 21:06
    @desc:
"""

def get_file_content(path, encoding='utf-8'):
    with open(path, "r", encoding=encoding) as file:
        content = file.read()
    return content

def get_mk_file_content(path):
    with open(path, "rb") as file:
        byte_content = file.read()
    return byte_content
