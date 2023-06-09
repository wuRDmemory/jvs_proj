'''
Author: Chenhao Wu wuch2039@163.com
Date: 2023-04-16 17:39:10
LastEditors: Chenhao Wu wuch2039@163.com
LastEditTime: 2023-04-16 18:21:08
FilePath: /jvs_prog/robot/conversation.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''

import os
from robot import logger
from robot.asr_base import ASRBase
from robot.chat import ChatRobotBase

logging = logger.getLogger(__name__)

class Conversation:
    def __init__(self, asr: ASRBase, tts, chat: ChatRobotBase):
        self.asr = asr
        self.tts = tts
        self.chat = chat

    def converse(self, fp: str):
        """conversation function, input a audio file, output a audio file
        Args:
            fp (str): audio file path 
        Returns:
            None
        """
        text = self.asr.transcribe(fp)
        logging.info('ASR: %s', text)
        response = self.chat.stream_chat(text)
        logging.info('Chat: %s', response)
