'''
Author: Chenhao Wu wuch2039@163.com
Date: 2023-04-04 22:41:35
LastEditors: Chenhao Wu wuch2039@163.com
LastEditTime: 2023-04-12 22:54:16
FilePath: /jvs_prog/robot/chat.py
Description: 
'''
import time
import openai
from abc import ABCMeta, abstractmethod
from robot import config, logger, constants

MODULE = 'CHAT'
logger = logger.getLogger(__name__)

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
        self.openai.api_key = openai_key
        self.proxy = proxy

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
        return rsp['choices'][0]['message']['content']

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

if __name__ == '__main__':
    robot = get_robot_by_slug('gpt')
    robot.stream_chat('帮我打开灯')
