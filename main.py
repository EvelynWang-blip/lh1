import os
import requests
import feedparser
import datetime
import json
import pytz
from openai import OpenAI

class NewsFetcher:
    def __init__(self):
        self.en_sources = [
            {"name": "Hacker News", "url": "https://hn.algolia.com/api/v1/search?query=AI&tags=story&numericFilters=created_at_i>{timestamp}"},
            {"name": "Reddit ML", "url": "https://www.reddit.com/r/MachineLearning/hot.json?limit=10"}
        ]
        self.cn_sources = [
            {"name": "机器之心", "url": "https://www.jiqizhixin.com/rss"},
            {"name": "量子位", "url": "https://www.qbitai.com/feed"}
        ]

    def fetch_en(self ):
        news_list = []
        # 抓取过去 7 天以确保有数据
        yesterday = datetime.datetime.now() - datetime.timedelta(days=7)
        timestamp = int(yesterday.timestamp())
        try:
            resp = requests.get(self.en_sources[0]["url"].format(timestamp=timestamp), timeout=10)
            if resp.status_code == 200:
                for hit in resp.json().get('hits', [])[:10]:
                    news_list.append({"title": hit['title'], "url": hit.get('url') or f"https://news.ycombinator.com/item?id={hit['objectID']}", "source": "Hacker News", "lang": "en"} )
        except Exception as e: print(f"Error HN: {e}")
        return news_list

    def fetch_cn(self):
        news_list = []
        for source in self.cn_sources:
            try:
                feed = feedparser.parse(source["url"])
                for entry in feed.entries[:5]:
                    news_list.append({"title": entry.title, "url": entry.link, "source": source["name"], "lang": "cn"})
            except Exception as e: print(f"Error {source['name']}: {e}")
        return news_list

def main():
    print("--- 启动单文件推送系统 ---")
    
    # 1. 抓取
    fetcher = NewsFetcher()
    en_news = fetcher.fetch_en()
    cn_news = fetcher.fetch_cn()
    print(f"DEBUG: 抓取到 {len(en_news)} 英文, {len(cn_news)} 中文")

    # 2. 筛选 (6:4 比例)
    selected = en_news[:6] + cn_news[:4]
    
    # 3. AI 总结 (尝试)
    final_news = []
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    try:
        prompt = "You are an AI news curator. For English news, provide a bilingual title and Chinese summary. For Chinese news, provide a Chinese summary. Output JSON with key 'news'."
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": json.dumps(selected, ensure_ascii=False)}],
            response_format={"type": "json_object"}
        )
        final_news = json.loads(response.choices[0].message.content).get("news", [])
    except Exception as e:
        print(f"DEBUG: AI 总结失败 ({e})，使用原始标题。")
        for item in selected:
            final_news.append({"title": item["title"], "summary": "（点击链接查看原文）", "url": item["url"]})

    # 4. 推送
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
    if webhook_url:
        now = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
        text_content = f"🚀 今日 AI 热点精选 | {now.strftime('%Y-%m-%d %H:%M')}\n\n"
        for idx, item in enumerate(final_news):
            text_content += f"{idx+1}. {item.get('title')}\n🔹 {item.get('summary')}\n🔗 链接: {item.get('url')}\n\n"
        
        resp = requests.post(webhook_url, json={"msg_type": "text", "content": {"text": text_content}}, timeout=10)
        print(f"DEBUG: 飞书返回: {resp.text}")
    else:
        print("错误: 未找到 Webhook URL")
    
    print("--- 运行结束 ---")

if __name__ == "__main__":
    main()
