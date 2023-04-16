'''
Author: wuRDmemory wuch2039@163.com
Date: 2023-03-31 07:31:19
LastEditors: Chenhao Wu wuch2039@163.com
LastEditTime: 2023-04-09 20:12:42
FilePath: /jvs_prog/robot/config.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
import os
import sys
import yaml
from easydict import EasyDict
from robot.logger import getLogger
from robot import constants

logger = getLogger(__name__)

_config = EasyDict()
has_init = False

def reload():
    """
    重新加载配置
    """
    logger.info("配置文件发生变更，重新加载配置文件")
    init()


def init():
    global has_init
    if os.path.isfile(constants.CONFIG_PATH):
        logger.critical(f"错误：{constants.CONFIG_PATH} 应该是个目录，而不应该是个文件")
    if not os.path.exists(constants.CONFIG_PATH):
        os.makedirs(constants.CONFIG_PATH)
    if not os.path.exists(constants.getConfigPath()):
        yes_no = input(f"配置文件{constants.getConfigPath()}不存在，要创建吗？(y/n)")
        if yes_no.lower() == "y":
            constants.newConfig()
            doInit(constants.getConfigPath())
        else:
            doInit(constants.getDefaultConfigPath())
    else:
        doInit(constants.getConfigPath())
    has_init = True

def doInit(config_file=constants.CONFIG_PATH):
    global _config

    # Read config
    logger.debug("Trying to read config file: '%s'", config_file)
    try:
        with open(config_file, "r") as f:
            _config = EasyDict(yaml.safe_load(f))
    except Exception as e:
        logger.error(f"配置文件 {config_file} 读取失败: {e}", stack_info=True)
        raise

def get(module, key, default=None):
    if not has_init:
        init()
    if module not in _config:
        raise KeyError(f"module '{module}' not exist in config")
    return _config.get(module).get(key, default)
