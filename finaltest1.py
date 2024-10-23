from flask import Flask
app = Flask(__name__,static_folder='static')


from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, text

from flask import request, abort, render_template
from linebot import  LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage,TextSendMessage,BubbleContainer, ImageSendMessage, BoxComponent, TextComponent, IconComponent, ButtonComponent, SeparatorComponent,FlexSendMessage,URIAction
import os

from flask import Flask
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta

import random
from linebot.models import PostbackEvent, TemplateSendMessage, CarouselTemplate, CarouselColumn, PostbackTemplateAction

from linebot.models import LocationSendMessage, ButtonsTemplate, URITemplateAction, ConfirmTemplate, MessageTemplateAction, ImageCarouselTemplate, ImageCarouselColumn,VideoSendMessage
from sqlalchemy import text
from urllib.parse import parse_qsl

from openai import OpenAI
import openai
from dotenv import load_dotenv
import json
import sys

import threading
import schedule
import time

from flask import jsonify, make_response
from model import db, Journal  # 從 models 模塊導入
import base64
import requests
from xhtml2pdf import pisa
from io import BytesIO
import logging
import pdfkit

app.config['SQLALCHEMY_DATABASE_URI'] = (os.environ.get('DATABASE_URL'))
# db=SQLAlchemy(app)
db.init_app(app)
# engine=create_engine('postgresql://admin:123456@127.0.0.1:5432/Bemomcares')

line_bot_api = LineBotApi(os.environ.get('Channel_Access_Token'))
handler = WebhookHandler(os.environ.get('Channel_Secret'))

#LIFF靜態頁面
@app.route('/page')
def page():
    liffid = '2005754474-9Qa5jj7y'
    
    # 獲取靜態文件夾中所有圖片檔案名稱
    image_folder = os.path.join(app.static_folder, 'image')
    image_files = [f for f in os.listdir(image_folder) if os.path.isfile(os.path.join(image_folder, f))]
    
    return render_template('index1.html', image_files=image_files, liffid = liffid)

#LIFF靜態頁面
@app.route('/page2')
def page2():
    liffid2 = '2005754474-eLDEppxO'
    return render_template('journal.html', liffid2 = liffid2)


#-----關鍵字Start-----

# 設置 OpenAI API Key
api_key = os.environ.get('Api_Key')
client = OpenAI(api_key)

# 初始化變量來跟踪系統狀態
is_active = False

#-----關鍵字End-----

#-----日記Start-----

GITHUB_API_TOKEN = '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'
GITHUB_REPO = 'bemomcares/photos'
GITHUB_FOLDER = 'jphoto'

# wkhtmltopdf 配置
config = pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf')

#-----日記End-----

#-----週期紀錄Start-----

# 資料庫連接信息
DATABASE_CONFIG = {
    'dbname': 'dbname_3qcx',
    'user': 'admin',
    'password': 'ucKH8MhsmXSQEaS69FnvP5YDeMW95WaC',
    'host': 'dpg-csb7h688fa8c73cluhag-a',
    'port': '5432'
}

# 創建資料表
def init_db():
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id VARCHAR(255) PRIMARY KEY,
                last_period_date DATE NOT NULL,
                estimated_due_date DATE NOT NULL
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
        print("資料表初始化完畢")
    except Exception as e:
        print(f"資料庫初始化錯誤: {e}")

# 初始化資料表
init_db()

def save_user_data(user_id, last_period_date, estimated_due_date):
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (user_id, last_period_date, estimated_due_date)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE
            SET last_period_date = EXCLUDED.last_period_date,
                estimated_due_date = EXCLUDED.estimated_due_date;
        """, (user_id, last_period_date, estimated_due_date))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"資料已成功儲存: user_id={user_id}, last_period_date={last_period_date}, estimated_due_date={estimated_due_date}")
    except Exception as e:
        print(f"保存用戶數據錯誤: {e}")

def get_user_data(user_id):
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT last_period_date, estimated_due_date FROM users WHERE user_id = %s", (user_id,))
        data = cursor.fetchone()
        cursor.close()
        conn.close()
        if data:
            data['last_period_date'] = data['last_period_date'].strftime('%Y-%m-%d')
            data['estimated_due_date'] = data['estimated_due_date'].strftime('%Y-%m-%d')
            print(f"從資料庫獲取資料: {data}")
            return data
        print("沒有找到用戶數據")
        return None
    except Exception as e:
        print(f"獲取用戶數據錯誤: {e}")
        return None
    
user_mod = {} #用來區分輸入欄目前處於哪個功能的狀態

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print("handle_message function was called")
    # user_msg = event.message.text
    # print(f"Received111 user_msg: {user_msg}")
    user_id = event.source.user_id
    
    
    if user_id not in user_mod:
        user_mod[user_id] = 0  # 初始狀態
    
    #user_mod[user_id] = 0
        
    if user_mod[user_id] == 0: #當user_mod為初始狀態時
        user_msg = event.message.text
        print(f"Received1-1 user_msg: {user_msg}")
        
        if user_msg == '@關鍵字':
            user_mod[user_id] = 1
            print(f"Received user_mod: {user_mod[user_id]}")
            response = "歡迎使用關鍵字問答！\n如果想知道更多關於系統簡介與使用說明，請輸入【系統簡介】或【介紹】。"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response))
        elif user_msg == '@舒緩運動':
            sendCarousel(event)
        elif user_msg == '@週期紀錄':
            user_mod[user_id] = 2
            print(f"Received user_mod: {user_mod[user_id]}")
        
            # 檢查用戶資料是否存在於資料庫中
            existing_data = get_user_data(user_id)
            
            if existing_data is None:
                existing_data = {}  # 或者賦予一個默認的空字典/列表/值
                
            print(f"Received user_states: {user_states}")
            print(f"Received existing_data: {existing_data}")  
        
            #用戶更新狀態
            if user_id in user_states and user_states[user_id] == "updating":
                handle_user_update(event, user_msg, user_id)
            else:
                handle_new_input(event, user_msg, user_id, existing_data)
            return  # 系統未啟動時，不回應任何其他訊息
        else:
            response = "歡迎點擊下方選單使用本系統所有功能！"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response))
    
    elif user_mod[user_id] == 1: #用戶正在：1 關鍵字搜尋 模式
        user_msg = event.message.text
        print(f"Received1-2 user_msg: {user_msg}")
        print(f"User {user_id} is in keyword mode with message: {user_msg}")
        
        if user_msg in ['結束關鍵字', '結束','結束問答']:
            response = "結束問答，感謝您的使用！"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response))
            user_mod[user_id] = 0  # 將用戶狀態設為無
        elif user_msg in ['系統簡介', '介紹','簡介']:
            response = system_intro(user_msg)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response))
        elif user_msg == '@關鍵字':
            response = "歡迎使用關鍵字問答！\n如果想知道更多關於系統簡介與使用說明，請輸入【系統簡介】或【介紹】"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response))
        else:
            response = default_response(user_msg)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response))
            
    elif user_mod[user_id] == 2: #用戶正在：2 週期紀錄 模式
        # 用戶更新狀態
        # if user_id in user_states and user_states[user_id] == "updating":
        #     handle_user_update(event, user_msg, user_id)
        # else:
        #     handle_new_input(event, user_msg, user_id, existing_data)
        # return  # 系統未啟動時，不回應任何其他訊息
        user_msg = event.message.text
        print(f"Received1-3 user_msg: {user_msg}")
        
        existing_data = get_user_data(user_id)
        
        if existing_data is None:
            existing_data = {}  # 或者賦予一個默認的空字典/列表/值
    
        if user_msg in ['確認', '確認無誤']:
            response = "確認資訊正確，歡迎使用其他功能！"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response))
            user_mod[user_id] = 0
    
        else:
            if user_id in user_states and user_states[user_id] == "updating":
                handle_user_update(event, user_msg, user_id)
            else:
                handle_new_input(event, user_msg, user_id, existing_data)
            return  # 系統未啟動時，不回應任何其他訊息
            
        
    
    # global is_active #關鍵字的啟動與否判斷函數
    # if not is_active:
    #     if user_msg == '@關鍵字':
    #         is_active = True
    #         response = "歡迎回到關鍵字問答，您可以繼續提問。"
    #         line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response))
    #     elif user_msg == '@舒緩運動':
    #         sendCarousel(event)
    #     elif user_msg == '@週期紀錄':
            
    #         # 檢查用戶資料是否存在於資料庫中
    #         existing_data = get_user_data(user_id)
    #         print(f"Received user_states: {user_states}")
    #         print(f"Received existing_data: {existing_data}")
            

    #     # 用戶更新狀態
    #     if user_id in user_states and user_states[user_id] == "updating":
    #         handle_user_update(event, user_msg, user_id)
    #     else:
    #         handle_new_input(event, user_msg, user_id, existing_data)
    #     return  # 系統未啟動時，不回應任何其他訊息
    
    # else:
    #     if user_msg in ['結束關鍵字', '結束','結束問答']:
    #         response = "結束問答，感謝您的使用！"
    #         line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response))
    #         is_active = False  # 將系統狀態設為不活躍
    #     elif user_msg in ['系統簡介', '介紹','簡介']:
    #         response = system_intro(user_msg)
    #         line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response))
    #     elif user_msg == '@關鍵字':
    #         response = "歡迎使用關鍵字問答！\n如果想知道更多關於系統簡介與使用說明，請輸入【系統簡介】或【介紹】"
    #         line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response))
    #     else:
    #         response = default_response(user_msg)
    #         line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response))
    
    #print(f"從事件中處理的 user_id: {user_id}")


#--週期Start--
def handle_user_update(event, user_msg, user_id):
    if not user_msg.strip():
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請輸入最後一次月經日的第一天。")
        )
        return
    
    try:
        last_period_date = datetime.strptime(user_msg, "%Y-%m-%d").date()
        
        # 計算今天的日期以及允許的最早日期 (今天 - 280 天)
        today = datetime.now().date()
        earliest_allowed_date = today - timedelta(days=280)
        
        # 檢查使用者輸入的日期是否在允許的區間內
        if earliest_allowed_date <= last_period_date <= today:
            estimated_due_date = last_period_date + timedelta(days=280)    # 日期在範圍內，計算預估的預產期
            save_user_data(user_id, last_period_date, estimated_due_date)  # 儲存使用者資料
            response_text = (
                f"最後一次月經的第一天已更新為 {last_period_date.strftime('%Y-%m-%d')}，"
                f"預計的生產日期是 {estimated_due_date.strftime('%Y-%m-%d')}。\n"
                "再次點擊選單中【週期紀錄】功能可查看當前週數。"
            )
            user_mod[user_id] = 0
            user_states.pop(user_id, None)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=response_text)
            )     
        else:
            response = "請輸入從今天起最多 280 天內的正確日期。"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response))
        
        # estimated_due_date = last_period_date + timedelta(days=280)
        # save_user_data(user_id, last_period_date, estimated_due_date)

        # response_text = (
        #     f"最後一次月經的第一天已更新為 {last_period_date.strftime('%Y-%m-%d')}，"
        #     f"預計的生產日期是 {estimated_due_date.strftime('%Y-%m-%d')}。\n"
        #     "再次點擊選單中【週期紀錄】功能可查看當前週數。"
        # )
        
        # user_mod[user_id] = 0

        # user_states.pop(user_id, None)

        # line_bot_api.reply_message(
        #     event.reply_token,
        #     TextSendMessage(text=response_text)
        #)
    except ValueError:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請以YYYY-MM-DD格式重新輸入最後一次月經日期。")
        )

def handle_new_input(event, user_msg, user_id, existing_data):
    #user_msg = event.message.text
    # print(f"Received22 user_msg: {user_msg}")
    
    if existing_data:
       
        week = calculate_week(datetime.strptime(existing_data['last_period_date'], "%Y-%m-%d").date())
        tip = get_pregnancy_tip(week)
        response_text = (
            f"您已有資料！最後一次月經日是：{existing_data['last_period_date']}，"
            f"預計的生產日期是：{existing_data['estimated_due_date']}。\n\n"
            f"當前週數：{week} 週。\n"
            f"{tip}\n\n"
            "若您要更改日期，請再輸入一次最後一次月經日的第一天以更新。\n"
            "若無需更改，請輸入【確認】以確保日期資料正確。"
            )
        user_states[user_id] = "updating"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response_text)
            )
        return
    
    if not user_msg.strip():
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請輸入最後一次月經日的第一天。")
        )
        return
    
    
    try:
        last_period_date = datetime.strptime(user_msg, "%Y-%m-%d").date()
        
        # 計算今天的日期以及允許的最早日期 (今天 - 280 天)
        today = datetime.now().date()
        earliest_allowed_date = today - timedelta(days=280)
        
        # 檢查使用者輸入的日期是否在允許的區間內
        if earliest_allowed_date <= last_period_date <= today:
            estimated_due_date = last_period_date + timedelta(days=280)    # 日期在範圍內，計算預估的預產期
            save_user_data(user_id, last_period_date, estimated_due_date)  # 儲存使用者資料
            response_text = (
                f"最後一次月經的第一天為 {last_period_date.strftime('%Y-%m-%d')}，"
                f"預計的生產日期是 {estimated_due_date.strftime('%Y-%m-%d')}。\n"
                "再次點擊選單中【週期紀錄】功能可查看當前週數。"
            )
            user_mod[user_id] = 0
            user_states.pop(user_id, None)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=response_text)
            )     
        else:
            response = "請輸入從今天起最多 280 天內的正確日期。"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response))
            
    except ValueError:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請以YYYY-MM-DD格式輸入最後一次月經日的第一天日期。")
        )

# 用來儲存用戶回應狀態的簡單字典
user_states = {}

def send_weekly_reminder():
    """每周發送提醒給用戶"""
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT user_id, last_period_date FROM users")
        users = cursor.fetchall()

        for user in users:
            # 確保 last_period_date 已經是日期對象
            last_period_date = user['last_period_date']
            week = calculate_week(last_period_date)
            tip = get_pregnancy_tip(week)
            reminder_text = (
                f"每週提醒：\n"
                f"當前週數：{week} 週。\n"
                f"{tip}"
            )
            line_bot_api.push_message(user['user_id'], TextSendMessage(text=reminder_text))
    except Exception as e:
        print(f"周提醒發送錯誤: {e}")
    finally:
        cursor.close()
        conn.close()


def weekly_reminder_schedule():
    """設置每周的指定時間推播"""
    schedule.every().saturday.at("11:41").do(send_weekly_reminder)
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分鐘檢查一次
        
#--週期End--
    
#--關鍵字start--

# 假的搜尋函式，您需要根據需要實作這部分
def google_res(query, num_results=5, verbose=False):
    return f"針對 '{query}' 的搜尋結果將在這裡顯示。"

def system_intro(user_msg):
    return '你好！這是一個孕期AI問答資訊系統。\n請直接輸入您想知道的問題，例如：孕吐怎麼辦、孕期小腿抽筋等。\n本系統只會回覆您有關孕期的問題，請勿輸入不相關的問題。\n請特別注意，詢問完記得輸入【結束】再使用其他功能唷！'

def default_response(user_msg):
    sys_msg = ('請執行語意判斷工作，針對使用者提出的語句，提供至少兩種建議,並使用第二人稱,務必注意語意順暢,避免太白話或贅字情形'
               '如已經回答問題,請不要出現特別提醒：此問題與本系統無關，無法回應。字眼'
               '所有問題都以孕期方面來回答並給出建議,如使用者給出抽筋字眼,請直接以孕婦角度來回應,不要識別為一般人的抽筋'
               '如果出現任何有關孕期運動的問題,或是給出的建議有關孕期運動,推薦使用者到功能介面點選舒緩運動功能,回應時請注意:本系統只有舒緩運動功能並沒有食譜功能,請勿擅自加入回答'
               '嚴格審閱使用者輸入的關鍵字,若跟孕期無關，請回答:「此問題與本系統無關，無法回應。」')

    prompt = f'main question:{user_msg}'
    return next(chat_f([], sys_msg, prompt))

func_table = [
    {
        "chain": True,
        "func": google_res,
        "spec": {
            "name": "google_res",
            "description": "以 Google 搜尋結果回答有關孕期問題,並根據使用者提供的文字提供至少兩項建議,務必注意語意順暢,避免太白話或贅字情形。嚴格審閱使用者輸入的關鍵字,若跟孕期無關，請回答:「此問題與本系統無關，無法回應。」",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "要搜索的關鍵字",
                    }
                },
                "required": ["query"],
            },
        }
    },
    {
        "chain": False,
        "func": system_intro,
        "spec": {
            "name": "system_intro",
            "description": "回覆向用戶打招呼或進行系統簡介",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_msg": {
                        "type": "string",
                        "description": "用戶的 prompt",
                    }
                },
                "required": ["user_msg"],
            },
        }
    }
]

def get_reply_f(messages, stream=False, **kwargs):
    try:
        response = client.chat.completions.create(
            model='gpt-4',
            messages=messages,
            stream=stream
        )

        if stream:
            for chunk in response:
                if hasattr(chunk['choices'][0]['delta'], 'content'):
                    yield chunk['choices'][0]['delta'].content
        else:
            yield response.choices[0].message.content

    except openai.OpenAIError as err:
        reply = f"發生 {err.__class__.__name__} 錯誤\n{err}"
        print(reply)
        yield reply
    except Exception as err:
        reply = f"發生錯誤\n{err}"
        print(reply)
        yield reply

def chat_f(hist, sys_msg, user_msg, stream=False, **kwargs):
    # 呼叫 get_reply_f 時，不要傳遞 func_table 參數
    replies = get_reply_f(
        [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": user_msg}
        ],
        stream=stream, **kwargs  # 刪除 func_table 參數
    )
    
    reply_full = ''
    for reply in replies:
        reply_full += reply
        yield reply

    hist += [
        {"role": "user", "content": user_msg},
        {"role": "assistant", "content": reply_full}
    ]
    
    while len(hist) >= 2 * 2:  # 控制歷史記錄的回溯深度
        hist.pop(0)


#-----週期紀錄End-----

#-----運動Start-----

pregnancy_early_exercises = [
    {
        'image_url': 'https://i.imgur.com/7aZqqlh.jpg',
        'text1': '鳥狗式 (核心)',
        'text2': '1. 四足跪姿，膝蓋位於髖關節正下方。\n2. 雙手打直，手掌平貼在地板上，位於肩膀正下方。\n3. 頭部、頸椎、脊椎成同一直線，背部保持平直，注意不要聳肩。\n4. 收縮軀幹的肌肉力量，保持身體的穩定。\n5. 慢慢將右腳抬高，向後延伸至臀部的高度，同時左手臂也慢慢抬高，向前延伸至肩膀的高度。\n6. 維持此姿勢停留10秒，再慢慢回到起始姿勢。'
    },
    {
        'image_url': 'https://i.imgur.com/1dQJKPV.jpg',
        'text1': '橋式 (臀腿)',
        'text2': '1. 平躺於地面,雙腳彎曲,腳掌著地與肩同寬。\n2. 保持背部平直,提起臀部，緩緩向上移動,直到身體、臀部與膝蓋成一直線。\n3. 緩緩放下臀部回到起始位置。\n4. 注意膝蓋不要往內夾,與腳尖呈同一方向'
    },
    {
        'image_url': 'https://i.imgur.com/uoED02n.jpg',
        'text1': '屈膝伏地挺身 (上半身)',
        'text2': '1. 雙手撐地比肩膀稍寬,膝蓋著地且靠近,頭部到後肩呈一直線,雙手指尖朝前方,面朝下。\n2. 手臂彎曲身體向下,直到手肘呈90度彎曲,動作進行時,身體到膝蓋保持一直線。\n3. 雙臂伸直,胸口向上移動,回到起始位置。'
    }
]

pregnancy_mid_exercises = [
    {
        'image_url': 'https://i.imgur.com/gv4kBOS.jpg',
        'text1': '貓牛式 (脊椎活動、核心)',
        'text2': '1. 四足跪姿，確保手腕與肩膀和膝蓋與髖關節成一直線。\n2. 吸氣時，拱起背部（貓式），低頭看向肚臍。\n3. 呼氣時，凹下背部（牛式），抬頭看向天花板。\n4. 重複5-10次，配合呼吸緩慢進行。'
    },
    {
        'image_url': 'https://i.imgur.com/TFQEvkh.jpg',
        'text1': '蚌式 (臀腿)',
        'text2': '1. 側躺在地上,兩側髖骨對齊,雙腿彎曲呈90度,腳跟併攏。\n2. 將上方膝蓋抬高,同時穩定骨盆並保持雙腳腳跟併攏。\n3. 再度將膝蓋放下,然後換邊。\n4. 注意全程應保持核心,過程中勿晃動。'
    },
    {
        'image_url': 'https://i.imgur.com/TdrsPB7.jpg',
        'text1': '扶牆挺身 (上半身)',
        'text2': '1. 雙腳打開與髖同寬,膝蓋稍微彎曲,手掌平貼牆面,與肩同寬。\n2. 保持腹部、背部核心張力,身體前傾,手肘慢慢彎曲。\n3. 手肘與牆面呈現90度後,用胸肌的力量撐起身體。'
    }
]

pregnancy_end_exercises = [
    {
        'image_url': 'https://i.imgur.com/YrIEASq.jpg',
        'text1': '椅子深蹲 (臀腿)',
        'text2': '1. 找一個與小腿長度等高,穩定的椅子,並站在椅子前。\n2. 收緊核心背部打直,切勿彎腰駝背,緩緩下蹲直到臀部輕碰到椅子即可,不要猛然放鬆做到椅子上。\n3. 起身時保持核心收緊,感受臀部肌肉的收縮帶動身體站起。'
    },
    {
        'image_url': 'https://i.imgur.com/gsCiRO2.jpg', # 圖改
        'text1': '彈力繩單邊側舉手 (上半身)',
        'text2': '1. 兩腳平行站立,踩住彈力繩,手心向下單手握住手柄,另一手插腰或自然放下。\n2. 抬頭挺胸收緊核心並緊握。\n3. 呼氣時將手臂同時向側邊抬起至地面水平,吸氣還原。\n4. 注意過程注重胸部肌肉的收縮,以及身體的穩定性,避免晃動。'
    },
    {
        'image_url': 'https://i.imgur.com/4UCGKl2.jpg', # 圖改
        'text1': '彈力繩下拉 (上半身)',
        'text2': '1. 將彈力繩固定在較高的位置,坐在地面上,上身挺直保持下背平直,核心收緊保持身體穩定。\n2. 掌心向前,雙手握住彈力繩的手柄,吸氣,吐氣時收縮肩胛骨,利用背部的肌肉將兩隻手臂同時下拉。\n3. 上臂與身體約成45度,呈現挺胸姿勢,呼吸還原。'
    }
]

# 全局變數，存儲已經發送的練習
sent_early = []
sent_mid = []
sent_end = []        

    
@handler.add(PostbackEvent)
def handle_postback(event):
    data = event.postback.data
    if data == '胃食道逆流':
        sendImageAndTextMessage(event, 'https://i.imgur.com/vaXuW5U.jpg',
                                '束縛角式\n這個姿勢有助於打開臀部、骨盆和腹股溝，緩解胃酸倒流症狀，它還能夠強化大腿內側肌肉、股溝和膝蓋，改善姿勢和身體意識，以及減輕坐骨神經痛和腰部不適。',
                                '建議可以將背部靠在牆上，增加支撐，如果還是感到不適，也可以使用抱枕、墊子或折疊的毯子來提供額外的支撐。')
    elif data == '緩解噁心':
        sendImageAndTextMessage(event, 'https://i.imgur.com/dLnIxzL.jpg',
                                '山式\n這個站立式的姿勢可以幫助緩解噁心，同時強化脊椎，放鬆背部，增強腳部、腳踝、大腿和臀部的力量和活動能力，改善整體姿勢，並幫助放鬆身心。',
                                '如果在閉眼時感到頭暈或難以保持平衡，可以睜開眼睛，將注意力集中在手掌之間的空間。')
    elif data == '緩解便秘':
        sendImageAndTextMessage(event, 'https://i.imgur.com/Js8tPyd.jpg',
                                '嬰兒式\n此姿勢可以刺激消化系統，緩解便秘，同時平靜心靈、放鬆身體，伸展臀部、腹股溝、腳踝和背部，延長脊柱，打開胸部，並鼓勵深、放鬆的呼吸。',
                                '如果難以將頭靠在地板上，可以在額頭下方放置折疊的毯子，以減輕頸部的緊張和壓力，如果膝蓋感到不適或疼痛，也可以在膝蓋摺痕之間放置折疊毯子，以減輕壓力。')
    elif data == '腰酸背痛':
        sendImageAndTextMessage(event, 'https://i.imgur.com/YmRMYo4.jpg',
                                '三角伸展式可以有效緩解腰酸背痛。',
                                '1. 站立姿勢，雙腳分開約1米。\n2. 將右腳尖指向前方，左腳尖指向左方。\n3. 吸氣，雙手平舉至肩膀高度。\n4. 呼氣，上半身向右側彎，右手摸到右腳踝，左手指向天空。\n5. 保持5-10個呼吸，回到站立，換邊重複。')
    elif data == '腿部抽筋':
        sendImageAndTextMessage(event, 'https://i.imgur.com/wQjmktH.jpg',
                                '針對不同的腿部抽筋分為以下處理方式',
                                '1. 小腿抽筋：抓住腳掌慢慢往上扳回，保持腳尖向上翹的姿勢，即可拉動小腿肚的肌肉。\n2. 大腿前側抽筋：站立腿向後彎曲，用手抓住腳背，腳跟往屁股方向勾，延伸大腿前方肌肉。\n3. 大腿後側抽筋：坐著將兩條腿伸直，輕輕彎曲身體向前，將膝蓋用力往下壓，拉伸大腿後方。(此圖示為大腿後側抽筋舒緩方式)')
    elif data == '孕期水腫':
        sendImageAndTextMessage(event, 'https://i.imgur.com/mk7qHCw.jpg',
                                    '孕期水腫舒緩運動',
                                    '1. 坐在柔軟的瑜珈墊上，雙腿向前打直，先將左腳腳掌往身體方向輕輕下壓，做完後換右腳，左右腳輪流，重複10次。\n2. 若感到掌下壓的過程有點吃力，可以將拉直的毛巾繞過腳底板，雙手抓住毛巾兩端往腰部兩側拉。\n3. 感覺腿部肌肉獲得拉伸，就有助於改善孕婦水腫腳會痛的狀況。')

    elif data == 'early':
        sendRandomExercise(event, pregnancy_early_exercises, sent_early)
    elif data == 'mid':
        sendRandomExercise(event, pregnancy_mid_exercises, sent_mid)
    elif data == 'end':
        sendRandomExercise(event, pregnancy_end_exercises, sent_end)

def sendImageAndTextMessage(event, image_url, text1, text2):
    messages = [
        ImageSendMessage(
            original_content_url=image_url,
            preview_image_url=image_url
        ),
        TextSendMessage(text=text1),
        TextSendMessage(text=text2)
    ]
    line_bot_api.reply_message(event.reply_token, messages)

def sendRandomExercise(event, exercises, sent_list):
    remaining_exercises = [exercise for exercise in exercises if exercise not in sent_list]
    if not remaining_exercises:
        # 重置已發送列表
        sent_list.clear()
        remaining_exercises = exercises.copy()

    exercise = random.choice(remaining_exercises)
    sent_list.append(exercise)

    messages = [
        TextSendMessage(text=exercise['text1']),
        ImageSendMessage(
            original_content_url=exercise['image_url'],
            preview_image_url=exercise['image_url']
        ),
        TextSendMessage(text=exercise['text2'])
    ]
    line_bot_api.reply_message(event.reply_token, messages)

def sendCarousel(event):
    try:
        message = TemplateSendMessage(
            alt_text='舒緩運動',
            template=CarouselTemplate(
                columns=[
                    CarouselColumn(
                        thumbnail_image_url='https://i.imgur.com/ke0KTei.jpg',
                        title='瑜珈',
                        text='若你想要...',
                        actions=[
                            PostbackTemplateAction(
                                label='緩解胃食道逆流',
                                data='胃食道逆流'
                            ),
                            PostbackTemplateAction(
                                label='緩解噁心',
                                data='緩解噁心'
                            ),
                            PostbackTemplateAction(
                                label='緩解便秘',
                                data='緩解便秘'
                            ),
                        ]
                    ),
                    CarouselColumn(
                        thumbnail_image_url='https://i.imgur.com/37mwtZ6.jpg',
                        title="拉伸",
                        text='若你感覺...',
                        actions=[
                            PostbackTemplateAction(
                                label='腰酸背痛',
                                data='腰酸背痛'
                            ),
                            PostbackTemplateAction(
                                label='腿部抽筋',
                                data='腿部抽筋'
                            ),
                            PostbackTemplateAction(
                                label='孕期水腫',
                                data='孕期水腫'
                            ),
                        ]
                    ),
                    CarouselColumn(
                        thumbnail_image_url='https://i.imgur.com/5tzFXsE.jpg',
                        title='核心與各項肌力訓練',
                        text='請在以下選擇...',
                        actions=[
                            PostbackTemplateAction(
                                label='懷孕初期',
                                data='early'
                            ),
                            PostbackTemplateAction(
                                label='懷孕中期',
                                data='mid'
                            ),
                            PostbackTemplateAction(
                                label='懷孕晚期',
                                data='end'
                            ),
                        ]
                    ),
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, message)
    except Exception as e:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f'發生錯誤：{str(e)}'))
#-----運動End-----

#-----週期Start-----
PREGNANCY_TIPS = {
    range(0, 7): "0-6週：40週孕期的倒數從現在開始，此時還沒有明顯的懷孕跡象，體型尚無明顯變化。\n此時受精卵著床，您會發覺胸部脹痛及白帶中有血絲或有點狀出血，有些準媽咪則可能會感到下腹疼痛，像月經來潮前的症狀，且會月經停止，但少數準媽咪第一個月尚有少量似月經一樣出血的狀況。",
    range(7, 9): "7-8週：此階段的乳房變得細嫩、脹大且乳暈顏色變深。\n因為靜脈的血液供應量增加，血壓會比平常低，造成頭暈情形。此時的子宮大約一顆鵝蛋大，也因為孕期賀爾蒙的作祟，您可能會感到腹部絞痛。",
    range(9, 12): "9-11週：孕期的荷爾蒙開始大肆影響妳的身體，此時您的皮膚狀態會開始改變，可能會高頻率長痘痘、皮膚乾癢、長黑斑，這都是正常的懷孕症狀，甚至因為賀爾蒙讓子宮脹大，所以也較容易有頻尿的現象。",
    range(12, 13): "12週：您的子宮已增大突出至骨盆腔，因此可從下腹部摸到子宮。此週你可能會感覺到害喜困擾減少很多，這將令你食慾大增，不過即將進入懷孕中期的您，一定要好好控制體重，否則容易演變為妊娠糖尿病、妊娠高血壓等妊娠併發症。",
    range(13, 14): "13週：這週寶寶在媽媽的肚子裡，快速的長大，使得有些準媽咪的肚皮出現一條條的妊娠紋囉！",
    range(14, 16): "14-15週：此時子宮的大小約一小顆哈密瓜，噁心的感覺可能已經改善許多，過去不想吃的東西，現在可能可以接受了，使部分準媽咪一不小心吃的較多，造成體重往上，出現浮腫的困擾。",
    range(16, 20): "16-19週：這階段您開始感覺到胎動，您的下腹隆起已較明顯，到目前為止您大約會增加4至5公斤體重，乳房及乳頭的腫脹越來越明顯，有些準媽咪會覺得疼痛。\n由於子宮的膨大，也可能會稍微擠壓到心肺，所以您活動時，可能會覺得比較喘，另外，也有部分準媽咪會感到下腹疼痛",
    range(20, 22): "20-21週：您現在的子宮體積大約一個嬰兒頭部的大小，子宮底的高度到達肚臍處，所以使得您非常有孕味，這時因為子宮的增大，身體的重心起了變化，突出的腹部使您的重心往前移，為了保持平衡，以挺起肚子的方式較方便走路。",
    range(22, 25): "22-24週：現在胎動會較頻繁而且明顯，有時會有少量稀薄的乳汁分泌。目前子宮的位置約在肚臍上3.5公分至5公分處，這階段您可能會經常小腿抽筋，產生較為激烈的疼痛。",
    range(25, 27): "25-26週：此時子宮約是一顆足球的大小，除了寶寶體重成長，媽媽的體重也同步成長，妊娠紋可能會增加。\n妳會開始感覺到寶寶強烈的胎動。子宮的位置約是在肚臍和肋骨之間。",
    range(27, 29): "27-28週：這兩週您的體重開始持續增加直到生產。肚子可能會摸起來較硬、脹脹的，這是因為子宮收縮的關係。",
    range(29, 31): "29-30週：這時您的腹部隨寶寶的增大而迅速變大，睡覺時您可能會感覺肚子懸空不舒服，可使用輔助孕媽咪的抱枕以緩解不適，且需要長時間維持左側睡，可能使您不太適應。",
    range(31, 33): "31-32週：這兩週您所感受到的胎動又更明顯了，寶寶的一舉一動幾乎都是與您息息相關，由於子宮底一直往上升到橫隔膜，有時您的呼吸會受影響而有呼不過氣的感覺。",
    range(33, 35): "33-34週：您的體重目前為止應增加10公斤至13公斤，子宮底是在肚臍以上12、3公分處，因子宮日漸膨脹造成懷孕後期的不舒服日益明顯，如反胃、胸悶、易心悸、疲倦、呼吸困難等。\n由於胎頭正逐漸下降，這些不舒服的現象日後會獲得改善。",
    range(35, 37): "35-36週：這兩週結束後胎兒已往下降，胎位也已固定了。腹壁與子宮壁已變得較薄，寶寶的手肘、小腳和頭部有時會清楚地從妳的腹部突顯出來，而且宮縮、陣痛頻率也越來越高。",
    range(37, 39): "37-38週：您可能會覺得不舒服，因為寶寶的頭部頂住了陰道口，這兩週你的子宮頸甚至可能會漸漸變軟，為了會後續生產做準備。",
    range(39, 41): "39-40週：子宮頸及陰道也變軟，準備寶寶的出生，不規則陣痛、浮腫、靜脈曲張及痔瘡更加明顯。\n寶寶隨時會出生，但是不用擔心，只有5%的寶寶是在預產期那天出生的。",
}

def init_db():
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id VARCHAR(255) PRIMARY KEY,
                last_period_date DATE NOT NULL,
                estimated_due_date DATE NOT NULL
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
        print("資料表初始化完畢")
    except Exception as e:
        print(f"資料庫初始化錯誤: {e}")


def calculate_week(last_period_date):
    today = datetime.now().date()
    week_diff = (today - last_period_date).days // 7
    return week_diff

def get_pregnancy_tip(week):
    for weeks_range, tip in PREGNANCY_TIPS.items():
        if week in weeks_range:
            return tip
    return "無法找到對應的孕期資訊。"


        
#-----週期End-----

#-----日記Start-----

@app.route('/add_diary/<user_id>', methods=['POST'])
def add_diary(user_id):
    title = request.form.get('title')
    content = request.form.get('content')
    date = request.form.get('date')
    cycle = request.form.get('cycle')
    feeling = request.form.get('feeling')

    if not title or not content or not date or not cycle or not feeling:
        print("缺少一個或多個必填欄位！")
        return jsonify({'success': False, 'message': '未收到完整的日記内容'}), 400

    print(f"新增日記，標題: {title}, 內容: {content}, 日期: {date}, 週期: {cycle}, 心情: {feeling}")
    
    try:
        photos = request.files.getlist('photos')
        photo_urls = [upload_photo_to_github(photo, user_id) for photo in photos]
        photo_url = ','.join(photo_urls) if photo_urls else None

        #檢查照片URL是否產生成功
        print(f"產生的照片 URLs: {photo_urls}")

        new_journal = Journal(
            user_id=user_id,
            jtitle=title,
            jcontent=content,
            jdate=date,
            jcycle=cycle,
            jfeeling=feeling,
            photo_url=photo_url
        )
        db.session.add(new_journal)
        db.session.commit()

        print(f"使用 jid 建立的新日記： {new_journal.jid}")
        # 確保返回生成的 jid
        return jsonify({'success': True, 'diary': new_journal.serialize(), 'jid': new_journal.jid}), 201

    except Exception as e:
        db.session.rollback()
        print(f"Error adding diary: {e}")
        return jsonify({'success': False, 'message': '新增日記時發生錯誤'}), 500


@app.route('/get_diaries/<user_id>', methods=['GET'])
def get_diaries(user_id):
    try:
        # 根據 user_id 獲取該用戶的所有日記
        diaries = Journal.query.filter_by(user_id=user_id).all()

        # 檢查是否找到日記
        if not diaries:
           return jsonify({"success": True, "entries": []}), 200

        # 返回日記資料
        entries = []
        for diary in diaries:
            entry = {
                "jid": diary.jid,
                "title": diary.jtitle,
                "content": diary.jcontent,
                "date": diary.jdate,
                "cycle": diary.jcycle,
                "feeling": diary.jfeeling,
                "photos": diary.photo_url.split(',') if diary.photo_url else []
            }
            entries.append(entry)

        return jsonify({"success": True, "entries": entries}), 200

    except Exception as e:
        print(f"獲取日記時發生錯誤: {e}")
        return jsonify({'success': False, 'message': '獲取日記時發生錯誤'}), 500

@app.route('/get_diary/<user_id>/<diary_id>', methods=['GET'])
def get_diary(user_id, diary_id):
    try:
        # 根據 user_id 和 diary_id 獲取特定日記
        diary = Journal.query.filter_by(user_id=user_id, jid=diary_id).first()

        # 檢查是否找到日記
        if not diary:
            return jsonify({'success': False, 'message': '沒有找到日記'}), 404

        # 返回日記資料
        entry = {
            "jid": diary.jid,
            "title": diary.jtitle,
            "content": diary.jcontent,
            "date": diary.jdate,
            "cycle": diary.jcycle,
            "feeling": diary.jfeeling,
            "photos": diary.photo_url.split(',') if diary.photo_url else []
        }

        return jsonify({"success": True, "entry": entry}), 200

    except Exception as e:
        print(f"獲取日記時發生錯誤: {e}")
        return jsonify({'success': False, 'message': '獲取日記時發生錯誤'}), 500

@app.route('/edit_diary/<user_id>/<diary_id>', methods=['PUT'])
def edit_diary(user_id, diary_id):
    print(f"收到的 user_id: {user_id}, diary_id: {diary_id}")  # 日誌記錄

    # 檢查 diary_id 是否有效
    if not diary_id or diary_id == 'undefined':
        return jsonify({'success': False, 'message': '日記 ID 無效'}), 400

    try:
        # 根據 user_id 和 diary_id 查找日記
        diary = Journal.query.filter_by(user_id=user_id, jid=diary_id).first()
        print(f"查詢到的日記: {diary}")  # 打印查詢到的日記
        
        if not diary:
            return jsonify({'success': False, 'message': '未找到日記'}), 404

        # 從表單中取得更新後的數據
        title = request.form.get('edit-jtitle')
        content = request.form.get('edit-jcontent')
        date = request.form.get('edit-jdate')
        cycle = request.form.get('edit-jcycle')
        feeling = request.form.get('edit-jfeeling')

        print(f"更新日記，標題: {title}, 內容: {content}, 日期: {date}, 週期: {cycle}, 心情: {feeling}")
        
        # 更新日記的欄位，僅當有新數據時才進行更新
        if title and title != 'None':
            diary.jtitle = title
        if content and content != 'None':
            diary.jcontent = content
        if date and date != 'None':
            diary.jdate = date
        if cycle and cycle != 'None':
            diary.jcycle = cycle
        if feeling and feeling != 'None':
            diary.jfeeling = feeling

        # 處理照片更新，僅當有新照片時才更新
        photos = request.files.getlist('edit-jphoto')
        if photos and photos[0].filename:  # 確保有選擇照片
            print(f"收到的照片文件: {[photo.filename for photo in photos]}")
            photo_urls = [upload_photo_to_github(photo, user_id) for photo in photos]
            print(f"生成的照片 URLs: {photo_urls}")
            if photo_urls:  # 確保有新照片才更新
                diary.photo_url = ','.join(photo_urls)  # 更新照片 URL
                print(f"更新後的照片 URLs: {diary.photo_url}")

        # 提交數據庫的更改
        db.session.commit()
        
        # 再次查詢更新後的日記
        updated_diary = Journal.query.filter_by(user_id=user_id, jid=diary_id).first()
        print(f"更新後的日記: {updated_diary}")
        
        return jsonify({'success': True, 'diary': updated_diary.serialize(), 'jid': updated_diary.jid})
        
    except Exception as e:
        db.session.rollback()  # 出錯時回滾數據庫操作
        print(f"編輯日記時發生錯誤: {e}")
        return jsonify({'success': False, 'message': '編輯日記時發生錯誤'}), 500


@app.route('/delete_diary/<user_id>/<diary_id>', methods=['DELETE'])
def delete_diary(user_id, diary_id):
    try:
        # 查找符合 user_id 和 jid 的日記
        diary = Journal.query.filter_by(user_id=user_id, jid=diary_id).first()

        if diary:
            db.session.delete(diary)  # 刪除日記條目
            db.session.commit()       # 提交變更
            return jsonify({'success': True}), 200  # 成功響應
        else:
            return jsonify({'success': False, 'error': '日記未找到'}), 404  # 沒找到日記

    except Exception as e:
        # 發生錯誤時回傳錯誤訊息
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/upload_photo', methods=['POST'])
def upload_photo():
    try:
        # 從請求中獲取文件和 user_id
        image = request.files['photos']
        user_id = request.form.get('user_id')

        # 調用上傳函數並獲取圖片 URL
        photo_url = upload_photo_to_github(image, user_id)
        
        # 返回圖片 URL 給前端
        return jsonify({'success': True, 'photo_url': photo_url}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    
def upload_photo_to_github(image, user_id):
    if not user_id:
        raise ValueError("用戶 ID 不能為空")
    
    if not image.filename:
        raise ValueError("圖片檔案名不能為空")
    
    clean_filename = os.path.basename(image.filename).replace(" ", "_").replace("/", "_").replace("\\", "_")
    file_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FOLDER}/{user_id}/{clean_filename}"

    headers = {
        "Authorization": f"token {GITHUB_API_TOKEN}",
        "Content-Type": "application/json"
    }

    image_data = base64.b64encode(image.read()).decode('utf-8')

    # 先檢查文件是否存在
    existing_file = requests.get(file_url, headers=headers)
    sha = None
    if existing_file.status_code == 200:
        # 文件已經存在，提取其 sha 值
        sha = existing_file.json().get('sha')

    data = {
        "message": f"上傳圖片 {clean_filename}",
        "content": image_data,
        "branch": "main"
    }

    # 如果文件存在，需要提供 sha 值來更新它
    if sha:
        data["sha"] = sha

    # 上傳文件
    upload_response = requests.put(file_url, json=data, headers=headers)

    try:
        upload_response.raise_for_status()
        print(f"Successfully uploaded photo {clean_filename} to GitHub")
    except requests.RequestException as e:
        print(f"Error uploading photo: {e}")
        raise RuntimeError(f"圖片上傳失敗: {e}")

    response_json = upload_response.json()
    return response_json.get("content", {}).get("download_url")

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    # 获取用户 ID
    user_id = request.json.get('userId')
    print(f"收到的 userId: {user_id}")

    # 從資料庫中查詢該用戶的所有日记
    journals = Journal.query.filter_by(user_id=user_id).all()
    print(f"查詢到 {len(journals)} 篇日记")

    # 準備資料以傳遞到模板
    entries = [
    {
        'photo_urls': journal.photo_url.split(',') if journal.photo_url else [],
        'jtitle': journal.jtitle,
        'jcontent': journal.jcontent,
        'jcycle': journal.jcycle,
        'jdate': journal.jdate,
        'jfeeling': journal.jfeeling
    } 
    for journal in journals
]


    data = {
        'title': 'Be mom cares Journal',
        'entries': entries,  # 傳遞用户日記内容
        'date': datetime.now().strftime('%Y-%m-%d')  # 添加生成日期
    }

    # 渲染 HTML 模板並將資料傳遞進去
    rendered = render_template('template.html', **data)
    print("HTML 渲染成功")

    # 將渲染後的 HTML 轉換為 PDF
    pdf = pdfkit.from_string(rendered, False, configuration=config)
    print("PDF 生成成功")

    # 上傳 PDF 並返回
    upload_url = upload_pdf_to_github(pdf, user_id)
    print(f"PDF 上傳成功，URL: {upload_url}")
    return jsonify({'success': True, 'pdf_url': upload_url})


def generate_filename(user_id):
    # 獲取當前日期，格式為 YYYYMMDD
    current_date = datetime.now().strftime("%Y%m%d")
    clean_filename = f"{user_id}_{current_date}.pdf"  # 生成文件名
    return clean_filename

def upload_pdf_to_github(pdf_content, user_id):
    # 動態生成文件名和路徑，將 PDF 上傳到對應用戶的資料夾
    clean_filename = generate_filename(user_id)
    file_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FOLDER}/{user_id}/{clean_filename}"

    headers = {
        "Authorization": f"token {GITHUB_API_TOKEN}",
        "Content-Type": "application/json"
    }

    pdf_data = base64.b64encode(pdf_content).decode('utf-8')

    try:
        # 检查文件是否已经存在
        existing_file = requests.get(file_url, headers=headers)
        sha = None
        if existing_file.status_code == 200:
            sha = existing_file.json().get('sha')

        data = {
            "message": f"上传 PDF 文件 {clean_filename} 到用戶 {user_id} 資料夾",
            "content": pdf_data,
            "branch": "main"
        }

        if sha:
            data["sha"] = sha

        # 上传 PDF 至 GitHub
        upload_response = requests.put(file_url, json=data, headers=headers)
        upload_response.raise_for_status()

        response_json = upload_response.json()
        download_url = response_json.get("content", {}).get("download_url")
        if not download_url:
            raise RuntimeError("無法取得下載鏈接")
        return download_url

    except requests.RequestException as e:
        print(f"請求 GitHub API 時發生錯誤: {e}")
        raise RuntimeError(f"PDF 上傳失敗: {e}")
    except Exception as e:
        print(f"上傳過程中發生其他錯誤: {e}")
        raise RuntimeError(f"其他上傳錯誤: {e}")

#-----日記End-----
        

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


#-----日記Start-----


#-----日記End-----


if __name__ == '__main__':
    threading.Thread(target=weekly_reminder_schedule).start()
    app.run()
    
    
