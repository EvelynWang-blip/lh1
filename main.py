import os
import requests
import feedparser
import datetime
import json
import pytz
from openai import OpenAI

class GlobalTrendRadar:
    def __init__(self):
        # 1. 核心趋势源 (覆盖 TikTok/YT/FB/Google 发现页聚合)
        self.trend_sources = [
            {"name": "Google Trends (Tech)", "url": "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"},
            {"name": "Social Media Today (Platform Trends )", "url": "https://www.socialmediatoday.com/feeds/news/"},
            {"name": "Marketing Brew (Industry Hot )", "url": "https://www.marketingbrew.com/rss"}
        ]
        # 2. 垂直社区发现页 (Reddit )
        self.reddit_subs = ["tech", "ecommerce", "gadgets", "phonecases"]

    def fetch_trends(self):
        data = {"hot_search": [], "platform_trends": [], "community_voice": []}
        
        # A. 抓取 Google 发现页热搜
        try:
            feed = feedparser.parse(self.trend_sources[0]["url"])
            for e in feed.entries[:5]:
                data["hot_search"].append({"title": e.title, "url": e.link})
        except: pass

        # B. 抓取 TikTok/YT/FB 平台趋势与达人动态
        try:
            feed = feedparser.parse(self.trend_sources[1]["url"])
            for e in feed.entries[:5]:
                data["platform_trends"].append({"title": e.title, "url": e.link, "source": "SocialMediaToday"})
        except: pass

        # C. 抓取 Reddit 垂直社区热议 (用户兴趣/吐槽)
        for sub in self.reddit_subs:
            try:
                headers = {'User-Agent': 'Mozilla/5.0'}
                url = f"https://www.reddit.com/r/{sub}/hot.json?limit=3"
                resp = requests.get(url, headers=headers, timeout=10 )
                if resp.status_code == 200:
                    for post in resp.json()['data']['children']:
                        p = post['data']
                        data["community_voice"].append({"title": f"[{sub}] {p['title']}", "url": f"https://www.reddit.com{p['permalink']}"} )
            except: pass

        return data

def main():
    print("--- 启动【全球趋势雷达】私域内参系统 ---")
    radar = GlobalTrendRadar()
    raw_data = radar.fetch_trends()
    
    # 尝试使用 AI 深度总结
    report_text = ""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    try:
        prompt = """
        你是一名顶尖跨境电商趋势分析师。请根据以下抓取到的【全平台热搜、社媒趋势、社区讨论】，输出一份深度运营报告：
        1. 发现页热搜：总结Google/TikTok/YT上的实时热点及达人动向。
        2. 科技电商热点：重点分析跨境电商、3C配件行业的节日热点及行业动态。
        3. 用户兴趣点：从Reddit讨论中提取用户的真实兴趣、需求及对现有产品的吐槽。
        4. FB私域选题：基于以上热点，提供3-5个高互动的文案选题建议。
        输出JSON，键为'report'。
        """
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": json.dumps(raw_data, ensure_ascii=False)}],
            response_format={"type": "json_object"}
        )
        report_text = json.loads(response.choices[0].message.content).get("report", "")
    except Exception as e:
        print(f"DEBUG: AI 总结失败 ({e})，进入结构化聚合模式。")
        # --- 结构化聚合模式：无AI时也能清晰看到分类热点 ---
        report_text = "⚠️ [AI 额度不足，为您聚合全平台实时热点]\n\n"
        report_text += "🔥 Google/平台热搜 (发现页):\n"
        for item in raw_data["hot_search"][:4]:
            report_text += f"- {item['title']}\n  🔗 {item['url']}\n"
        report_text += "\n📱 社媒趋势/达人动态 (TikTok/YT/FB):\n"
        for item in raw_data["platform_trends"][:4]:
            report_text += f"- {item['title']}\n  🔗 {item['url']}\n"
        report_text += "\n💬 垂直社区真实声音 (Reddit):\n"
        for item in raw_data["community_voice"][:5]:
            report_text += f"- {item['title']}\n  🔗 {item['url']}\n"
        report_text += "\n💡 节日提醒：请关注近期全球节日热度，将热搜词融入您的文案中！"

    # 推送逻辑
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
    if webhook_url:
        now = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
        payload = {
            "msg_type": "text",
            "content": {
                "text": f"🌐 全球趋势雷达 & 私域灵感 | {now.strftime('%Y-%m-%d')}\n\n{report_text}"
            }
        }
        requests.post(webhook_url, json=payload, timeout=10)
    
    print("--- 运行结束 ---")

if __name__ == "__main__":
    main()
