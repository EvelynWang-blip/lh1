import os
import requests
import feedparser
import datetime
import json
import pytz
from openai import OpenAI

class GlobalTrendRadar:
    def __init__(self):
        # 1. 核心趋势源
        self.google_trends_rss = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
        self.marketing_rss = "https://www.socialmediatoday.com/feeds/news/"
        # 2. 垂直社区
        self.reddit_subs = ["tech", "ecommerce", "gadgets", "phonecases"]
        # 3. 模拟浏览器请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64 ) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def fetch_trends(self):
        data = {"hot_search": [], "platform_trends": [], "community_voice": []}
        
        # A. 抓取 Google 热搜 (增加超时重试)
        print("DEBUG: 正在抓取 Google Trends...")
        try:
            resp = requests.get(self.google_trends_rss, headers=self.headers, timeout=15)
            feed = feedparser.parse(resp.content)
            for e in feed.entries[:5]:
                data["hot_search"].append({"title": e.title, "url": e.link})
            print(f"DEBUG: Google Trends 抓取到 {len(data['hot_search'])} 条")
        except Exception as e:
            print(f"DEBUG: Google Trends 抓取失败: {e}")

        # B. 抓取社媒平台趋势 (TikTok/FB/YT 动态)
        print("DEBUG: 正在抓取社媒平台趋势...")
        try:
            resp = requests.get(self.marketing_rss, headers=self.headers, timeout=15)
            feed = feedparser.parse(resp.content)
            for e in feed.entries[:5]:
                data["platform_trends"].append({"title": e.title, "url": e.link})
            print(f"DEBUG: 社媒趋势抓取到 {len(data['platform_trends'])} 条")
        except Exception as e:
            print(f"DEBUG: 社媒趋势抓取失败: {e}")

        # C. 抓取 Reddit 社区热议 (强化反爬)
        print("DEBUG: 正在抓取 Reddit 社区讨论...")
        for sub in self.reddit_subs:
            try:
                url = f"https://www.reddit.com/r/{sub}/hot.json?limit=5"
                resp = requests.get(url, headers=self.headers, timeout=15 )
                if resp.status_code == 200:
                    posts = resp.json().get('data', {}).get('children', [])
                    for post in posts:
                        p = post['data']
                        data["community_voice"].append({"title": f"[{sub}] {p['title']}", "url": f"https://www.reddit.com{p['permalink']}"} )
                else:
                    print(f"DEBUG: Reddit r/{sub} 返回状态码 {resp.status_code}")
            except Exception as e:
                print(f"DEBUG: Reddit r/{sub} 抓取异常: {e}")
        print(f"DEBUG: Reddit 社区抓取到 {len(data['community_voice'])} 条")

        return data

def main():
    print("--- 启动【高稳定性趋势雷达】系统 ---")
    radar = GlobalTrendRadar()
    raw_data = radar.fetch_trends()
    
    # AI 总结逻辑 (保持不变，含兜底)
    report_text = ""
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    
    try:
        if not api_key: raise Exception("Missing API Key")
        prompt = "你是一名顶尖跨境电商趋势分析师。请根据抓取到的全平台热搜、社媒趋势、社区讨论，输出一份深度运营报告。包括：发现页热搜总结、科技电商热点、用户兴趣点吐槽、FB私域选题。输出JSON格式，键为'report'。"
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": json.dumps(raw_data, ensure_ascii=False)}],
            response_format={"type": "json_object"}
        )
        report_text = json.loads(response.choices[0].message.content).get("report", "")
    except Exception as e:
        print(f"DEBUG: AI 总结失败 ({e})，进入结构化聚合模式。")
        report_text = "⚠️ [AI 额度不足，为您聚合全平台实时热点]\n\n"
        
        if raw_data["hot_search"]:
            report_text += "🔥 Google/平台热搜 (发现页):\n"
            for item in raw_data["hot_search"][:5]:
                report_text += f"- {item['title']}\n  🔗 {item['url']}\n"
        
        if raw_data["platform_trends"]:
            report_text += "\n📱 社媒趋势/达人动态 (TikTok/YT/FB):\n"
            for item in raw_data["platform_trends"][:5]:
                report_text += f"- {item['title']}\n  🔗 {item['url']}\n"
        
        if raw_data["community_voice"]:
            report_text += "\n💬 垂直社区真实声音 (Reddit):\n"
            for item in raw_data["community_voice"][:6]:
                report_text += f"- {item['title']}\n  🔗 {item['url']}\n"
        
        if not any(raw_data.values()):
            report_text = "❌ 抱歉，今日全平台抓取均被拦截或无更新，请稍后再试或检查网络设置。"

    # 推送逻辑
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
    if webhook_url:
        now = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
        payload = {"msg_type": "text", "content": {"text": f"🌐 全球趋势雷达 & 私域灵感 | {now.strftime('%Y-%m-%d')}\n\n{report_text}"}}
        requests.post(webhook_url, json=payload, timeout=10)
    
    print("--- 运行结束 ---")

if __name__ == "__main__":
    main()
