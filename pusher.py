import requests
import json
import datetime
import pytz

class FeishuPusher:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def push(self, news_items):
        now = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
        date_str = now.strftime('%Y-%m-%d %H:%M')
        
        text_content = f"🚀 今日 AI 热点精选 | {date_str}\n\n"
        for idx, item in enumerate(news_items):
            title = item.get('title', 'No Title')
            summary = item.get('summary', '')
            url = item.get('url', '#')
            text_content += f"{idx+1}. {title}\n🔹 {summary}\n🔗 链接: {url}\n\n"
        
        payload = {"msg_type": "text", "content": {"text": text_content}}
        
        print(f"DEBUG: 正在发送到 Webhook (最后四位: ...{self.webhook_url[-4:]})")
        try:
            resp = requests.post(self.webhook_url, json=payload, timeout=10)
            print(f"DEBUG: 飞书返回: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")
