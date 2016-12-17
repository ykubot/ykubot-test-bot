from __future__ import unicode_literals

import http
import json
import math
import os
import sys
import random
from argparse import ArgumentParser

from flask import Flask, request, abort, render_template, Response
from linebot import (
    LineBotApi, WebhookParser
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageMessage
)

app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)

if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)

# Set Microsoft cognitive api key
with open('api_key.txt', 'r') as f:
    api_key = f.read().rstrip('\n')


@app.route('/')
def index():
    title = "kubot"
    message = "Hello"
    return render_template('index.html',
                           message=message, title=title)


def get_ms_header(key):
    headers = {
        'Content-Type': 'application/octet-stream',
        'Ocp-Apim-Subscription-Key': key,
    }
    return headers


def get_emotion(binary_file, header):
    try:
        conn = http.client.HTTPSConnection('api.projectoxford.ai')
        conn.request("POST", "/emotion/v1.0/recognize?", binary_file, header)
        response = conn.getresponse()
        response_data = response.read()
        json_data = json.loads(response_data.decode('utf-8'))
        conn.close()
        return json_data

    except Exception as e:
        print(e)


def float_format(num):
    return '%.6f' % num


def my_round(num, d=0):
    p = 10 ** d
    return float(math.floor((num * p) + math.copysign(0.5, num))) / p


def create_message(text):
    messages = ['今でしょ！',
                '・・・',
                'せやろか？',
                'せやな^^',
                'なんでやねん笑',
                'それな',
                'あー、ね',
                'マジでか',
                'w',
                'ww',
                'www',
                'からの〜',
                'て、思うやん？']
    if '？' in text:
        return 'ちょっと何言ってるかわからないです'
    elif '今でしょ' in text:
        return 'まだでしょ！'
    else:
        return messages[random.randint(0, len(messages))]


def create_emotion_message(data):
    for face in data:
        face_scores = face['scores']
        face_surprise = float_format(face_scores['surprise'])
        face_contempt = float_format(face_scores['contempt'])
        face_disgust = float_format(face_scores['disgust'])
        face_fear = float_format(face_scores['fear'])
        face_neutral = float_format(face_scores['neutral'])
        face_anger = float_format(face_scores['anger'])
        face_happiness = float_format(my_round(face_scores['happiness'], 6))
        face_sadness = float_format(face_scores['sadness'])
        print('Surprise: ', face_surprise)
        print('Contempt: ', face_contempt)
        print('Disgust: ', face_disgust)
        print('Fear: ', face_fear)
        print('Neutral: ', face_neutral)
        print('Anger: ', face_anger)
        print('Happiness: ', face_happiness)
        print('Sadness: ', face_sadness)
        text = '驚き:' + face_surprise + '\n'
        text += '軽蔑:' + face_contempt + '\n'
        text += 'いらいら:' + face_disgust + '\n'
        text += '恐怖:' + face_fear + '\n'
        text += '素:' + face_neutral + '\n'
        text += '怒り:' + face_anger + '\n'
        text += '喜び:' + face_happiness + '\n'
        text += '悲しみ:' + face_sadness + '\n'
    return text

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    if not request.json:
        abort(400)

    # get request body as text
    body = request.get_data(as_text=True)

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)
    # print(events)

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if isinstance(event.message, TextMessage):
            # text = event.message.text
            text = create_message(event.message.text)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text)
            )
        if isinstance(event.message, ImageMessage):
            # Get image content
            message_content = line_bot_api.get_message_content(event.message.id)
            # with open(file_path, 'wb') as fd:
            #     for chunk in message_content.iter_content():
            #         fd.write(chunk)

            data = get_emotion(message_content.content, get_ms_header(api_key))
            print(data)
            text = create_emotion_message(data)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text)
            )

        # print(event.source.userId)
        # profile = line_bot_api.get_profile(event.source.userId)
        # print(profile.display_name)
        # print(profile.user_id)
        # print(profile.picture_url)
        # print(profile.status_message)

    # レスポンスオブジェクトを作る
    response = Response()
    # ステータスコードは NoContent (200)
    response.status_code = 200
    return response


if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', default=8888, help='port')
    arg_parser.add_argument('-d', '--debug', default=True, help='debug')
    options = arg_parser.parse_args()

    app.run(debug=options.debug, port=options.port)
