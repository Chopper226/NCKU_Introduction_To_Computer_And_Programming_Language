from flask import Flask, request
from pyngrok import ngrok
from linebot import LineBotApi
from linebot.v3 import WebhookHandler
from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError
import firebase_admin 
from firebase_admin import db
import google.generativeai as genai
import openai
import json
import logging
import time
import requests


# 設定你的 Line Bot 的 access token 和 secret 以及 firebase
access_token = 'YOUR ACCESS TOKEN'
secret = 'YOUR SECRET'
firebase_url = "YOUR FIREBASE URL"
cred = firebase_admin.credentials.Certificate("path/to/serviceAccountKey.json") 
firebase_admin.initialize_app(cred, {
    'databaseURL': firebase_url
})

ngrok_url=''

#自動更新WebhookURL
def auto_update_webhook_url():
    time.sleep(1) #等候1秒讓ngrok完成註冊新網址
    try:
        self_url = "http://localhost:4040/api/tunnels"
        res = requests.get(self_url)
        res_unicode = res.content.decode("utf-8")
        res_json = json.loads(res_unicode)  
        ngrok_url = res_json["tunnels"][0]["public_url"] 

        #開始更新
        line_put_endpoint_url = "https://api.line.me/v2/bot/channel/webhook/endpoint"
        data = {"endpoint": ngrok_url}
        headers = {
        "Authorization": "Bearer " + access_token ,
        "Content-Type": "application/json"
        }
        print(data)
        res = requests.put(line_put_endpoint_url, headers=headers, json=data)

        # 檢查回應狀態碼
        if res.status_code == 200:
            print("WebhookURL更新成功！")
        else:
            print("WebhookURL更新失敗")

    except Exception as e:
        print(f"Error: {e}")


app = Flask(__name__)
port = 5000

# Open a ngrok tunnel to the HTTP server
public_url = ngrok.connect(port).public_url
print(f" * ngrok tunnel \"{public_url}\" -> \"http://127.0.0.1:{port}\" ")


line_bot_api = LineBotApi(access_token)
handler = WebhookHandler(secret)

used_reply_tokens = set()

@app.route("/", methods=['POST'])
def linebot():
    body = request.get_data(as_text=True)  # 取得收到的訊息內容
    signature = request.headers['X-Line-Signature']

    try:
        # 驗證簽名
        handler.handle(body, signature)

        # 解析收到的訊息
        json_data = json.loads(body)
        msg = json_data['events'][0]['message']['text']
        tk = json_data['events'][0]['replyToken']
        conversation_id = json_data['events'][0]['source']['userId']

        if tk in used_reply_tokens:
            print("Reply token already used. Skipping reply.")
            return 'OK'

        # 回覆訊息
        reply_msg = process_message(msg,conversation_id)
        text_message = TextSendMessage(text=reply_msg)
        line_bot_api.reply_message(tk, text_message)

        used_reply_tokens.add(tk)
        print(f"Replied: {reply_msg}")

    except LineBotApiError as e:
        if e.status_code == 400 and 'Invalid reply token' in e.error.message:
             print("Invalid reply token. Please handle this error appropriately.")
    except Exception as e:
        print(f"Error: {e}")
        logging.error("Error: %s", str(e))
        return 'Error', 200  # 確保返回狀態碼200

    return 'OK'

def process_message(msg,conversation_id):

    # 處理收到的訊息並呼叫 OpenAI  Gemini API

    openai.api_key = 'YOUR OPENAI API'
    googleAiapi_key = "YOUR GEMINI API"
    ai_msg = msg[:4].lower()
    
    if msg == '!clear': # 清空對話歷史記錄
        db.reference(f'/conversations/{conversation_id}/ai').set({})
        db.reference(f'/conversations/{conversation_id}/gemini').set({})
        return "對話歷史已清空。"
    elif msg == '!clear opai':
        db.reference(f'/conversations/{conversation_id}/ai').set({})
        return "opai 的對話歷史已清空。"
    elif msg == '!clear gemi':
        db.reference(f'/conversations/{conversation_id}/gemini').set({})
        return "gemi 的對話歷史已清空。"
    
    elif ai_msg == 'opai':
        ref = db.reference(f'/conversations/{conversation_id}/ai')
        conversation_history = ref.get() or [] #抓取資料庫內容
        
        conversation_history.append({'role': 'user', 'content': msg[4:]})
        messages = [{'role': entry['role'], 'content': entry['content']} for entry in conversation_history]

        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=messages,
            max_tokens=256,
            temperature=0.5,
        )

        reply_msg = response['choices'][0]['message']['content'].strip()
        conversation_history.append({'role': 'assistant', 'content': reply_msg})
        ref.set(conversation_history)

    elif ai_msg == 'gemi' :
        ref = db.reference(f'/conversations/{conversation_id}/gemini')
        conversation_history = ref.get() or [] #抓取資料庫內容

        conversation_history.append({'role': 'user', 'content': msg[4:]})
        messages = [{'role': 'user', 'parts': [entry['content']]} for entry in conversation_history]
        
        genai.configure(api_key = googleAiapi_key)
        model = genai.GenerativeModel('gemini-pro')

        response = model.generate_content(messages)
        reply_msg = response.text.strip()
        conversation_history.append({'role': 'assistant', 'content': reply_msg})
        ref.set(conversation_history)
    else:
        reply_msg = msg

    return reply_msg

if __name__ == "__main__":
    auto_update_webhook_url()
    app.run()