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
        
        content = [
            [
                {
                    "tag": "text",
                    "text": f"📅 每日 AI 资讯聚合 | {date_str}\n\n"
                }
            ]
        ]
        
        for idx, item in enumerate(news_items):
            # For English news, item['title'] should be bilingual
            title = item.get('title', 'No Title')
            summary = item.get('summary', 'No Summary')
            url = item.get('url', '#')
            source = item.get('source', 'Unknown')
            
            content.append([
                {
                    "tag": "text",
                    "text": f"{idx+1}. {title}\n",
                    "style": ["bold"]
                },
                {
                    "tag": "text",
                    "text": f"🔹 {summary}\n"
                },
                {
                    "tag": "a",
                    "text": f"🔗 来源: {source}",
                    "href": url
                },
                {
                    "tag": "text",
                    "text": "\n\n"
                }
            ])
            
        return {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": "🚀 今日 AI 热点精选",
                        "content": content
                    }
                }
            }
        }

    def push(self, news_items):
        payload = self.format_news(news_items)
        try:
            resp = requests.post(self.webhook_url, json=payload, timeout=10)
            if resp.status_code == 200:
                print("Pushed to Feishu successfully.")
            else:
                print(f"Failed to push to Feishu: {resp.text}")
        except Exception as e:
            print(f"Error pushing to Feishu: {e}")

if __name__ == "__main__":
    # Test push
    test_news = [
        {"title": "OpenAI Launches New Model / OpenAI 发布新模型", "summary": "A new AI model has been launched with enhanced reasoning capabilities.", "url": "https://openai.com", "source": "OpenAI", "lang": "en"}
    ]
    pusher = FeishuPusher("YOUR_WEBHOOK_HERE")
    # pusher.push(test_news)
