'''
Author: wuRDmemory wuch2039@163.com
Date: 2023-03-29 21:15:13
LastEditors: wuRDmemory wuch2039@163.com
LastEditTime: 2023-03-29 22:02:16
FilePath: /jvs_prog/recorder.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
import wave
import pyaudio
import struct
import math
from robot.logger import getLogger

logger = getLogger(__name__)

# Define stream parameters
CHUNK = 1024  # number of audio samples per frame
FORMAT = pyaudio.paInt16  # audio format
CHANNELS = 1  # mono audio
RATE = 16000  # sample rate
SLIENCE_TIME = 4  # time of silence to stop recording

# Define threshold for detecting human voice
THRESHOLD = 1500

def recode_voice(file_path):
    # Create PyAudio object
    p = pyaudio.PyAudio()

    # Open audio stream
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    logger.info("[Recorder] Recording...")

    # Loop until human voice is detected
    frames = []
    slience_count = 0
    status = 0 # 0: no voice, 1: voice detected; 2: voice end
    while status != 2:
        # Read audio data from microphone
        data = stream.read(CHUNK)
        
        # Convert audio data to numbers
        nums = struct.unpack('h' * CHUNK, data)
        
        # Calculate root mean square (RMS) amplitude of audio data
        rms = math.sqrt(sum([(n**2) for n in nums]) / CHUNK)
        
        # Check if RMS amplitude is above threshold
        if status == 0:
            if rms > THRESHOLD:
                logger.info("[Recorder] Human voice detected!")
                status = 1
        elif status == 1:
            frames.append(data)
            if rms < THRESHOLD:
                slience_count += 1
                if slience_count > SLIENCE_TIME * RATE / CHUNK:
                    logger.info("[Recorder] Recording finish...")
                    status = 2
            else:
                slience_count = 0

    # Stop audio stream
    stream.stop_stream()
    stream.close()

    # Terminate PyAudio object
    p.terminate()

    # Save the audio to a WAV file
    wave_file = wave.open(file_path, 'wb')
    wave_file.setnchannels(CHANNELS)
    wave_file.setsampwidth(p.get_sample_size(FORMAT))
    wave_file.setframerate(RATE)
    wave_file.writeframes(b''.join(frames))
    wave_file.close()
    
    logger.info("[Recorder] Wav file in {}".format(file_path))