#!/usr/bin/env python

import collections
import pyaudio
from . import snowboydetect
import struct
import time
import math
import wave
import os
import logging
from easydict import EasyDict
from ctypes import CFUNCTYPE, c_char_p, c_int, cdll
from contextlib import contextmanager
from robot import constants, utils, config
from robot.logger import getLogger

logger = getLogger("snowboy", level=logging.DEBUG)
TOP_DIR = os.path.dirname(os.path.abspath(__file__))

RESOURCE_FILE = os.path.join(TOP_DIR, "resources/common.res")
DETECT_DING = os.path.join(TOP_DIR, "resources/ding.wav")
DETECT_DONG = os.path.join(TOP_DIR, "resources/dong.wav")

def py_error_handler(filename, line, function, err, fmt):
    pass

ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)

c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)


@contextmanager
def no_alsa_error():
    try:
        asound = cdll.LoadLibrary("libasound.so")
        asound.snd_lib_error_set_handler(c_error_handler)
        yield
        asound.snd_lib_error_set_handler(None)
    except:
        yield
        pass


class RingBuffer(object):
    """Ring buffer to hold audio from PortAudio"""

    def __init__(self, size=4096):
        self._buf = collections.deque(maxlen=size)

    def extend(self, data):
        """Adds data to the end of buffer"""
        self._buf.extend(data)

    def get(self):
        """Retrieves data from the beginning of buffer and clears it"""
        tmp = bytes(bytearray(self._buf))
        self._buf.clear()
        return tmp


def play_audio_file(fname=DETECT_DING):
    """Simple callback function to play a wave file. By default it plays
    a Ding sound.

    :param str fname: wave file name
    :return: None
    """
    ding_wav = wave.open(fname, "rb")
    ding_data = ding_wav.readframes(ding_wav.getnframes())
    with no_alsa_error():
        audio = pyaudio.PyAudio()
    stream_out = audio.open(
        format=audio.get_format_from_width(ding_wav.getsampwidth()),
        channels=ding_wav.getnchannels(),
        rate=ding_wav.getframerate(),
        input=False,
        output=True,
    )
    stream_out.start_stream()
    stream_out.write(ding_data)
    time.sleep(0.2)
    stream_out.stop_stream()
    stream_out.close()
    audio.terminate()

class ActiveListener(object):
    """Active Listening with VAD"""

    def __init__(self, decoder_model, resource=RESOURCE_FILE):
        logger.debug("activeListen __init__()")
        self.recordedData = []
        model_str = ",".join(decoder_model)
        self.detector = snowboydetect.SnowboyDetect(
            resource_filename=resource.encode(), model_str=model_str.encode()
        )
        self.ring_buffer = RingBuffer(
            self.detector.NumChannels() * self.detector.SampleRate() * 5
        )

    def listen(
        self,
        interrupt_check=lambda: False,
        sleep_time=0.03,
        silent_count_threshold=15,
        recording_timeout=100,
    ):
        """
        :param interrupt_check: a function that returns True if the main loop
                                needs to stop.
        :param silent_count_threshold: indicates how long silence must be heard
                                       to mark the end of a phrase that is
                                       being recorded.
        :param float sleep_time: how much time in second every loop waits.
        :param recording_timeout: limits the maximum length of a recording.
        :return: recorded file path
        """
        logger.debug("activeListen listen()")

        self._running = True

        def audio_callback(in_data, frame_count, time_info, status):
            self.ring_buffer.extend(in_data)
            play_data = chr(0) * len(in_data)
            return play_data, pyaudio.paContinue

        with no_alsa_error():
            self.audio = pyaudio.PyAudio()

        logger.debug("opening audio stream")

        try:
            self.stream_in = self.audio.open(
                input=True,
                output=False,
                format=self.audio.get_format_from_width(
                    self.detector.BitsPerSample() / 8
                ),
                channels=self.detector.NumChannels(),
                rate=self.detector.SampleRate(),
                frames_per_buffer=2048,
                stream_callback=audio_callback,
            )
        except Exception as e:
            logger.critical(e, stack_info=True)
            return

        logger.debug("audio stream opened")

        if interrupt_check():
            logger.debug("detect voice return")
            return

        silentCount = 0
        recordingCount = 0

        logger.debug("begin activeListen loop")

        while self._running is True:

            if interrupt_check():
                logger.debug("detect voice break")
                break
            data = self.ring_buffer.get()
            if len(data) == 0:
                time.sleep(sleep_time)
                continue

            status = self.detector.RunDetection(data)
            if status == -1:
                logger.warning("Error initializing streams or reading audio data")

            stopRecording = False
            if recordingCount > recording_timeout:
                stopRecording = True
            elif status == -2:  # silence found
                if silentCount > silent_count_threshold:
                    stopRecording = True
                else:
                    silentCount = silentCount + 1
            elif status == 0:  # voice found
                silentCount = 0

            if stopRecording == True:
                return self.saveMessage()

            recordingCount = recordingCount + 1
            self.recordedData.append(data)

        logger.debug("finished.")

    def saveMessage(self):
        """
        Save the message stored in self.recordedData to a timestamped file.
        """
        filename = os.path.join(
            constants.TEMP_PATH, "output" + str(int(time.time())) + ".wav"
        )
        data = b"".join(self.recordedData)

        # use wave to save data
        wf = wave.open(filename, "wb")
        wf.setnchannels(self.detector.NumChannels())
        wf.setsampwidth(
            self.audio.get_sample_size(
                self.audio.get_format_from_width(self.detector.BitsPerSample() / 8)
            )
        )
        wf.setframerate(self.detector.SampleRate())
        wf.writeframes(data)
        wf.close()
        logger.debug("finished saving: " + filename)

        self.stream_in.stop_stream()
        self.stream_in.close()
        self.audio.terminate()

        return filename

class HotwordDetector(object):
    """
    Snowboy decoder to detect whether a keyword specified by `decoder_model`
    exists in a microphone input stream.

    :param decoder_model: decoder model file path, a string or a list of strings
    :param resource: resource file path.
    :param sensitivity: decoder sensitivity, a float of a list of floats.
                              The bigger the value, the more senstive the
                              decoder. If an empty list is provided, then the
                              default sensitivity in the model will be used.
    :param audio_gain: multiply input volume by this factor.
    :param apply_frontend: applies the frontend processing algorithm if True.
    :param config: config object
    """

    def __init__(
        self, config: EasyDict = {},
        resource: str = RESOURCE_FILE,
    ):
        self._running = False
        self._config = config

        decoder_models = config.modelf
        sensitivity = config.sensitivity
        model_str = ",".join(decoder_models)
        self.detector = snowboydetect.SnowboyDetect(
            resource_filename = resource.encode(),
            model_str = model_str.encode()
        )

        self.detector.SetAudioGain(config.gain)
        self.detector.ApplyFrontend(config.apply_frontend)
        self.num_hotwords = self.detector.NumHotwords()

        if len(decoder_models) > 1 and len(sensitivity) == 1:
            sensitivity = sensitivity * self.num_hotwords
        
        if len(sensitivity) != 0:
            assert self.num_hotwords == len(sensitivity), (
                "number of hotwords in decoder_model (%d) and sensitivity "
                "(%d) does not match" % (self.num_hotwords, len(sensitivity))
            )
        sensitivity_str = ",".join([str(t) for t in sensitivity])
        if len(sensitivity) != 0:
            self.detector.SetSensitivity(sensitivity_str.encode())

        self.ring_buffer = RingBuffer(
            self.detector.NumChannels() * self.detector.SampleRate() * 5
        )

    def start(
        self,
        detected_callback=play_audio_file,
        interrupt_check=lambda: False,
        sleep_time=0.03,
        audio_recorder_callback=None,
    ):
        """
        Start the voice detector. For every `sleep_time` second it checks the
        audio buffer for triggering keywords. If detected, then call
        corresponding function in `detected_callback`, which can be a single
        function (single model) or a list of callback functions (multiple
        models). Every loop it also calls `interrupt_check` -- if it returns
        True, then breaks from the loop and return.

        :param detected_callback: a function or list of functions. The number of
                                  items must match the number of models in
                                  `decoder_model`.
        :param interrupt_check: a function that returns True if the main loop
                                needs to stop.
        :param float sleep_time: how much time in second every loop waits.
        :param audio_recorder_callback: if specified, this will be called after
                                        a keyword has been spoken and after the
                                        phrase immediately after the keyword has
                                        been recorded. The function will be
                                        passed the name of the file where the
                                        phrase was recorded.
        :param silent_count_threshold: indicates how long silence must be heard
                                       to mark the end of a phrase that is
                                       being recorded.
        :param recording_timeout: limits the maximum length of a recording.
        :return: None
        """
        self._running = True
        def audio_callback(in_data, frame_count, time_info, status):
            if utils.isRecordable():
                self.ring_buffer.extend(in_data)
                play_data = chr(0) * len(in_data)
            else:
                play_data = chr(0)
            return play_data, pyaudio.paContinue

        with no_alsa_error():
            self.audio = pyaudio.PyAudio()
        
        self.stream_in = self.audio.open(
            input=True,
            output=False,
            format=self.audio.get_format_from_width(self.detector.BitsPerSample() / 8),
            channels=self.detector.NumChannels(),
            rate=self.detector.SampleRate(),
            frames_per_buffer=self._config.chunk,
            stream_callback=audio_callback,
        )

        if interrupt_check():
            logger.debug("detect voice return")
            return

        tc = type(detected_callback)
        if tc is not list:
            detected_callbacks = [detected_callback]
        else:
            detected_callbacks = detected_callback
        
        if len(detected_callbacks) == 1 and self.num_hotwords > 1:
            detected_callbacks *= self.num_hotwords

        assert self.num_hotwords == len(detected_callbacks), (
            "Error: hotwords in your models (%d) do not match the number of "
            "callbacks (%d)" % (self.num_hotwords, len(detected_callbacks))
        )

        logger.debug("detecting...")

        state = 'PASSIVE'
        voice_detect = 0 # 0: no voice, 1: voice detect; 2: voice end
        while self._running:
            if interrupt_check():
                logger.debug("detect voice break")
                break

            data = self.ring_buffer.get()
            # data = self.stream_in.read(self._config.chunk)
            if len(data) == 0:
                time.sleep(sleep_time)
                continue

            status = self.detector.RunDetection(data)
            if status == -1:
                logger.warning("Error initializing streams or reading audio data")

            # small state machine to handle recording of phrase after keyword
            if state == "PASSIVE":
                if status > 0:  # key word found
                    # self.recordedData.append(data)
                    message = "Keyword " + str(status) + " detected at time: "
                    message += time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.localtime(time.time())
                    )
                    logger.debug(message)
                    callback = detected_callbacks[status - 1]
                    callback and callback()

                    if audio_recorder_callback and status != 0:
                        self.recorded_data = []
                        silent_count = 0
                        state = "ACTIVE"
                        voice_detect = 0
                    continue
            elif state == "ACTIVE":
                chunk = len(data)//2
                nums = struct.unpack('h' * chunk, data)
                rms = math.sqrt(sum([(n**2) for n in nums]) / chunk)

                stop_recording = False
                if voice_detect == 0:
                    if rms > self._config.silence_threshold:
                        logger.debug("voice detect in " + 
                            str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())))
                        )
                        voice_detect = 1
                        self.recorded_data.append(data)
                elif voice_detect == 1:
                    self.recorded_data.append(data)
                    if rms < self._config.silence_threshold:
                        silent_count += 1
                        if silent_count > self._config.silence_time * self._config.rate / self._config.chunk:
                            logger.info("voice end in " + 
                                str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())))
                            )
                            voice_detect = 2
                            stop_recording = True
                
                if stop_recording:
                    fname = self.saveMessage(self.recorded_data, self._config.save_dir)
                    audio_recorder_callback(fname)
                    state = "PASSIVE"
                    voice_detect = 0
                    continue

        logger.debug("finished.")

    def saveMessage(self, frames: list, file_dir: str):
        """
        Save the message stored in self.recordedData to a timestamped file.
        """
        filename = os.path.join(
            file_dir, "output" + str(int(time.time())) + ".wav"
        )
        data = b"".join(frames)

        # use wave to save data
        wf = wave.open(filename, "wb")
        wf.setnchannels(self.detector.NumChannels())
        wf.setsampwidth(
            self.audio.get_sample_size(
                self.audio.get_format_from_width(self.detector.BitsPerSample() / 8)
            )
        )
        wf.setframerate(self.detector.SampleRate())
        wf.writeframes(data)
        wf.close()
        logger.debug("finished saving: " + filename)
        return filename

    def terminate(self):
        """
        Terminate audio stream. Users can call start() again to detect.
        :return: None
        """
        if self._running:
            self.stream_in.stop_stream()
            self.stream_in.close()
            self.audio.terminate()
            self._running = False
