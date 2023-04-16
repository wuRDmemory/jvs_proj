'''
Author: Chenhao Wu wuch2039@163.com
Date: 2023-04-10 19:46:08
LastEditors: Chenhao Wu wuch2039@163.com
LastEditTime: 2023-04-10 20:18:02
FilePath: /jvs_prog/test_openai.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
import openai
import json
import os

openai.proxy = {
    "http": "http://127.0.0.1:12333",
    "https": "http://127.0.0.1:12333",
}
openai.api_key = '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'

q = "帮我打开灯"
rsp = openai.ChatCompletion.create(
  model="gpt-3.5-turbo",
  messages=[
        {"role": "user", "content": q}
    ]
)
print(rsp['choices'][0]['message']['content'])