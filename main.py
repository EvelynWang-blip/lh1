import os
import requests
import feedparser
import datetime
import json
import pytz
import re

class GlobalTrendRadar:
    def __init__(self):
        self.google_trends_rss = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
        self.marketing_rss = "https://www.socialmediatoday.com/feeds/news/"
        self.reddit_subs = ["tech", "ecommerce", "gadgets", "phonecases"]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64 ) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def extract_keywords(self, text):
        # 简单逻辑提取关键词：提取大写字母单词或特定电商关键词
        words = re.findall(r'\b[A-Z][a-z]+\b|\b[A-Z]{2,}\b|iPhone|TikTok|Magsafe|Casetify|Amazon|Facebook|Instagram', text)
        # 去重并格式化为标签
        unique_keywords = sorted(list(set(words)))
        return " ".join([f"#{w}" for w in unique_keywords[:4]]) if unique_keywords else "#Trend"

    def fetch_trends(self):
        data = {"hot_search": [], "platform_trends": [], "community_voice": []}
        
        # A. 抓取 Google 热搜
        try:
            resp = requests.get(self.google_trends_rss, headers=self.headers, timeout=15)
            feed = feedparser.parse(resp.content)
            for e in feed.entries[:5]:
                data["hot_search"].append({"title": e.title, "url": e.link, "tags": self.extract_keywords(e.title)})
        except: pass

        # B. 抓取社媒平台趋势
        try:
            resp = requests.get(self.marketing_rss, headers=self.headers, timeout=15)
            feed = feedparser.parse(resp.content)
            for e in feed.entries[:5]:
                data["platform_trends"].append({"title": e.title, "url": e.link, "tags": self.extract_keywords(e.title)})
        except: pass

        # C. 抓取 Reddit 社区热议
        for sub in self.reddit_subs:
            try:
                url = f"https://www.reddit.com/r/{sub}/hot.json?limit=3"
                resp = requests.get(url, headers=self.headers, timeout=15 )
                if resp.status_code == 200:
                    posts = resp.json().get('data', {}).get('children', [])
                    for post in posts:
                        p = post['data']
                        data["community_voice"].append({
                            "title": f"[{sub}] {p['title']}", 
                            "url": f"https://www.reddit.com{p['permalink']}",
                            "tags": self.extract_keywords(p['title'] )
                        })
            except: pass
        return data

def main():
    print("--- 启动【关键词雷达版】系统 ---")
    radar = GlobalTrendRadar()
    raw_data = radar.fetch_trends()
    
    # 构建推送文本 (完全跳过 AI 逻辑，直接展示关键词标签)
    now = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
    report_text = f"🌐 全球趋势雷达 & 私域灵感 | {now.strftime('%Y-%m-%d')}\n\n"
    
    if raw_data["hot_search"]:
        report_text += "🔥 Google/平台热搜 (发现页):\n"
        for item in raw_data["hot_search"][:5]:
            report_text += f"- {item['title']}\n  🏷️ 关键词: {item['tags']}\n  🔗 {item['url']}\n"
    
    if raw_data["platform_trends"]:
        report_text += "\n📱 社媒趋势/达人动态 (TikTok/YT/FB):\n"
        for item in raw_data["platform_trends"][:5]:
            report_text += f"- {item['title']}\n  🏷️ 关键词: {item['tags']}\n  🔗 {item['url']}\n"
    
    if raw_data["community_voice"]:
        report_text += "\n💬 垂直社区真实声音 (Reddit):\n"
        for item in raw_data["community_voice"][:6]:
            report_text += f"- {item['title']}\n  🏷️ 关键词: {item['tags']}\n  🔗 {item['url']}\n"

    if not any(raw_data.values()):
        report_text += "❌ 抱歉，今日全平台抓取均被拦截或无更新，请稍后再试。"

    report_text += "\n💡 运营提示：点击链接可直达海外热议现场，捕捉第一手文案灵感！"

    # 推送逻辑
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
    if webhook_url:
        payload = {"msg_type": "text", "content": {"text": report_text}}
        requests.post(webhook_url, json=payload, timeout=10)
    
    print("--- 运行结束 ---")

if __name__ == "__main__":
    main()
