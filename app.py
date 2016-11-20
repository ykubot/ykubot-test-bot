from __future__ import unicode_literals

import os
import sys
import random
from argparse import ArgumentParser

from flask import Flask, request, abort, render_template, jsonify, Response
from linebot import (
    LineBotApi, WebhookParser
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
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


@app.route('/')
def index():
    title = "kubot"
    message = "Hello"
    return render_template('index.html',
                           message=message, title=title)


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


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    # if not request.json:
    #     abort(400)

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        # if not isinstance(event, MessageEvent):
        #     continue
        # if not isinstance(event.message, TextMessage):
        #     continue

        # text = event.message.text
        text = create_message(event.message.text)

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text)
        )

    # レスポンスオブジェクトを作る
    response = Response()
    # ステータスコードは NoContent (200)
    response.status_code = 200
    return response
    # return jsonify('OK'), HTTP_200_OK


if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', default=8888, help='port')
    arg_parser.add_argument('-d', '--debug', default=True, help='debug')
    options = arg_parser.parse_args()

    app.run(debug=options.debug, port=options.port)
    # app.run(port = 5000, threaded = True, debug = True)
