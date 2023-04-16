'''
Author: wuRDmemory wuch2039@163.com
Date: 2023-03-26 22:03:39
LastEditors: Chenhao Wu wuch2039@163.com
LastEditTime: 2023-04-16 18:01:27
FilePath: /jvs_prog/asr/asr_base.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''

import os
import sys
import wave
import whisper
from robot import config
from abc import ABCMeta, abstractmethod
from aip import AipSpeech
from robot.logger import getLogger

MODULE = 'ASR'
logger = getLogger(__name__)

class ASRBase(object):
    '''Abstract class for ASR
    '''
    __metaclass__ = ABCMeta

    @classmethod
    def get_config(cls):
        return {}

    @classmethod
    def get_instance(cls):
        profile = cls.get_config()
        instance = cls(**profile)
        return instance

    @abstractmethod
    def transcribe(self, fp):
        pass

    @abstractmethod
    def get_pcm_from_wav(self, wav_path):
        """
        从 wav 文件中读取 pcm

        :param wav_path: wav 文件路径
        :returns: pcm 数据
        """
        wav = wave.open(wav_path, "rb")
        return wav.readframes(wav.getnframes())

class ASRBuide(ASRBase):
    """
    百度的语音识别API.
    dev_pid:
        - 1936: 普通话远场
        - 1536：普通话(支持简单的英文识别)
        - 1537：普通话(纯中文识别)
        - 1737：英语
        - 1637：粤语
        - 1837：四川话
    要使用本模块, 首先到 yuyin.baidu.com 注册一个开发者账号,
    之后创建一个新应用, 然后在应用管理的"查看key"中获得 API Key 和 Secret Key
    填入 config.xml 中.
    """

    SLUG = "baidu_asr"

    def __init__(self, app_id, api_key, secret_key, dev_pid=1936, **args):
        super(self.__class__, self).__init__()
        self.client = AipSpeech(app_id, api_key, secret_key)
        self.dev_pid = dev_pid

    @classmethod
    def get_config(cls):
        # Try to get baidu_yuyin config from config
        return config.get(MODULE, ASRBuide.SLUG, {})

    def transcribe(self, fp):
        # 识别本地文件
        pcm = self.get_pcm_from_wav(fp)
        res = self.client.asr(pcm, "pcm", 16000, {"dev_pid": self.dev_pid})
        if res["err_no"] == 0:
            logger.info(f"{self.SLUG} 语音识别到了：{res['result']}")
            return "".join(res["result"])
        else:
            logger.info(f"{self.SLUG} 语音识别出错了: {res['err_msg']}")
            if res["err_msg"] == "request pv too much":
                logger.info("       出现这个原因很可能是你的百度语音服务调用量超出限制，或未开通付费")
            return ""

class ASROpenAI(ASRBase):
    SLUG ='openai_asr'

    def __init__(self, root_dir, **args):
        super(self.__class__, self).__init__()
        self.model = whisper.load_model(name='base')

    @classmethod
    def get_config(cls):
        # Try to get baidu_yuyin config from config
        return config.get(MODULE, ASROpenAI.SLUG, {})

    def transcribe(self, fp):
        result = self.model.transcribe(fp)
        if result and 'text' in result:
            return result['text']
        return ''

def get_all_engines(cls):
    def get_all_subclass(cls):
        all_subclasses = set()
        for subclass in cls.__subclasses__():
            all_subclasses.add(subclass)
            all_subclasses.update(get_all_subclass(subclass))
        return all_subclasses

    all_engines = get_all_subclass(cls)
    return list(filter(lambda x: hasattr(x, 'SLUG') and x.SLUG, all_engines))

def get_engine_by_slug(slug):
    all_engines = get_all_engines(ASRBase)
    for engine in all_engines:
        if engine.SLUG == slug:
            return engine.get_instance()
    logger.error('No such engine: %s' % slug)
    return None
