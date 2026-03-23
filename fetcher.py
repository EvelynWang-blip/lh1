import requests
import json
import datetime
import pytz

class FeishuPusher:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def format_news(self, news_items):
        now = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
        date_str = now.strftime('%Y-%m-%d %H:%M')
        
        # 使用最简单的纯文本格式测试
        text_content = f"📅 每日 AI 资讯聚合 | {date_str}\n\n"
        
        for idx, item in enumerate(news_items):
            title = item.get('title', 'No Title')
            url = item.get('url', '#')
            source = item.get('source', 'Unknown')
            text_content += f"{idx+1}. {title}\n🔗 来源: {source}\n🔗 链接: {url}\n\n"
            
        return {
            "msg_type": "text",
            "content": {
                "text": text_content
            }
        }

    def push(self, news_items):
        payload = self.format_news(news_items)
        print(f"DEBUG: 正在推送 Payload 到飞书...")
        try:
            resp = requests.post(self.webhook_url, json=payload, timeout=10)
            print(f"DEBUG: 飞书返回状态码: {resp.status_code}")
            print(f"DEBUG: 飞书返回内容: {resp.text}")
            if resp.status_code == 200:
                print("Pushed to Feishu successfully.")
            else:
                print(f"Failed to push to Feishu: {resp.text}")
        except Exception as e:
            print(f"Error pushing to Feishu: {e}")
