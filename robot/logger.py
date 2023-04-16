'''
Author: wuRDmemory wuch2039@163.com
Date: 2023-03-29 21:20:57
LastEditors: Chenhao Wu wuch2039@163.com
LastEditTime: 2023-04-09 19:55:12
FilePath: /jvs_prog/robot/loger.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
import logging
import os
from logging.handlers import RotatingFileHandler

PAGE = 4096
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR


def getLogger(name, level: int=logging.INFO):
    """
    作用同标准模块 logging.getLogger(name)

    :returns: logger
    """
    format = "%(asctime)s - %(name)s - %(filename)s - %(funcName)s - line %(lineno)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(format)
    logging.basicConfig(format=format)
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # FileHandler
    file_handler = RotatingFileHandler(
        os.path.join("/tmp", "wukong.log"),
        maxBytes=1024 * 1024,
        backupCount=5,
    )
    file_handler.setLevel(level=logging.NOTSET)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger