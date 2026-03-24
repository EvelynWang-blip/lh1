import os
import requests
import feedparser
import datetime
import json
import pytz
from openai import OpenAI

class NewsFetcher:
    def __init__(self):
        # 1. 垂直类目关键词配置
        self.keywords = [
            "TikTok viral phone case", 
            "iPhone accessories trend", 
            "Magsafe accessories trending",
            "Casetify review Reddit",
            "aesthetic iPhone setup TikTok"
        ]
        # 2. 吐槽/需求类关键词 (用于抓取用户痛点)
        self.complaint_keywords = ["phone case complaints reddit", "iPhone case problems"]

    def fetch_targeted_news(self):
        data = {"trends": [], "complaints": [], "brands": []}
        
        # A. 从 Reddit 抓取手机配件深度讨论 (r/phonecases, r/iphone)
        reddit_subs = ["phonecases", "iphone", "magsafe"]
        for sub in reddit_subs:
            try:
                headers = {'User-Agent': 'Mozilla/5.0'}
                url = f"https://www.reddit.com/r/{sub}/hot.json?limit=5"
                resp = requests.get(url, headers=headers, timeout=10 )
                if resp.status_code == 200:
                    for post in resp.json()['data']['children']:
                        p = post['data']
                        data["trends"].append({"title": f"[{sub}] {p['title']}", "url": f"https://www.reddit.com{p['permalink']}"} )
            except: pass

        # B. 从 Hacker News/Google News 聚合中抓取 Casetify 及配件动态
        try:
            brand_url = "https://hn.algolia.com/api/v1/search?query=Casetify+iPhone+accessories&tags=story"
            resp = requests.get(brand_url, timeout=10 )
            if resp.status_code == 200:
                for hit in resp.json().get('hits', [])[:5]:
                    data["brands"].append({"title": hit['title'], "url": hit.get('url') or f"https://news.ycombinator.com/item?id={hit['objectID']}"} )
        except: pass

        return data

def main():
    print("--- 启动【手机配件】私域深度内参系统 ---")
    fetcher = NewsFetcher()
    raw_data = fetcher.fetch_targeted_news()
    
    # 尝试使用 AI 总结
    report_text = ""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    try:
        prompt = """
        你是一名资深的手机配件跨境电商专家。请根据提供的资讯，围绕【手机壳、Magsafe、iPhone周边】输出报告：
        1. TikTok/IG爆款：总结近期流行的手机壳风格、审美趋势。
        2. 用户痛点：总结Reddit上对手机壳的吐槽（如发黄、不防摔、Magsafe吸力弱等）。
        3. 竞品动态：重点分析Casetify等品牌的最新动作。
        4. 文案选题：提供3-5个适合FB群组的互动选题。
        输出JSON，键为'report'。
        """
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": json.dumps(raw_data, ensure_ascii=False)}],
            response_format={"type": "json_object"}
        )
        report_text = json.loads(response.choices[0].message.content).get("report", "")
    except Exception as e:
        print(f"DEBUG: AI 总结失败 ({e})，进入精准兜底模式。")
        # --- 精准兜底：直接按类目输出抓取到的垂直热点 ---
        report_text = "⚠️ [AI 总结暂不可用，以下为您搜集到的垂直类目热点]\n\n"
        report_text += "🔥 手机配件/Magsafe 热门讨论:\n"
        for item in raw_data["trends"][:6]:
            report_text += f"- {item['title']}\n  🔗 {item['url']}\n"
        report_text += "\n🏢 竞品/品牌动态 (Casetify等):\n"
        for item in raw_data["brands"][:4]:
            report_text += f"- {item['title']}\n  🔗 {item['url']}\n"
        report_text += "\n💡 运营提示：请重点关注 Reddit 帖子中的评论区，那里藏着用户最真实的购买动机和吐槽！"

    # 推送逻辑
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
    if webhook_url:
        now = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
        payload = {
            "msg_type": "text",
            "content": {
                "text": f"📱 手机配件私域运营内参 | {now.strftime('%Y-%m-%d')}\n\n{report_text}"
            }
        }
        requests.post(webhook_url, json=payload, timeout=10)
    
    print("--- 运行结束 ---")

if __name__ == "__main__":
    main()
