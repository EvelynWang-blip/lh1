import os
import requests
import feedparser
import datetime
import json
import pytz
from openai import OpenAI

class NewsFetcher:
    def __init__(self):
        # 1. 纯海外顶尖营销博客 RSS
        self.en_rss = [
            {"name": "Social Media Today", "url": "https://www.socialmediatoday.com/feeds/news/"},
            {"name": "Search Engine Journal", "url": "https://www.searchenginejournal.com/feed/"}
        ]
        # 2. 海外营销人社区
        self.en_community = "https://www.reddit.com/r/AI_Marketing/hot.json?limit=10"
        # 3. 中文出海深度观察 (仅保留 2 条 )
        self.cn_rss = "https://36kr.com/feed"

    def fetch_en(self ):
        news_list = []
        # 抓取博客 RSS
        for source in self.en_rss:
            try:
                feed = feedparser.parse(source["url"])
                for entry in feed.entries[:3]:
                    news_list.append({"title": entry.title, "url": entry.link, "source": source["name"], "lang": "en"})
            except Exception as e: print(f"Error {source['name']}: {e}")
        # 抓取 Reddit 社区热点
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(self.en_community, headers=headers, timeout=10)
            if resp.status_code == 200:
                for post in resp.json()['data']['children'][:4]:
                    p = post['data']
                    news_list.append({"title": p['title'], "url": f"https://www.reddit.com{p['permalink']}", "source": "Reddit Community", "lang": "en"} )
        except Exception as e: print(f"Error Reddit: {e}")
        return news_list

    def fetch_cn(self):
        news_list = []
        try:
            feed = feedparser.parse(self.cn_rss)
            # 仅筛选与“出海”、“跨境”、“全球”相关的深度内容
            for entry in feed.entries:
                if any(k in entry.title for k in ["出海", "跨境", "全球", "海外", "Amazon", "TikTok"]):
                    news_list.append({"title": entry.title, "url": entry.link, "source": "36氪出海", "lang": "cn"})
                if len(news_list) >= 4: break
        except Exception as e: print(f"Error CN: {e}")
        return news_list

def main():
    print("--- 启动全球营销 AI 灵感系统 ---")
    fetcher = NewsFetcher()
    en_news = fetcher.fetch_en()
    cn_news = fetcher.fetch_cn()
    
    # 严格按照 6 条海外 + 4 条深度出海的比例
    selected = en_news[:6] + cn_news[:4]
    
    # AI 总结：要求其针对 Facebook 私域运营给出建议
    final_news = []
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    try:
        prompt = """
        你是一名顶尖的跨境电商私域运营专家。请针对以下资讯给出建议：
        1. 英文标题请提供【中英对照】。
        2. 摘要请重点分析：该热点如何转化为 Facebook 群组的互动文案，或者揭示了海外用户什么样的新喜好。
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

    # 推送逻辑
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
    if webhook_url:
        now = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
        text_content = f"🌎 全球营销 & AI 灵感推送 | {now.strftime('%Y-%m-%d %H:%M')}\n\n"
        for idx, item in enumerate(final_news):
            text_content += f"{idx+1}. {item.get('title')}\n💡 运营启发: {item.get('summary')}\n🔗 链接: {item.get('url')}\n\n"
        
        requests.post(webhook_url, json={"msg_type": "text", "content": {"text": text_content}}, timeout=10)
    
    print("--- 运行结束 ---")

if __name__ == "__main__":
    main()
