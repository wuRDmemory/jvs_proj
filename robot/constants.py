'''
Author: wuRDmemory wuch2039@163.com
Date: 2023-03-31 07:22:24
LastEditors: Chenhao Wu wuch2039@163.com
LastEditTime: 2023-04-16 17:59:40
FilePath: /jvs_prog/robot/constants.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
import os
import sys
from easydict import EasyDict

DEFUALT_ROOT = os.getcwd()
CONFIG_PATH = os.path.join(DEFUALT_ROOT, 'config')

def getConfigPath():
    return os.path.join(CONFIG_PATH, 'config.yaml')