from flask import Flask, request, abort
import os
import pymysql
pymysql.install_as_MySQLdb()
import MySQLdb

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

app = Flask(__name__)

#環境変数取得
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]
DB_USERNAME = os.environ["DB_USERNAME"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_HOSTNAME = os.environ["DB_HOSTNAME"]
DB_NAME = os.environ["DB_NAME"]

DB_TABLE = "linedata"

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

@app.route("/")
def hello_world():
    return "hello world!"

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
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))

# Follow Event
@handler.add(FollowEvent)
def on_follow(event):
    reply_token = event.reply_token
    user_id = event.source.user_id
    profiles = line_bot_api.get_profile(user_id=user_id)
    display_name = profiles.display_name
    picture_url = profiles.picture_url
    status_message = profiles.status_message

    # DBへの保存
    try:
        conn = MySQLdb.connect(user=DB_USERNAME, passwd=DB_PASSWORD, host=DB_HOSTNAME, db=DB_NAME)
        c = conn.cursor()
        sql = "SELECT `id` FROM`"+DB_TABLE+"` WHERE `user_id` = '"+user_id+"';"
        c.execute(sql)
        ret = c.fetchall()
        if len(ret) == 0:
            sql = "INSERT INTO `"+DB_TABLE+"` (`user_id`, `display_name`, `picture_url`, `status_message`, `status`)\
              VALUES ('"+user_id+"', '"+str(display_name)+"', '"+str(picture_url)+"', '"+str(status_message)+"', 1);"
        elif len(ret) == 1:
            sql = "UPDATE `"+DB_TABLE+"` SET `display_name` = '"+str(display_name)+"', `picture_url` = '"+str(picture_url)+"',\
            `status_message` = '"+str(status_message)+"', `status` = '1' WHERE `user_id` = '"+user_id+"';"
        c.execute(sql)
        conn.commit()
    finally:
        conn.close()
        c.close()

    # メッセージの送信
    line_bot_api.reply_message(
        reply_token=reply_token,
        messages=TextSendMessage(text='メッセージArigato!\nです')
    )


if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)