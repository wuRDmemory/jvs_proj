'''
Author: wuRDmemory wuch2039@163.com
Date: 2023-03-26 21:19:44
LastEditors: Chenhao Wu wuch2039@163.com
LastEditTime: 2023-04-16 18:04:11
FilePath: /jvs_prog/main.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''

import os
import sys
import argparse
import yaml
from robot import utils
from easydict import EasyDict
from robot.asr_base import get_engine_by_slug as get_asr_by_slug
from robot.chat import get_robot_by_slug as get_chat_by_slug
from robot.recorder import recode_voice
from robot.logger import getLogger
from snowboy.snowboydecoder import HotwordDetector, play_audio_file
from robot.conversation import Conversation

logger = getLogger(__name__)

def parse_args():
    '''parse arguments for main function
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', default='config/config.yaml', help='config file')
    args = parser.parse_args()
    return args

def read_config(config_file):
    '''read config file
    '''
    with open(config_file, 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return EasyDict(config) 

class JVSRobot:
    def __init__(self, config):
        self.config = config
        self.asr = get_asr_by_slug(config.ASR.slug)
        self.chat = get_chat_by_slug(config.CHAT.slug)
        self.detector = HotwordDetector(config.DETECTOR)
        self.conversation = Conversation(self.asr, None, self.chat)

    def _detected_callback(self):
        def _start_record():
            logger.info("start recording...")
            # self.conversation.isRecording = True
            utils.setRecordable(True)
        
        play_audio_file()

    def run(self):
        try:
            self.detector.start(
                detected_callback = self._detected_callback,
                audio_recorder_callback = self.conversation.converse,
                sleep_time=0.03
            )
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt")
        self.detector.terminate()

def main():
    args = parse_args()
    config = read_config(args.config)

    robot = JVSRobot(config)
    robot.run()

    # # baidu_asr = ASRBuide(config.appid, config.api_key, config.secret_key)
    # recode_voice('output.wav')
    # baidu_asr = ASRBuide(config.ASR.app_id, config.ASR.api_key, config.ASR.secret_key)
    # baidu_asr.transcribe('output.wav')

if __name__ == '__main__':
    main()