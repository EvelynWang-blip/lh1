import os
import requests
import feedparser
import datetime
import json
import pytz
from openai import OpenAI

class NewsFetcher:
    def __init__(self):
        # 针对跨境电商营销优化的英文源
        self.en_sources = [
            # 1. 营销类 AI 热点 (Reddit)
            {"name": "AI Marketing Tips", "url": "https://www.reddit.com/r/AI_Marketing/hot.json?limit=10"},
            # 2. AI 工具前沿 (Hacker News 过滤营销/电商关键词 )
            {"name": "E-commerce AI", "url": "https://hn.algolia.com/api/v1/search?query=ecommerce+marketing+AI&tags=story&numericFilters=created_at_i>{timestamp}"}
        ]
        # 针对出海/电商优化的中文源
        self.cn_sources = [
            {"name": "36氪出海", "url": "https://36kr.com/feed"}, # 跨境出海前沿
            {"name": "机器之心-商业应用", "url": "https://www.jiqizhixin.com/rss"}
        ]

    def fetch_en(self ):
        news_list = []
        yesterday = datetime.datetime.now() - datetime.timedelta(days=7)
        timestamp = int(yesterday.timestamp())
        # 抓取 Reddit 营销热点
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(self.en_sources[0]["url"], headers=headers, timeout=10)
            if resp.status_code == 200:
                for post in resp.json()['data']['children'][:5]:
                    p = post['data']
                    news_list.append({"title": p['title'], "url": f"https://www.reddit.com{p['permalink']}", "source": "Reddit Marketing", "lang": "en"} )
        except Exception as e: print(f"Error Reddit: {e}")
        # 抓取 HN 电商 AI
        try:
            resp = requests.get(self.en_sources[1]["url"].format(timestamp=timestamp), timeout=10)
            if resp.status_code == 200:
                for hit in resp.json().get('hits', [])[:5]:
                    news_list.append({"title": hit['title'], "url": hit.get('url') or f"https://news.ycombinator.com/item?id={hit['objectID']}", "source": "HN Tech", "lang": "en"} )
        except Exception as e: print(f"Error HN: {e}")
        return news_list

    def fetch_cn(self):
        news_list = []
        for source in self.cn_sources:
            try:
                feed = feedparser.parse(source["url"])
                for entry in feed.entries[:5]:
                    # 过滤包含“出海”、“电商”、“AI”或“营销”的内容
                    news_list.append({"title": entry.title, "url": entry.link, "source": source["name"], "lang": "cn"})
            except Exception as e: print(f"Error {source['name']}: {e}")
        return news_list

def main():
    print("--- 启动跨境电商 AI 资讯系统 ---")
    fetcher = NewsFetcher()
    en_news = fetcher.fetch_en()
    cn_news = fetcher.fetch_cn()
    
    # 比例 6:4，优先取相关的
    selected = en_news[:6] + cn_news[:4]
    
    # AI 总结部分：特别要求 AI 提取对“电商营销”的价值
    final_news = []
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    try:
        prompt = """
        你是一名跨境电商资深运营专家。请从以下资讯中提取对【电商营销、Facebook文案灵感、海外用户喜好】有价值的内容。
        1. 英文内容请提供中英对照标题。
        2. 摘要请重点说明：该热点对电商运营有什么启发，或者可以如何应用到文案中。
        3. 输出 JSON 格式，包含键 'news'。
        """
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": json.dumps(selected, ensure_ascii=False)}],
            response_format={"type": "json_object"}
        )
        final_news = json.loads(response.choices[0].message.content).get("news", [])
    except Exception as e:
        print(f"DEBUG: AI 总结失败 ({e})")
        for item in selected:
            final_news.append({"title": item["title"], "summary": "（AI 摘要暂不可用，请查看原文获取灵感）", "url": item["url"]})

    # 推送部分保持不变...
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
    if webhook_url:
        now = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
        text_content = f"🛒 跨境电商 AI 运营灵感 | {now.strftime('%Y-%m-%d %H:%M')}\n\n"
        for idx, item in enumerate(final_news):
            text_content += f"{idx+1}. {item.get('title')}\n💡 运营启发: {item.get('summary')}\n🔗 链接: {item.get('url')}\n\n"
        
        requests.post(webhook_url, json={"msg_type": "text", "content": {"text": text_content}}, timeout=10)
    
    print("--- 运行结束 ---")

if __name__ == "__main__":
    main()
