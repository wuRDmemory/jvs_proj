'''
Author: Chenhao Wu wuch2039@163.com
Date: 2023-04-04 22:41:35
LastEditors: Chenhao Wu wuch2039@163.com
LastEditTime: 2023-04-12 22:54:16
FilePath: /jvs_prog/robot/chat.py
Description: 
'''
import os
import time
import openai
import logging
from abc import ABCMeta, abstractmethod
from robot import config
from robot.logger import getLogger

MODULE = 'CHAT'
logger = getLogger(__name__, level=logging.DEBUG)

class ChatRobotBase(object):
    '''Abstract class for ChatRobot
    '''
    __metaclass__ = ABCMeta
    
    @classmethod
    def get_instance(cls):
        profile = cls.get_config()
        instance = cls(**profile)
        return instance

    def __init__(self, **kwargs):
        pass

    @abstractmethod
    def chat(self, texts, parsed):
        pass

    @abstractmethod
    def stream_chat(self, texts):
        pass

class GPTRobot(ChatRobotBase):
    '''GPT Chat Robot
    '''
    SLUG = 'gpt'

    def __init__(self, openai_key: str, proxy: dict):
        self.openai = openai
        self.openai.api_key = os.environ.get('OPENAI_KEY')
        self.proxy = proxy
        logger.debug('GPT openai key: %s', self.openai.api_key)

    @classmethod
    def get_config(cls):
        return config.get(MODULE, cls.SLUG, {})

    def stream_chat(self, texts):
        rsp = self.openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": texts}
            ]
        )

        try:
            return rsp['choices'][0]['message']['content']
        except Exception as e:
            logger.error('GPT chat error: %s', e)
            return None

def get_subclass(cls):
    '''Get all subclasses of a class
    '''
    subclasses = set()
    for subclass in cls.__subclasses__():
        subclasses.add(subclass)
        subclasses.update(get_subclass(subclass))
    return subclasses

def get_robot_by_slug(slug):
    '''Get robot by slug
    '''
    for robot_cls in get_subclass(ChatRobotBase):
        if robot_cls.SLUG == slug:
            return robot_cls.get_instance()
    return None

