from flask import Flask, request, abort
import os
import json
import requests

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    FollowEvent, UnfollowEvent, MessageEvent, PostbackEvent,
    TextMessage, TextSendMessage, TemplateSendMessage,
    ButtonsTemplate, CarouselTemplate, CarouselColumn,
    PostbackTemplateAction, FlexSendMessage
)

app = Flask(__name__)

# 環境変数取得
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]
DB_USERNAME = os.environ["DB_USERNAME"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_HOSTNAME = os.environ["DB_HOSTNAME"]
DB_NAME = os.environ["DB_NAME"]

DB_TABLE = "linedata"

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = event.message.text
    if "おはよう" in message:
        reply = "おはようございます！"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply))
    elif "こんにちは" in message:
        reply = "こんにちは！"
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=reply))
    elif "こんばんは" in message:
        reply = "こんばんは！"
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=reply))
    elif "時間割" in message:
        if "今日" in message:
            reply = "今日の時間割"
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text=reply))
        elif "明日" in message:
            reply = "明日の時間割"
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text=reply))
        else:
            reply = "いつの時間割を返信するか送ってください！\n例：「今日の時間割」"
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text=reply))
    elif "天気" in message:
        if "今日" in message:
            json_open = requests.get(
                'http://api.openweathermap.org/data/2.5/onecall?lat=34.440051&lon=135.373055&lang=ja&units=metric&exclude={current,minutely,hourly,alerts}&appid=87224c26fda90becf7d1a263ced5a5b3')
            json_load = json_open.json()
            reply = {"type": "flex",
                     "altText": "山形未歩さんを応援しよう！",
                     "contents": {
                         "type": "bubble",
                         "header": {
                             "type": "box",
                             "layout": "vertical",
                             "contents": [
                                 {
                                     "type": "text",
                                     "text": "山形未歩さんを応援しよう！",
                                     "decoration": "none",
                                     "align": "center",
                                     "size": "lg",
                                     "margin": "none",
                                     "weight": "bold"
                                 }
                             ]
                         },
                         "hero": {
                             "type": "image",
                             "url": "https://bpf.tabippo.net/2021/wp-content/uploads/2020/11/%E5%B1%B1%E5%BD%A2%EF%BC%91.jpeg",
                             "size": "full"
                         },
                         "body": {
                             "type": "box",
                             "layout": "vertical",
                             "contents": [
                                 {
                                     "type": "text",
                                     "text": "英語科 磯田先生の教え子，山形未歩さんがSHINEという世界を旅する女子が輝くコンテストに出場しています。書類審査，グループディスカッションを突破した山形さんは，現在，3rdステージのWeb投票に挑戦しています。11/26まで1日1回投票できます。ぜひ投票しましょう！",
                                     "wrap": True,
                                     "size": "sm"
                                 }
                             ]
                         },
                         "footer": {
                             "type": "box",
                             "layout": "vertical",
                             "contents": [
                                 {
                                     "type": "button",
                                     "action": {
                                         "type": "uri",
                                         "label": "投票ページに移動",
                                         "uri": "https://bpf.tabippo.net/2021/shine/b-59/"
                                     }
                                 },
                                 {
                                     "type": "text",
                                     "text": "＊「今日の時間割」のときのみ，時間割と同時にこのメッセージを送っています。",
                                     "wrap": True,
                                     "size": "xs"
                                 }
                             ]
                         },
                         "styles": {
                             "header": {
                                 "backgroundColor": "#F9D959"
                             },
                             "hero": {
                                 "separator": False
                             }
                         }
                     }
                     }
            """ reply = {
                "type": "flex",
                "altText": "今日の天気" + "：" + json_load['daily'][0]['weather'][0]['description'],
                "contents": {
                        "type": "bubble",
                        "header": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "今日の天気",
                                    "color": "#FFFFFF",
                                    "margin": "none",
                                    "weight": "bold",
                                    "gravity": "center",
                                    "size": "xl"
                                }
                            ],
                            "backgroundColor": "#3cb371",
                            "margin": "none"
                        },
                    "body": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "box",
                                    "layout": "horizontal",
                                    "contents": [
                                        {
                                            "type": "box",
                                            "layout": "vertical",
                                            "contents": [
                                                {
                                                    "type": "box",
                                                    "layout": "vertical",
                                                    "contents": [
                                                        {
                                                            "type": "image",
                                                            "url": "http://openweathermap.org/img/wn/" + json_load['daily'][0]['weather'][0]['icon'] + "@2x.png",
                                                            "size": "md",
                                                            "aspectRatio": "2:1"
                                                        }
                                                    ]
                                                },
                                                {
                                                    "type": "box",
                                                    "layout": "vertical",
                                                    "contents": [
                                                        {
                                                            "type": "text",
                                                            "text": json_load['daily'][0]['weather'][0]['description'],
                                                            "align": "center"
                                                        }
                                                    ]
                                                }
                                            ]
                                        },
                                        {
                                            "type": "box",
                                            "layout": "vertical",
                                            "contents": [
                                                {
                                                    "type": "spacer",
                                                    "size": "md"
                                                },
                                                {
                                                    "type": "text",
                                                    "text": str(json_load['daily'][0]['temp']['max']) + "℃",
                                                    "size": "xl",
                                                    "color": "#ff6347"
                                                },
                                                {
                                                    "type": "text",
                                                    "text": str(json_load['daily'][0]['temp']['min']) + "℃",
                                                    "size": "xl",
                                                    "color": "#4169e1"
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                    }
                }
            } """
            container_obj = FlexSendMessage.new_from_json_dict(reply)
            line_bot_api.reply_message(
                event.reply_token, messages=container_obj)
        elif "明日" in message:
            json_open = requests.get(
                'http://api.openweathermap.org/data/2.5/onecall?lat=34.440051&lon=135.373055&lang=ja&units=metric&exclude={current,minutely,hourly,alerts}&appid=87224c26fda90becf7d1a263ced5a5b3')
            json_load = json_open.json()
            tdat = json_load['daily'][1]['weather'][0]['description']
            reply = tdat
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text=reply))
        else:
            reply = "いつの天気を返信するか送ってください！\n例：「今日の天気」"
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text=reply))
    elif "運行情報" in message:
        reply = "運行情報"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply))
    elif "設定" in message:
        reply = "設定画面を開きません。"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply))
    else:
        reply = message
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply))

# Follow Event


@handler.add(FollowEvent)
def on_follow(event):
    reply_token = event.reply_token
    user_id = event.source.user_id
    profiles = line_bot_api.get_profile(user_id=user_id)
    display_name = profiles.display_name
    picture_url = profiles.picture_url
    status_message = profiles.status_message

    # メッセージの送信
    line_bot_api.reply_message(
        reply_token=reply_token,
        messages=TextSendMessage(
            text=display_name + "さん、当アカウントの友達登録ありがとうございます！\n\n【当アカウントの利用方法】\n「今日の時間割」と送信すると時間割設定画面で設定された時間割を返信します。")
    )


if __name__ == "__main__":
    #    app.run()
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)
