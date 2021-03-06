from flask import Flask, request, abort, render_template, redirect, session
import os
import json
import requests
import datetime
import pytz
import urllib.request
from urllib.parse import urlencode
import random
import string
import pprint
import psycopg2

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    SourceUser, SourceGroup, SourceRoom,
    TemplateSendMessage, ConfirmTemplate, MessageAction,
    ButtonsTemplate, ImageCarouselTemplate, ImageCarouselColumn, URIAction,
    PostbackAction, DatetimePickerAction,
    CameraAction, CameraRollAction, LocationAction,
    CarouselTemplate, CarouselColumn, PostbackEvent,
    StickerMessage, StickerSendMessage, LocationMessage, LocationSendMessage,
    ImageMessage, VideoMessage, AudioMessage, FileMessage,
    UnfollowEvent, FollowEvent, JoinEvent, LeaveEvent, BeaconEvent,
    FlexSendMessage, BubbleContainer, ImageComponent, BoxComponent,
    TextComponent, IconComponent, ButtonComponent,
    SeparatorComponent, QuickReply, QuickReplyButton, RichMenu, RichMenuArea, RichMenuBounds, RichMenuSize
)

app = Flask(__name__)
app.secret_key = "zVoYisWmTe"

# 環境変数取得
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]
DB_USERNAME = os.environ["DB_USERNAME"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_HOSTNAME = os.environ["DB_HOSTNAME"]
DB_NAME = os.environ["DB_NAME"]
DB_TABLE = "line_data"
ADMIN_UID = os.environ["ADMIN_UID"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)


@app.route("/login")
def login():
    statenumber = ''.join(
        [random.choice(string.ascii_letters + string.digits) for i in range(10)])
    return redirect("https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id=1655825338&redirect_uri=https://university-life-useful-bot.herokuapp.com/post&state=" + statenumber + "&scope=profile%20openid&disable_ios_auto_login=true")


@app.route("/post")
def post():
    code = request.args.get('code', '')
    state = request.args.get('state', '')
    response = requests.post('https://api.line.me/oauth2/v2.1/token', data={'grant_type': 'authorization_code', 'code': code,
                             'redirect_uri': 'https://university-life-useful-bot.herokuapp.com/post', 'client_id': '1655825338', 'client_secret': '23252a4f6b865a32a80427f71e89fe53'})
    if response.status_code == 200:
        response_json = response.json()
        id_token = response_json["id_token"]
        response2 = requests.post('https://api.line.me/oauth2/v2.1/verify', data={
                                  'id_token': id_token, 'client_id': '1655825338'})
        if response2.status_code == 200:
            response2_json = response2.json()
            session["flag"] = True
            session["uid"] = response2_json["sub"]
            session["name"] = response2_json["name"]
            session["picture"] = response2_json["picture"]
            return redirect("https://university-life-useful-bot.herokuapp.com/edit")
        else:
            return 'エラー'
    else:
        return 'エラー'


@app.route("/edit")
def edit():
    if "flag" in session and session["flag"]:
        con = psycopg2.connect("host=" + DB_HOSTNAME +
                               " port=" + "5432" +
                               " dbname=" + DB_NAME +
                               " user=" + DB_USERNAME +
                               " password=" + DB_PASSWORD)
        sql = 'select * from ' + DB_TABLE
        with con.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
        for r in rows:
            if r[0] == session["uid"]:
                result = []
                for s in r:
                    result.append(s)
                result[1] = session["name"]
                return render_template("edit.html", user_data=result)
                break
        else:
            result = []
            for s in range(0,116,1):
                result.append('')
            result[0] = session["uid"]
            result[1] = session["name"]
            return render_template("edit.html", user_data=result)
    else:
        return "ログインしてください。"


@app.route("/submit", methods=['POST'])
def submit():
    con = psycopg2.connect("host=" + DB_HOSTNAME +
                           " port=" + "5432" +
                           " dbname=" + DB_NAME +
                           " user=" + DB_USERNAME +
                           " password=" + DB_PASSWORD)
    sql = 'select * from ' + DB_TABLE
    with con.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()
        for r in rows:
            if r[0] == session["uid"]:
                sql = "UPDATE " + DB_TABLE + " SET name= '" + session["name"]
                for i in range(1, 36, 1):
                    id_name = "',tt" + str(i) + "_name= '"
                    id_teacher = "',tt" + str(i) + "_teacher= '"
                    id_room = "',tt" + str(i) + "_room= '"
                    sql += id_name + request.form["tt" + str(i) + "_name"] + id_teacher + request.form["tt" + str(
                        i) + "_teacher"] + id_room + request.form["tt" + str(i) + "_room"]
                sql += "'WHERE uid = '" + session["uid"] + "'"
                cur.execute(sql)
                con.commit()
                return session["name"] + "の設定を保存しました。"
                break
        else:
            sql = "INSERT INTO " + DB_TABLE + " VALUES ('" + session["uid"] + "','" + session["name"] + "','','','','','','','','"
            for i in range(1, 36, 1):
                sql += "','" + request.form["tt" + str(i) + "_name"] + "','" + request.form["tt" + str(
                    i) + "_teacher"] + "','" + request.form["tt" + str(i) + "_room"] + ")"
            cur.execute(sql)
            con.commit()
            return session["name"] + "の設定を保存しました。"


@app.route("/admin")
def admin():
    if session["uid"] == ADMIN_UID:
        con = psycopg2.connect("host=" + DB_HOSTNAME +
                               " port=" + "5432" +
                               " dbname=" + DB_NAME +
                               " user=" + DB_USERNAME +
                               " password=" + DB_PASSWORD)
        sql = 'select * from ' + DB_TABLE
        with con.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            return render_template("admin.html", user_data=rows)


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
            con = psycopg2.connect("host=" + DB_HOSTNAME +
                                   " port=" + "5432" +
                                   " dbname=" + DB_NAME +
                                   " user=" + DB_USERNAME +
                                   " password=" + DB_PASSWORD)
            sql = 'select * from ' + DB_TABLE
            with con.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()
                now = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
                weekday = now.weekday()
                reply = {
                    "type": "flex",
                            "altText": "今日の時間割",
                            "contents": {
                                "type": "bubble",
                                "header": {
                                    "type": "box",
                                    "layout": "vertical",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": "今日の時間割",
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
                                    ]
                                }
                            }
                }
                if weekday == 0:
                    for r in rows:
                        if r[0] == event.source.user_id:
                            result = []
                            for s in range(10, 25):
                                if r[s] is None:
                                    result.append('')
                                else:
                                    result.append(r[s])
                            result.append(0)
                            if result:
                                if result[15] == 0:  # 科目名のみモード
                                    i = 1
                                    for t in range(0, 13, 3):
                                        if result[t] == '':
                                            i += 1
                                            continue
                                        else:
                                            reply["contents"]["body"]["contents"].append({
                                                "type": "box",
                                                "layout": "horizontal",
                                                "contents": [
                                                    {
                                                        "type": "text",
                                                        "text": str(i) + "限：",
                                                        "margin": "sm",
                                                        "flex": 1
                                                    },
                                                    {
                                                        "type": "text",
                                                        "text": result[t],
                                                        "wrap": True,
                                                        "flex": 4
                                                    }
                                                ]
                                            })
                                            i += 1
                                    container_obj = FlexSendMessage.new_from_json_dict(
                                        reply)
                                    line_bot_api.reply_message(
                                        event.reply_token, messages=container_obj)
                                elif result[14] == 1:  # 科目名・担当者名・教室名全部入りモード
                                    i = 1
                                    for t in range(0, 14, 3):
                                        if result[t] == '':
                                            i += 1
                                            continue
                                        else:

                                            i += 1
                            break
                if weekday == 1:
                    for r in rows:
                        if r[0] == event.source.user_id:
                            result = []
                            for s in range(25, 40):
                                if r[s] is None:
                                    result.append('')
                                else:
                                    result.append(r[s])
                            result.append(0)
                            if result:
                                if result[15] == 0:  # 科目名のみモード
                                    i = 1
                                    for t in range(0, 13, 3):
                                        if result[t] == '':
                                            i += 1
                                            continue
                                        else:
                                            reply["contents"]["body"]["contents"].append({
                                                "type": "box",
                                                "layout": "horizontal",
                                                "contents": [
                                                    {
                                                        "type": "text",
                                                        "text": str(i) + "限：",
                                                        "margin": "sm",
                                                        "flex": 1
                                                    },
                                                    {
                                                        "type": "text",
                                                        "text": result[t],
                                                        "wrap": True,
                                                        "flex": 4
                                                    }
                                                ]
                                            })
                                            i += 1
                                    container_obj = FlexSendMessage.new_from_json_dict(
                                        reply)
                                    line_bot_api.reply_message(
                                        event.reply_token, messages=container_obj)
                                elif result[14] == 1:  # 科目名・担当者名・教室名全部入りモード
                                    i = 1
                                    for t in range(0, 14, 3):
                                        if result[t] == '':
                                            i += 1
                                            continue
                                        else:

                                            i += 1
                            break
                if weekday == 2:
                    for r in rows:
                        if r[0] == event.source.user_id:
                            result = []
                            for s in range(40, 55):
                                if r[s] is None:
                                    result.append('')
                                else:
                                    result.append(r[s])
                            result.append(0)
                            if result:
                                if result[15] == 0:  # 科目名のみモード
                                    i = 1
                                    for t in range(0, 13, 3):
                                        if result[t] == '':
                                            i += 1
                                            continue
                                        else:
                                            reply["contents"]["body"]["contents"].append({
                                                "type": "box",
                                                "layout": "horizontal",
                                                "contents": [
                                                    {
                                                        "type": "text",
                                                        "text": str(i) + "限：",
                                                        "margin": "sm",
                                                        "flex": 1
                                                    },
                                                    {
                                                        "type": "text",
                                                        "text": result[t],
                                                        "wrap": True,
                                                        "flex": 4
                                                    }
                                                ]
                                            })
                                            i += 1
                                    container_obj = FlexSendMessage.new_from_json_dict(
                                        reply)
                                    line_bot_api.reply_message(
                                        event.reply_token, messages=container_obj)
                                elif result[14] == 1:  # 科目名・担当者名・教室名全部入りモード
                                    i = 1
                                    for t in range(0, 14, 3):
                                        if result[t] == '':
                                            i += 1
                                            continue
                                        else:

                                            i += 1
                            break
                if weekday == 3:
                    for r in rows:
                        if r[0] == event.source.user_id:
                            result = []
                            for s in range(55, 70):
                                if r[s] is None:
                                    result.append('')
                                else:
                                    result.append(r[s])
                            result.append(0)
                            if result:
                                if result[15] == 0:  # 科目名のみモード
                                    i = 1
                                    for t in range(0, 13, 3):
                                        if result[t] == '':
                                            i += 1
                                            continue
                                        else:
                                            reply["contents"]["body"]["contents"].append({
                                                "type": "box",
                                                "layout": "horizontal",
                                                "contents": [
                                                    {
                                                        "type": "text",
                                                        "text": str(i) + "限：",
                                                        "margin": "sm",
                                                        "flex": 1
                                                    },
                                                    {
                                                        "type": "text",
                                                        "text": result[t],
                                                        "wrap": True,
                                                        "flex": 4
                                                    }
                                                ]
                                            })
                                            i += 1
                                    container_obj = FlexSendMessage.new_from_json_dict(
                                        reply)
                                    line_bot_api.reply_message(
                                        event.reply_token, messages=container_obj)
                                elif result[14] == 1:  # 科目名・担当者名・教室名全部入りモード
                                    i = 1
                                    for t in range(0, 14, 3):
                                        if result[t] == '':
                                            i += 1
                                            continue
                                        else:

                                            i += 1
                            break
                if weekday == 4:
                    for r in rows:
                        if r[0] == event.source.user_id:
                            result = []
                            for s in range(70, 85):
                                if r[s] is None:
                                    result.append('')
                                else:
                                    result.append(r[s])
                            result.append(0)
                            if result:
                                if result[15] == 0:  # 科目名のみモード
                                    i = 1
                                    for t in range(0, 13, 3):
                                        if result[t] == '':
                                            i += 1
                                            continue
                                        else:
                                            reply["contents"]["body"]["contents"].append({
                                                "type": "box",
                                                "layout": "horizontal",
                                                "contents": [
                                                    {
                                                        "type": "text",
                                                        "text": str(i) + "限：",
                                                        "margin": "sm",
                                                        "flex": 1
                                                    },
                                                    {
                                                        "type": "text",
                                                        "text": result[t],
                                                        "wrap": True,
                                                        "flex": 4
                                                    }
                                                ]
                                            })
                                            i += 1
                                    container_obj = FlexSendMessage.new_from_json_dict(
                                        reply)
                                    line_bot_api.reply_message(
                                        event.reply_token, messages=container_obj)
                                elif result[14] == 1:  # 科目名・担当者名・教室名全部入りモード
                                    i = 1
                                    for t in range(0, 14, 3):
                                        if result[t] == '':
                                            i += 1
                                            continue
                                        else:

                                            i += 1
                            break
                if weekday == 5:
                    for r in rows:
                        if r[0] == event.source.user_id:
                            result = []
                            for s in range(85, 100):
                                if r[s] is None:
                                    result.append('')
                                else:
                                    result.append(r[s])
                            result.append(0)
                            if result:
                                if result[15] == 0:  # 科目名のみモード
                                    i = 1
                                    for t in range(0, 13, 3):
                                        if result[t] == '':
                                            i += 1
                                            continue
                                        else:
                                            reply["contents"]["body"]["contents"].append({
                                                "type": "box",
                                                "layout": "horizontal",
                                                "contents": [
                                                    {
                                                        "type": "text",
                                                        "text": str(i) + "限：",
                                                        "margin": "sm",
                                                        "flex": 1
                                                    },
                                                    {
                                                        "type": "text",
                                                        "text": result[t],
                                                        "wrap": True,
                                                        "flex": 4
                                                    }
                                                ]
                                            })
                                            i += 1
                                    container_obj = FlexSendMessage.new_from_json_dict(
                                        reply)
                                    line_bot_api.reply_message(
                                        event.reply_token, messages=container_obj)
                                elif result[14] == 1:  # 科目名・担当者名・教室名全部入りモード
                                    i = 1
                                    for t in range(0, 14, 3):
                                        if result[t] == '':
                                            i += 1
                                            continue
                                        else:

                                            i += 1
                            break
                if weekday == 6:
                    for r in rows:
                        if r[0] == event.source.user_id:
                            result = []
                            for s in range(100, 115):
                                if r[s] is None:
                                    result.append('')
                                else:
                                    result.append(r[s])
                            result.append(0)
                            if result:
                                if result[15] == 0:  # 科目名のみモード
                                    i = 1
                                    for t in range(0, 13, 3):
                                        if result[t] == '':
                                            i += 1
                                            continue
                                        else:
                                            reply["contents"]["body"]["contents"].append({
                                                "type": "box",
                                                "layout": "horizontal",
                                                "contents": [
                                                    {
                                                        "type": "text",
                                                        "text": str(i) + "限：",
                                                        "margin": "sm",
                                                        "flex": 1
                                                    },
                                                    {
                                                        "type": "text",
                                                        "text": result[t],
                                                        "wrap": True,
                                                        "flex": 4
                                                    }
                                                ]
                                            })
                                            i += 1
                                    container_obj = FlexSendMessage.new_from_json_dict(
                                        reply)
                                    line_bot_api.reply_message(
                                        event.reply_token, messages=container_obj)
                                elif result[14] == 1:  # 科目名・担当者名・教室名全部入りモード
                                    i = 1
                                    for t in range(0, 14, 3):
                                        if result[t] == '':
                                            i += 1
                                            continue
                                        else:

                                            i += 1
                            break
        elif "明日" in message:
            con = psycopg2.connect("host=" + DB_HOSTNAME +
                                   " port=" + "5432" +
                                   " dbname=" + DB_NAME +
                                   " user=" + DB_USERNAME +
                                   " password=" + DB_PASSWORD)
            sql = 'select * from ' + DB_TABLE
            with con.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()
                now = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
                weekday = now.weekday() + 1
                reply = {
                    "type": "flex",
                            "altText": "明日の時間割",
                            "contents": {
                                "type": "bubble",
                                "header": {
                                    "type": "box",
                                    "layout": "vertical",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": "明日の時間割",
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
                                    ]
                                }
                            }
                }
                if weekday == 7:
                    for r in rows:
                        if r[0] == event.source.user_id:
                            result = []
                            for s in range(10, 25):
                                if r[s] is None:
                                    result.append('')
                                else:
                                    result.append(r[s])
                            result.append(0)
                            if result:
                                if result[15] == 0:  # 科目名のみモード
                                    i = 1
                                    for t in range(0, 13, 3):
                                        if result[t] == '':
                                            i += 1
                                            continue
                                        else:
                                            reply["contents"]["body"]["contents"].append({
                                                "type": "box",
                                                "layout": "horizontal",
                                                "contents": [
                                                    {
                                                        "type": "text",
                                                        "text": str(i) + "限：",
                                                        "margin": "sm",
                                                        "flex": 1
                                                    },
                                                    {
                                                        "type": "text",
                                                        "text": result[t],
                                                        "wrap": True,
                                                        "flex": 4
                                                    }
                                                ]
                                            })
                                            i += 1
                                    container_obj = FlexSendMessage.new_from_json_dict(
                                        reply)
                                    line_bot_api.reply_message(
                                        event.reply_token, messages=container_obj)
                                elif result[14] == 1:  # 科目名・担当者名・教室名全部入りモード
                                    i = 1
                                    for t in range(0, 14, 3):
                                        if result[t] == '':
                                            i += 1
                                            continue
                                        else:

                                            i += 1
                            break
                if weekday == 1:
                    for r in rows:
                        if r[0] == event.source.user_id:
                            result = []
                            for s in range(25, 40):
                                if r[s] is None:
                                    result.append('')
                                else:
                                    result.append(r[s])
                            result.append(0)
                            if result:
                                if result[15] == 0:  # 科目名のみモード
                                    i = 1
                                    for t in range(0, 13, 3):
                                        if result[t] == '':
                                            i += 1
                                            continue
                                        else:
                                            reply["contents"]["body"]["contents"].append({
                                                "type": "box",
                                                "layout": "horizontal",
                                                "contents": [
                                                    {
                                                        "type": "text",
                                                        "text": str(i) + "限：",
                                                        "margin": "sm",
                                                        "flex": 1
                                                    },
                                                    {
                                                        "type": "text",
                                                        "text": result[t],
                                                        "wrap": True,
                                                        "flex": 4
                                                    }
                                                ]
                                            })
                                            i += 1
                                    container_obj = FlexSendMessage.new_from_json_dict(
                                        reply)
                                    line_bot_api.reply_message(
                                        event.reply_token, messages=container_obj)
                                elif result[14] == 1:  # 科目名・担当者名・教室名全部入りモード
                                    i = 1
                                    for t in range(0, 14, 3):
                                        if result[t] == '':
                                            i += 1
                                            continue
                                        else:

                                            i += 1
                            break
                if weekday == 2:
                    for r in rows:
                        if r[0] == event.source.user_id:
                            result = []
                            for s in range(40, 55):
                                if r[s] is None:
                                    result.append('')
                                else:
                                    result.append(r[s])
                            result.append(0)
                            if result:
                                if result[15] == 0:  # 科目名のみモード
                                    i = 1
                                    for t in range(0, 13, 3):
                                        if result[t] == '':
                                            i += 1
                                            continue
                                        else:
                                            reply["contents"]["body"]["contents"].append({
                                                "type": "box",
                                                "layout": "horizontal",
                                                "contents": [
                                                    {
                                                        "type": "text",
                                                        "text": str(i) + "限：",
                                                        "margin": "sm",
                                                        "flex": 1
                                                    },
                                                    {
                                                        "type": "text",
                                                        "text": result[t],
                                                        "wrap": True,
                                                        "flex": 4
                                                    }
                                                ]
                                            })
                                            i += 1
                                    container_obj = FlexSendMessage.new_from_json_dict(
                                        reply)
                                    line_bot_api.reply_message(
                                        event.reply_token, messages=container_obj)
                                elif result[14] == 1:  # 科目名・担当者名・教室名全部入りモード
                                    i = 1
                                    for t in range(0, 14, 3):
                                        if result[t] == '':
                                            i += 1
                                            continue
                                        else:

                                            i += 1
                            break
                if weekday == 3:
                    for r in rows:
                        if r[0] == event.source.user_id:
                            result = []
                            for s in range(55, 70):
                                if r[s] is None:
                                    result.append('')
                                else:
                                    result.append(r[s])
                            result.append(0)
                            if result:
                                if result[15] == 0:  # 科目名のみモード
                                    i = 1
                                    for t in range(0, 13, 3):
                                        if result[t] == '':
                                            i += 1
                                            continue
                                        else:
                                            reply["contents"]["body"]["contents"].append({
                                                "type": "box",
                                                "layout": "horizontal",
                                                "contents": [
                                                    {
                                                        "type": "text",
                                                        "text": str(i) + "限：",
                                                        "margin": "sm",
                                                        "flex": 1
                                                    },
                                                    {
                                                        "type": "text",
                                                        "text": result[t],
                                                        "wrap": True,
                                                        "flex": 4
                                                    }
                                                ]
                                            })
                                            i += 1
                                    container_obj = FlexSendMessage.new_from_json_dict(
                                        reply)
                                    line_bot_api.reply_message(
                                        event.reply_token, messages=container_obj)
                                elif result[14] == 1:  # 科目名・担当者名・教室名全部入りモード
                                    i = 1
                                    for t in range(0, 14, 3):
                                        if result[t] == '':
                                            i += 1
                                            continue
                                        else:

                                            i += 1
                            break
                if weekday == 4:
                    for r in rows:
                        if r[0] == event.source.user_id:
                            result = []
                            for s in range(70, 85):
                                if r[s] is None:
                                    result.append('')
                                else:
                                    result.append(r[s])
                            result.append(0)
                            if result:
                                if result[15] == 0:  # 科目名のみモード
                                    i = 1
                                    for t in range(0, 13, 3):
                                        if result[t] == '':
                                            i += 1
                                            continue
                                        else:
                                            reply["contents"]["body"]["contents"].append({
                                                "type": "box",
                                                "layout": "horizontal",
                                                "contents": [
                                                    {
                                                        "type": "text",
                                                        "text": str(i) + "限：",
                                                        "margin": "sm",
                                                        "flex": 1
                                                    },
                                                    {
                                                        "type": "text",
                                                        "text": result[t],
                                                        "wrap": True,
                                                        "flex": 4
                                                    }
                                                ]
                                            })
                                            i += 1
                                    container_obj = FlexSendMessage.new_from_json_dict(
                                        reply)
                                    line_bot_api.reply_message(
                                        event.reply_token, messages=container_obj)
                                elif result[14] == 1:  # 科目名・担当者名・教室名全部入りモード
                                    i = 1
                                    for t in range(0, 14, 3):
                                        if result[t] == '':
                                            i += 1
                                            continue
                                        else:

                                            i += 1
                            break
                if weekday == 5:
                    for r in rows:
                        if r[0] == event.source.user_id:
                            result = []
                            for s in range(85, 100):
                                if r[s] is None:
                                    result.append('')
                                else:
                                    result.append(r[s])
                            result.append(0)
                            if result:
                                if result[15] == 0:  # 科目名のみモード
                                    i = 1
                                    for t in range(0, 13, 3):
                                        if result[t] == '':
                                            i += 1
                                            continue
                                        else:
                                            reply["contents"]["body"]["contents"].append({
                                                "type": "box",
                                                "layout": "horizontal",
                                                "contents": [
                                                    {
                                                        "type": "text",
                                                        "text": str(i) + "限：",
                                                        "margin": "sm",
                                                        "flex": 1
                                                    },
                                                    {
                                                        "type": "text",
                                                        "text": result[t],
                                                        "wrap": True,
                                                        "flex": 4
                                                    }
                                                ]
                                            })
                                            i += 1
                                    container_obj = FlexSendMessage.new_from_json_dict(
                                        reply)
                                    line_bot_api.reply_message(
                                        event.reply_token, messages=container_obj)
                                elif result[14] == 1:  # 科目名・担当者名・教室名全部入りモード
                                    i = 1
                                    for t in range(0, 14, 3):
                                        if result[t] == '':
                                            i += 1
                                            continue
                                        else:

                                            i += 1
                            break
                if weekday == 6:
                    for r in rows:
                        if r[0] == event.source.user_id:
                            result = []
                            for s in range(100, 115):
                                if r[s] is None:
                                    result.append('')
                                else:
                                    result.append(r[s])
                            result.append(0)
                            if result:
                                if result[15] == 0:  # 科目名のみモード
                                    i = 1
                                    for t in range(0, 13, 3):
                                        if result[t] == '':
                                            i += 1
                                            continue
                                        else:
                                            reply["contents"]["body"]["contents"].append({
                                                "type": "box",
                                                "layout": "horizontal",
                                                "contents": [
                                                    {
                                                        "type": "text",
                                                        "text": str(i) + "限：",
                                                        "margin": "sm",
                                                        "flex": 1
                                                    },
                                                    {
                                                        "type": "text",
                                                        "text": result[t],
                                                        "wrap": True,
                                                        "flex": 4
                                                    }
                                                ]
                                            })
                                            i += 1
                                    container_obj = FlexSendMessage.new_from_json_dict(
                                        reply)
                                    line_bot_api.reply_message(
                                        event.reply_token, messages=container_obj)
                                elif result[14] == 1:  # 科目名・担当者名・教室名全部入りモード
                                    i = 1
                                    for t in range(0, 14, 3):
                                        if result[t] == '':
                                            i += 1
                                            continue
                                        else:

                                            i += 1
                            break
        else:
            reply = "いつの時間割を返信するか送ってください！\n例：「今日の時間割」"
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text=reply))
    # elif "天気" in message:
    #     if "今日" in message:
    #         try:
    #             url = 'https://www.jma.go.jp/bosai/forecast/data/forecast/270000.json'
    #             res = urllib.request.urlopen(url)
    #             json_load = json.loads(res.read().decode('utf-8'))
    #             today = datetime.datetime.now(
    #                 pytz.timezone('Asia/Tokyo')).strftime("%Y-%m-%d")
    #             reportDatetime = json_load[0]["reportDatetime"]
    #             today_comparenum = reportDatetime.find('T')
    #             today_comparetxt = reportDatetime[:today_comparenum]
    #             array = [
    #                 [100, "1nRV_lWsi6ECjfbNwui992aYeZZF1jqWK"],
    #                 [101, "1z87Ns2IijhU7jHIW4IhFGLegsCzna3xP"],
    #                 [102, "1caWIofc86avt1HvPtznBAdeLb90oDkta"],
    #                 [104, "1wj2m05Rhf57mn_JrvU-mTw6v7U1iEElx"],
    #                 [110, "1Z1OqRYumQihKlPZmxz67KLZmrAdq3eOs"],
    #                 [112, "1dPrrUozhhv1swCCiVmRiDOzlDMV4twjS"],
    #                 [115, "1sZVW6kPB91OYO_beH9Hg5P358EuDlWr8"],
    #                 [200, "1ahxfgvY4Li3nMPCDLZfJosrk2RKO0-tU"],
    #                 [201, "1Xr6HfglnaHaWAs6koR5l6VRJEPwYrUKr"],
    #                 [202, "1xmnHajfHx1qhdTdK2CNqacEOjw9CeaV3"],
    #                 [204, "16dRJzT9JfpQYZ3qUqCpfqw3qlyi6Rl0B"],
    #                 [210, "1iLF6VIZPMWHy7_p2rW1QbJsYMTrvaKYW"],
    #                 [212, "1uXq7tHoPMLPvTnFL_kBJoN7cbRi4Kd5w"],
    #                 [215, "1kehdv3wi-bFjrRGTL2EMmvwdf9-xDf2t"],
    #                 [300, "1viZY8Wjw3TG5Z4xHwmn7Vpp6Rm1HmQaE"],
    #                 [301, "1M6b6AUsn7QzFjO0dukn6Yshh8OaG7S6Z"],
    #                 [302, "1eVAvl3i7VXt_mZHJ2b1o0P9QwprDTjDn"],
    #                 [303, "17kgTtfdOzpMu1EaKunLUQ0u3VuaiJrPp"],
    #                 [308, "1AswoFT-sR3dlFBfBteX6UYMkK0ekLhuQ"],
    #                 [311, "16NwFUIwPmXtEZq_yfX-mNP4cG1mfssJW"],
    #                 [313, "1FEUGe6ahf2w7c_nmYxPegJPMhG2YL29f"],
    #                 [314, "1SAPJzjo--HEWcgMfEppAlkCamZ0Vdp5y"],
    #                 [400, "1Yi54UcqtiQj2GEUNNqaFYPsFGPDxINOP"],
    #                 [401, "166qOvyRwpotiPuQWb8dpWHXSjcIT8XI7"],
    #                 [402, "16SBKyYUfrWbcCUQQuolaIYLWcR-hgmpi"],
    #                 [403, "1qDz_42BX-3Bmp2my0YjpFCo3ASs0TYFv"],
    #                 [406, "1iNUUBTDpn-2VF0QllG2TMTrguU8uDDBx"],
    #                 [411, "12y6NBqPMJCr3HKD-uiWz8xmCaz1Vs2Rl"],
    #                 [413, "14j84CjGa3XZoG3kbaO-c1oHntReS0G_0"],
    #                 [414, "1qll8bZGSGYwgXL9twFhh4eFxGBegsuRZ"],
    #                 [500, "1336JpawiphPnVQSXBjBMHJ156G6dbUbU"],
    #                 [501, "1UUt4sbCrw8Jhg4Ni0E2tv3DZcS-kg8ER"],
    #                 [502, "1OGKgcN3gvBXhgknzp5YwL5fK8Gl0oQvI"],
    #                 [504, "1qf4ar6z3UKfuV0M4MCfd8VtI__y8ayHQ"],
    #                 [510, "1qklXyxL0dCRNAILvlyhO9J6Dg16-Bz67"],
    #                 [512, "1o8xI7G1HL1MywOuljDG8xH_a3GPFHNDW"],
    #                 [515, "1QuQ7ewqOBycd4rMiR-sse33ss9djJhqz"],
    #                 [601, "1dvq58mXTqsTvgYbSKOQeemcP_Vzi1CyJ"],
    #                 [610, "1LrKK0SKfs1MRsK8TfdjeuLLTylHFqYtl"],
    #                 [701, "17HMq1GZzw4A8A56W_P9uApK3-cbUmGRC"],
    #                 [711, "1zJZAtN_PrQVzdUwMPSgEg0bSdnRvHrjX"]
    #             ]

    #             if today != today_comparetxt and len(json_load[0]['timeSeries'][2]['areas'][0]['temps']) == 2:
    #                 for num in range(41):
    #                     if int(json_load[0]['timeSeries'][0]['areas'][0]['weatherCodes'][1])-1 == array[num][0]:
    #                         imgcode = array[num][1]
    #                         break
    #                 temp_max = str(
    #                     json_load[0]['timeSeries'][2]['areas'][0]['temps'][1]) + "℃"
    #                 if str(json_load[0]['timeSeries'][2]['areas'][0]['temps'][1]) == str(json_load[0]['timeSeries'][2]['areas'][0]['temps'][0]):
    #                     temp_min = "-"
    #                 else:
    #                     temp_min = str(
    #                         json_load[0]['timeSeries'][2]['areas'][0]['temps'][0]) + "℃"
    #                 reply = {
    #                     "type": "flex",
    #                     "altText": "今日の天気" + "：" + json_load[0]['timeSeries'][0]['areas'][0]['weathers'][1],
    #                     "contents": {
    #                         "type": "bubble",
    #                         "header": {
    #                             "type": "box",
    #                             "layout": "vertical",
    #                             "contents": [
    #                                 {
    #                                     "type": "text",
    #                                     "text": "今日の天気",
    #                                     "color": "#FFFFFF",
    #                                     "margin": "none",
    #                                     "weight": "bold",
    #                                     "gravity": "center",
    #                                     "size": "xl"
    #                                 }
    #                             ],
    #                             "backgroundColor": "#3cb371",
    #                             "margin": "none"
    #                         },
    #                         "body": {
    #                             "type": "box",
    #                             "layout": "vertical",
    #                             "contents": [
    #                                 {
    #                                     "type": "box",
    #                                     "layout": "horizontal",
    #                                     "contents": [
    #                                         {
    #                                             "type": "box",
    #                                             "layout": "vertical",
    #                                             "contents": [
    #                                                 {
    #                                                     "type": "box",
    #                                                     "layout": "vertical",
    #                                                     "contents": [
    #                                                         {
    #                                                             "type": "image",
    #                                                             "url": 'https://drive.google.com/uc?id=' + imgcode + '#dummy.png',
    #                                                             "size": "md",
    #                                                             "aspectRatio": "2:1"
    #                                                         }
    #                                                     ]
    #                                                 },
    #                                                 {
    #                                                     "type": "box",
    #                                                     "layout": "vertical",
    #                                                     "contents": [
    #                                                         {
    #                                                             "type": "text",
    #                                                             "text": json_load[0]['timeSeries'][0]['areas'][0]['weathers'][1],
    #                                                             "align": "center"
    #                                                         }
    #                                                     ]
    #                                                 }
    #                                             ]
    #                                         },
    #                                         {
    #                                             "type": "box",
    #                                             "layout": "vertical",
    #                                             "contents": [
    #                                                 {
    #                                                     "type": "text",
    #                                                     "text": temp_max,
    #                                                     "size": "xl",
    #                                                     "color": "#ff6347"
    #                                                 },
    #                                                 {
    #                                                     "type": "text",
    #                                                     "text": temp_min,
    #                                                     "size": "xl",
    #                                                     "color": "#4169e1"
    #                                                 }
    #                                             ]
    #                                         }
    #                                     ]
    #                                 }
    #                             ]
    #                         }
    #                     }
    #                 }
    #                 container_obj = FlexSendMessage.new_from_json_dict(reply)
    #                 line_bot_api.reply_message(
    #                     event.reply_token, messages=container_obj)
    #             elif today == today_comparetxt and len(json_load[0]['timeSeries'][2]['areas'][0]['temps']) == 4:
    #                 for num in range(41):
    #                     if int(json_load[0]['timeSeries'][0]['areas'][0]['weatherCodes'][0])-1 == array[num][0]:
    #                         imgcode = array[num][1]
    #                         break
    #                 temp_max = str(
    #                     json_load[0]['timeSeries'][2]['areas'][0]['temps'][1]) + "℃"
    #                 if str(json_load[0]['timeSeries'][2]['areas'][0]['temps'][1]) == str(json_load[0]['timeSeries'][2]['areas'][0]['temps'][0]):
    #                     temp_min = "-"
    #                 else:
    #                     temp_min = str(
    #                         json_load[0]['timeSeries'][2]['areas'][0]['temps'][0]) + "℃"
    #                 reply = {
    #                     "type": "flex",
    #                     "altText": "今日の天気" + "：" + json_load[0]['timeSeries'][0]['areas'][0]['weathers'][0],
    #                     "contents": {
    #                         "type": "bubble",
    #                         "header": {
    #                             "type": "box",
    #                             "layout": "vertical",
    #                             "contents": [
    #                                 {
    #                                     "type": "text",
    #                                     "text": "今日の天気",
    #                                     "color": "#FFFFFF",
    #                                     "margin": "none",
    #                                     "weight": "bold",
    #                                     "gravity": "center",
    #                                     "size": "xl"
    #                                 }
    #                             ],
    #                             "backgroundColor": "#3cb371",
    #                             "margin": "none"
    #                         },
    #                         "body": {
    #                             "type": "box",
    #                             "layout": "vertical",
    #                             "contents": [
    #                                 {
    #                                     "type": "box",
    #                                     "layout": "horizontal",
    #                                     "contents": [
    #                                         {
    #                                             "type": "box",
    #                                             "layout": "vertical",
    #                                             "contents": [
    #                                                 {
    #                                                     "type": "box",
    #                                                     "layout": "vertical",
    #                                                     "contents": [
    #                                                         {
    #                                                             "type": "image",
    #                                                             "url": 'https://drive.google.com/uc?id=' + imgcode + '#dummy.png',
    #                                                             "size": "md",
    #                                                             "aspectRatio": "2:1"
    #                                                         }
    #                                                     ]
    #                                                 },
    #                                                 {
    #                                                     "type": "box",
    #                                                     "layout": "vertical",
    #                                                     "contents": [
    #                                                         {
    #                                                             "type": "text",
    #                                                             "text": json_load[0]['timeSeries'][0]['areas'][0]['weathers'][0],
    #                                                             "align": "center"
    #                                                         }
    #                                                     ]
    #                                                 }
    #                                             ]
    #                                         },
    #                                         {
    #                                             "type": "box",
    #                                             "layout": "vertical",
    #                                             "contents": [
    #                                                 {
    #                                                     "type": "text",
    #                                                     "text": temp_max,
    #                                                     "size": "xl",
    #                                                     "color": "#ff6347"
    #                                                 },
    #                                                 {
    #                                                     "type": "text",
    #                                                     "text": temp_min,
    #                                                     "size": "xl",
    #                                                     "color": "#4169e1"
    #                                                 }
    #                                             ]
    #                                         }
    #                                     ]
    #                                 }
    #                             ]
    #                         }
    #                     }
    #                 }
    #                 container_obj = FlexSendMessage.new_from_json_dict(reply)
    #                 line_bot_api.reply_message(
    #                     event.reply_token, messages=container_obj)
    #             elif today == today_comparetxt and len(json_load[0]['timeSeries'][2]['areas'][0]['temps']) == 2:
    #                 for num in range(41):
    #                     if int(json_load[0]['timeSeries'][0]['areas'][0]['weatherCodes'][0])-1 == array[num][0]:
    #                         imgcode = array[num][1]
    #                         break
    #                 temp_max = "-"
    #                 temp_min = "-"
    #                 reply = {
    #                     "type": "flex",
    #                     "altText": "今日の天気" + "：" + json_load[0]['timeSeries'][0]['areas'][0]['weathers'][0],
    #                     "contents": {
    #                         "type": "bubble",
    #                         "header": {
    #                             "type": "box",
    #                             "layout": "vertical",
    #                             "contents": [
    #                                 {
    #                                     "type": "text",
    #                                     "text": "今日の天気",
    #                                     "color": "#FFFFFF",
    #                                     "margin": "none",
    #                                     "weight": "bold",
    #                                     "gravity": "center",
    #                                     "size": "xl"
    #                                 }
    #                             ],
    #                             "backgroundColor": "#3cb371",
    #                             "margin": "none"
    #                         },
    #                         "body": {
    #                             "type": "box",
    #                             "layout": "vertical",
    #                             "contents": [
    #                                 {
    #                                     "type": "box",
    #                                     "layout": "horizontal",
    #                                     "contents": [
    #                                         {
    #                                             "type": "box",
    #                                             "layout": "vertical",
    #                                             "contents": [
    #                                                 {
    #                                                     "type": "box",
    #                                                     "layout": "vertical",
    #                                                     "contents": [
    #                                                         {
    #                                                             "type": "image",
    #                                                             "url": 'https://drive.google.com/uc?id=' + imgcode + '#dummy.png',
    #                                                             "size": "md",
    #                                                             "aspectRatio": "2:1"
    #                                                         }
    #                                                     ]
    #                                                 },
    #                                                 {
    #                                                     "type": "box",
    #                                                     "layout": "vertical",
    #                                                     "contents": [
    #                                                         {
    #                                                             "type": "text",
    #                                                             "text": json_load[0]['timeSeries'][0]['areas'][0]['weathers'][0],
    #                                                             "align": "center"
    #                                                         }
    #                                                     ]
    #                                                 }
    #                                             ]
    #                                         },
    #                                         {
    #                                             "type": "box",
    #                                             "layout": "vertical",
    #                                             "contents": [
    #                                                 {
    #                                                     "type": "text",
    #                                                     "text": temp_max,
    #                                                     "size": "xl",
    #                                                     "color": "#ff6347"
    #                                                 },
    #                                                 {
    #                                                     "type": "text",
    #                                                     "text": temp_min,
    #                                                     "size": "xl",
    #                                                     "color": "#4169e1"
    #                                                 }
    #                                             ]
    #                                         }
    #                                     ]
    #                                 }
    #                             ]
    #                         }
    #                     }
    #                 }
    #                 container_obj = FlexSendMessage.new_from_json_dict(reply)
    #                 line_bot_api.reply_message(
    #                     event.reply_token, messages=container_obj)
    #         except urllib.error.HTTPError as e:
    #             print('HTTPError: ', e)
    #         except json.JSONDecodeError as e:
    #             print('JSONDecodeError: ', e)
    #     elif "明日" in message:
    #         try:
    #             url = 'https://www.jma.go.jp/bosai/forecast/data/forecast/270000.json'
    #             res = urllib.request.urlopen(url)
    #             json_load = json.loads(res.read().decode('utf-8'))
    #             today = datetime.datetime.now(
    #                 pytz.timezone('Asia/Tokyo')).strftime("%Y-%m-%d")
    #             reportDatetime = json_load[0]["reportDatetime"]
    #             today_comparenum = reportDatetime.find('T')
    #             today_comparetxt = reportDatetime[:today_comparenum]
    #             array = [
    #                 [100, "1nRV_lWsi6ECjfbNwui992aYeZZF1jqWK"],
    #                 [101, "1z87Ns2IijhU7jHIW4IhFGLegsCzna3xP"],
    #                 [102, "1caWIofc86avt1HvPtznBAdeLb90oDkta"],
    #                 [104, "1wj2m05Rhf57mn_JrvU-mTw6v7U1iEElx"],
    #                 [110, "1Z1OqRYumQihKlPZmxz67KLZmrAdq3eOs"],
    #                 [112, "1dPrrUozhhv1swCCiVmRiDOzlDMV4twjS"],
    #                 [115, "1sZVW6kPB91OYO_beH9Hg5P358EuDlWr8"],
    #                 [200, "1ahxfgvY4Li3nMPCDLZfJosrk2RKO0-tU"],
    #                 [201, "1Xr6HfglnaHaWAs6koR5l6VRJEPwYrUKr"],
    #                 [202, "1xmnHajfHx1qhdTdK2CNqacEOjw9CeaV3"],
    #                 [204, "16dRJzT9JfpQYZ3qUqCpfqw3qlyi6Rl0B"],
    #                 [210, "1iLF6VIZPMWHy7_p2rW1QbJsYMTrvaKYW"],
    #                 [212, "1uXq7tHoPMLPvTnFL_kBJoN7cbRi4Kd5w"],
    #                 [215, "1kehdv3wi-bFjrRGTL2EMmvwdf9-xDf2t"],
    #                 [300, "1viZY8Wjw3TG5Z4xHwmn7Vpp6Rm1HmQaE"],
    #                 [301, "1M6b6AUsn7QzFjO0dukn6Yshh8OaG7S6Z"],
    #                 [302, "1eVAvl3i7VXt_mZHJ2b1o0P9QwprDTjDn"],
    #                 [303, "17kgTtfdOzpMu1EaKunLUQ0u3VuaiJrPp"],
    #                 [308, "1AswoFT-sR3dlFBfBteX6UYMkK0ekLhuQ"],
    #                 [311, "16NwFUIwPmXtEZq_yfX-mNP4cG1mfssJW"],
    #                 [313, "1FEUGe6ahf2w7c_nmYxPegJPMhG2YL29f"],
    #                 [314, "1SAPJzjo--HEWcgMfEppAlkCamZ0Vdp5y"],
    #                 [400, "1Yi54UcqtiQj2GEUNNqaFYPsFGPDxINOP"],
    #                 [401, "166qOvyRwpotiPuQWb8dpWHXSjcIT8XI7"],
    #                 [402, "16SBKyYUfrWbcCUQQuolaIYLWcR-hgmpi"],
    #                 [403, "1qDz_42BX-3Bmp2my0YjpFCo3ASs0TYFv"],
    #                 [406, "1iNUUBTDpn-2VF0QllG2TMTrguU8uDDBx"],
    #                 [411, "12y6NBqPMJCr3HKD-uiWz8xmCaz1Vs2Rl"],
    #                 [413, "14j84CjGa3XZoG3kbaO-c1oHntReS0G_0"],
    #                 [414, "1qll8bZGSGYwgXL9twFhh4eFxGBegsuRZ"],
    #                 [500, "1336JpawiphPnVQSXBjBMHJ156G6dbUbU"],
    #                 [501, "1UUt4sbCrw8Jhg4Ni0E2tv3DZcS-kg8ER"],
    #                 [502, "1OGKgcN3gvBXhgknzp5YwL5fK8Gl0oQvI"],
    #                 [504, "1qf4ar6z3UKfuV0M4MCfd8VtI__y8ayHQ"],
    #                 [510, "1qklXyxL0dCRNAILvlyhO9J6Dg16-Bz67"],
    #                 [512, "1o8xI7G1HL1MywOuljDG8xH_a3GPFHNDW"],
    #                 [515, "1QuQ7ewqOBycd4rMiR-sse33ss9djJhqz"],
    #                 [601, "1dvq58mXTqsTvgYbSKOQeemcP_Vzi1CyJ"],
    #                 [610, "1LrKK0SKfs1MRsK8TfdjeuLLTylHFqYtl"],
    #                 [701, "17HMq1GZzw4A8A56W_P9uApK3-cbUmGRC"],
    #                 [711, "1zJZAtN_PrQVzdUwMPSgEg0bSdnRvHrjX"]
    #             ]

    #             if today != today_comparetxt and len(json_load[0]['timeSeries'][2]['areas'][0]['temps']) == 2:
    #                 for num in range(41):
    #                     if int(json_load[0]['timeSeries'][0]['areas'][0]['weatherCodes'][2])-1 == array[num][0]:
    #                         imgcode = array[num][1]
    #                         break
    #                 temp_max = str(
    #                     json_load[0]['timeSeries'][2]['areas'][0]['temps'][3]) + "℃"
    #                 if str(json_load[0]['timeSeries'][2]['areas'][0]['temps'][3]) == str(json_load[0]['timeSeries'][2]['areas'][0]['temps'][2]):
    #                     temp_min = "-"
    #                 else:
    #                     temp_min = str(
    #                         json_load[0]['timeSeries'][2]['areas'][0]['temps'][2]) + "℃"
    #                 reply = {
    #                     "type": "flex",
    #                     "altText": "明日の天気" + "：" + json_load[0]['timeSeries'][0]['areas'][0]['weathers'][2],
    #                     "contents": {
    #                         "type": "bubble",
    #                         "header": {
    #                             "type": "box",
    #                             "layout": "vertical",
    #                             "contents": [
    #                                 {
    #                                     "type": "text",
    #                                     "text": "明日の天気",
    #                                     "color": "#FFFFFF",
    #                                     "margin": "none",
    #                                     "weight": "bold",
    #                                     "gravity": "center",
    #                                     "size": "xl"
    #                                 }
    #                             ],
    #                             "backgroundColor": "#3cb371",
    #                             "margin": "none"
    #                         },
    #                         "body": {
    #                             "type": "box",
    #                             "layout": "vertical",
    #                             "contents": [
    #                                 {
    #                                     "type": "box",
    #                                     "layout": "horizontal",
    #                                     "contents": [
    #                                         {
    #                                             "type": "box",
    #                                             "layout": "vertical",
    #                                             "contents": [
    #                                                 {
    #                                                     "type": "box",
    #                                                     "layout": "vertical",
    #                                                     "contents": [
    #                                                         {
    #                                                             "type": "image",
    #                                                             "url": 'https://drive.google.com/uc?id=' + imgcode + '#dummy.png',
    #                                                             "size": "md",
    #                                                             "aspectRatio": "2:1"
    #                                                         }
    #                                                     ]
    #                                                 },
    #                                                 {
    #                                                     "type": "box",
    #                                                     "layout": "vertical",
    #                                                     "contents": [
    #                                                         {
    #                                                             "type": "text",
    #                                                             "text": json_load[0]['timeSeries'][0]['areas'][0]['weathers'][2],
    #                                                             "align": "center"
    #                                                         }
    #                                                     ]
    #                                                 }
    #                                             ]
    #                                         },
    #                                         {
    #                                             "type": "box",
    #                                             "layout": "vertical",
    #                                             "contents": [
    #                                                 {
    #                                                     "type": "text",
    #                                                     "text": temp_max,
    #                                                     "size": "xl",
    #                                                     "color": "#ff6347"
    #                                                 },
    #                                                 {
    #                                                     "type": "text",
    #                                                     "text": temp_min,
    #                                                     "size": "xl",
    #                                                     "color": "#4169e1"
    #                                                 }
    #                                             ]
    #                                         }
    #                                     ]
    #                                 }
    #                             ]
    #                         }
    #                     }
    #                 }
    #                 container_obj = FlexSendMessage.new_from_json_dict(
    #                     reply)
    #                 line_bot_api.reply_message(
    #                     event.reply_token, messages=container_obj)
    #             elif today == today_comparetxt and len(json_load[0]['timeSeries'][2]['areas'][0]['temps']) == 4:
    #                 for num in range(41):
    #                     if int(json_load[0]['timeSeries'][0]['areas'][0]['weatherCodes'][1])-1 == array[num][0]:
    #                         imgcode = array[num][1]
    #                         break
    #                 temp_max = str(
    #                     json_load[0]['timeSeries'][2]['areas'][0]['temps'][3]) + "℃"
    #                 if str(json_load[0]['timeSeries'][2]['areas'][0]['temps'][3]) == str(json_load[0]['timeSeries'][2]['areas'][0]['temps'][2]):
    #                     temp_min = "-"
    #                 else:
    #                     temp_min = str(
    #                         json_load[0]['timeSeries'][2]['areas'][0]['temps'][2]) + "℃"
    #                 reply = {
    #                     "type": "flex",
    #                     "altText": "明日の天気" + "：" + json_load[0]['timeSeries'][0]['areas'][0]['weathers'][1],
    #                     "contents": {
    #                         "type": "bubble",
    #                         "header": {
    #                             "type": "box",
    #                             "layout": "vertical",
    #                             "contents": [
    #                                 {
    #                                     "type": "text",
    #                                     "text": "明日の天気",
    #                                     "color": "#FFFFFF",
    #                                     "margin": "none",
    #                                     "weight": "bold",
    #                                     "gravity": "center",
    #                                     "size": "xl"
    #                                 }
    #                             ],
    #                             "backgroundColor": "#3cb371",
    #                             "margin": "none"
    #                         },
    #                         "body": {
    #                             "type": "box",
    #                             "layout": "vertical",
    #                             "contents": [
    #                                 {
    #                                     "type": "box",
    #                                     "layout": "horizontal",
    #                                     "contents": [
    #                                         {
    #                                             "type": "box",
    #                                             "layout": "vertical",
    #                                             "contents": [
    #                                                 {
    #                                                     "type": "box",
    #                                                     "layout": "vertical",
    #                                                     "contents": [
    #                                                         {
    #                                                             "type": "image",
    #                                                             "url": 'https://drive.google.com/uc?id=' + imgcode + '#dummy.png',
    #                                                             "size": "md",
    #                                                             "aspectRatio": "2:1"
    #                                                         }
    #                                                     ]
    #                                                 },
    #                                                 {
    #                                                     "type": "box",
    #                                                     "layout": "vertical",
    #                                                     "contents": [
    #                                                         {
    #                                                             "type": "text",
    #                                                             "text": json_load[0]['timeSeries'][0]['areas'][0]['weathers'][1],
    #                                                             "align": "center"
    #                                                         }
    #                                                     ]
    #                                                 }
    #                                             ]
    #                                         },
    #                                         {
    #                                             "type": "box",
    #                                             "layout": "vertical",
    #                                             "contents": [
    #                                                 {
    #                                                     "type": "text",
    #                                                     "text": temp_max,
    #                                                     "size": "xl",
    #                                                     "color": "#ff6347"
    #                                                 },
    #                                                 {
    #                                                     "type": "text",
    #                                                     "text": temp_min,
    #                                                     "size": "xl",
    #                                                     "color": "#4169e1"
    #                                                 }
    #                                             ]
    #                                         }
    #                                     ]
    #                                 }
    #                             ]
    #                         }
    #                     }
    #                 }
    #                 container_obj = FlexSendMessage.new_from_json_dict(
    #                     reply)
    #                 line_bot_api.reply_message(
    #                     event.reply_token, messages=container_obj)
    #             elif today == today_comparetxt and len(json_load[0]['timeSeries'][2]['areas'][0]['temps']) == 2:
    #                 for num in range(41):
    #                     if int(json_load[0]['timeSeries'][0]['areas'][0]['weatherCodes'][1])-1 == array[num][0]:
    #                         imgcode = array[num][1]
    #                         break
    #                 temp_max = str(
    #                     json_load[0]['timeSeries'][2]['areas'][0]['temps'][1]) + "℃"
    #                 temp_min = str(
    #                     json_load[0]['timeSeries'][2]['areas'][0]['temps'][0]) + "℃"
    #                 reply = {
    #                     "type": "flex",
    #                     "altText": "明日の天気" + "：" + json_load[0]['timeSeries'][0]['areas'][0]['weathers'][2],
    #                     "contents": {
    #                         "type": "bubble",
    #                         "header": {
    #                             "type": "box",
    #                             "layout": "vertical",
    #                             "contents": [
    #                                 {
    #                                     "type": "text",
    #                                     "text": "明日の天気",
    #                                     "color": "#FFFFFF",
    #                                     "margin": "none",
    #                                     "weight": "bold",
    #                                     "gravity": "center",
    #                                     "size": "xl"
    #                                 }
    #                             ],
    #                             "backgroundColor": "#3cb371",
    #                             "margin": "none"
    #                         },
    #                         "body": {
    #                             "type": "box",
    #                             "layout": "vertical",
    #                             "contents": [
    #                                 {
    #                                     "type": "box",
    #                                     "layout": "horizontal",
    #                                     "contents": [
    #                                         {
    #                                             "type": "box",
    #                                             "layout": "vertical",
    #                                             "contents": [
    #                                                 {
    #                                                     "type": "box",
    #                                                     "layout": "vertical",
    #                                                     "contents": [
    #                                                         {
    #                                                             "type": "image",
    #                                                             "url": 'https://drive.google.com/uc?id=' + imgcode + '#dummy.png',
    #                                                             "size": "md",
    #                                                             "aspectRatio": "2:1"
    #                                                         }
    #                                                     ]
    #                                                 },
    #                                                 {
    #                                                     "type": "box",
    #                                                     "layout": "vertical",
    #                                                     "contents": [
    #                                                         {
    #                                                             "type": "text",
    #                                                             "text": json_load[0]['timeSeries'][0]['areas'][0]['weathers'][2],
    #                                                             "align": "center"
    #                                                         }
    #                                                     ]
    #                                                 }
    #                                             ]
    #                                         },
    #                                         {
    #                                             "type": "box",
    #                                             "layout": "vertical",
    #                                             "contents": [
    #                                                 {
    #                                                     "type": "text",
    #                                                     "text": temp_max,
    #                                                     "size": "xl",
    #                                                     "color": "#ff6347"
    #                                                 },
    #                                                 {
    #                                                     "type": "text",
    #                                                     "text": temp_min,
    #                                                     "size": "xl",
    #                                                     "color": "#4169e1"
    #                                                 }
    #                                             ]
    #                                         }
    #                                     ]
    #                                 }
    #                             ]
    #                         }
    #                     }
    #                 }
    #                 container_obj = FlexSendMessage.new_from_json_dict(
    #                     reply)
    #                 line_bot_api.reply_message(
    #                     event.reply_token, messages=container_obj)
    #         except urllib.error.HTTPError as e:
    #             print('HTTPError: ', e)
    #         except json.JSONDecodeError as e:
    #             print('JSONDecodeError: ', e)
    #     else:
    #         reply = "いつの天気を返信するか送ってください！\n例：「今日の天気」"
    #         line_bot_api.reply_message(
    #             event.reply_token, TextSendMessage(text=reply))
    # elif "運行情報" in message:
    #     reply = "運行情報"
    #     line_bot_api.reply_message(
    #         event.reply_token,
    #         TextSendMessage(text=reply))
    elif "設定" in message:
        reply = "設定画面を開きません。"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply))
    elif "ひらけごま" in message or "開けごま" in message or "ひらけ胡麻" in message or "開け胡麻" in message:
        reply = "開きません"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply))
    elif "help" in message or "Help" in message or "HELP" in message or "ヘルプ" in message or "使い方" in message or "わからない" in message:
        reply = "【使用方法】\n・時間割\n「今日の時間割」または「明日の時間割」と送信すると，設定ページで設定された時間割が表示されます。\n・天気\n「今日の天気」または「明日の天気」と送信すると，設定ページで設定された大学最寄り駅がある都道府県の時間割が表示されます。\n・運行情報\n「運行情報」と送信すると，設定ページで設定された路線(最大4路線)の運行情報を表示します。\n・設定\n「設定」と送信すると，設定ページのURLが表示されます(仮)。"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply,
                            quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(
                                        action=MessageAction(
                                            label="今日の時間割", text="今日の時間割")
                                    ),
                                    QuickReplyButton(
                                        action=MessageAction(
                                            label="今日の天気", text="今日の天気")
                                    ),
                                    QuickReplyButton(
                                        action=MessageAction(
                                            label="運行情報", text="運行情報")
                                    )
                                ])))
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
