import os
import requests
import feedparser
import datetime
import json
import pytz
from openai import OpenAI

class NewsFetcher:
    def __init__(self):
        # 1. 海外社媒趋势与案例 (TikTok/IG/私域)
        self.marketing_sources = [
            {"name": "Social Media Today", "url": "https://www.socialmediatoday.com/feeds/news/"},
            {"name": "Marketing Brew", "url": "https://www.marketingbrew.com/rss"}
        ]
        # 2. Reddit 用户深度讨论 (吐槽/需求 )
        self.reddit_url = "https://www.reddit.com/r/ecommerce/hot.json?limit=10"
        # 3. 竞品与品牌动态 (以 Casetify 等品牌为关键词 )
        self.brand_query = "https://hn.algolia.com/api/v1/search?query=Casetify+DTC+brand&tags=story"

    def fetch_all(self ):
        data = {"marketing": [], "reddit": [], "brands": []}
        # 抓取营销趋势
        for s in self.marketing_sources:
            try:
                feed = feedparser.parse(s["url"])
                for e in feed.entries[:5]:
                    data["marketing"].append({"title": e.title, "url": e.link, "source": s["name"]})
            except: pass
        # 抓取 Reddit 讨论
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(self.reddit_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                for post in resp.json()['data']['children'][:5]:
                    p = post['data']
                    data["reddit"].append({"title": p['title'], "url": f"https://www.reddit.com{p['permalink']}"} )
        except: pass
        # 抓取品牌动态
        try:
            resp = requests.get(self.brand_query, timeout=10)
            if resp.status_code == 200:
                for hit in resp.json().get('hits', [])[:3]:
                    data["brands"].append({"title": hit['title'], "url": hit.get('url') or f"https://news.ycombinator.com/item?id={hit['objectID']}"} )
        except: pass
        return data

def main():
    print("--- 启动私域运营内参系统 (含 AI 兜底) ---")
    fetcher = NewsFetcher()
    raw_data = fetcher.fetch_all()
    
    # 尝试使用 AI 总结
    report_text = ""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    try:
        prompt = """
        你是一名顶尖跨境私域运营专家。请根据提供的资讯，严格按照以下格式输出一份运营简报：
        ① 内容模块：TikTok爆款方向、IG审美趋势
        ② 用户模块：Reddit高互动讨论(吐槽/需求)、Amazon用户评论特征总结
        ③ 竞品模块：典型品牌动态(如Casetify)
        ④ 私域与选题：1个社群玩法案例、3-5条FB群组选题建议
        输出要求：中文，条理清晰。输出JSON，键为'report'。
        """
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": json.dumps(raw_data, ensure_ascii=False)}],
            response_format={"type": "json_object"}
        )
        report_text = json.loads(response.choices[0].message.content).get("report", "")
    except Exception as e:
        print(f"DEBUG: AI 总结失败 ({e})，进入无 AI 模式。")
        # --- 兜底逻辑：手动拼接原始数据 ---
        report_text = "⚠️ [提示: AI 额度不足，当前显示原始热点链接]\n\n"
        report_text += "📌 海外营销趋势:\n"
        for item in raw_data["marketing"][:5]:
            report_text += f"- {item['title']}\n  🔗 {item['url']}\n"
        report_text += "\n💬 Reddit 用户讨论:\n"
        for item in raw_data["reddit"][:3]:
            report_text += f"- {item['title']}\n  🔗 {item['url']}\n"
        report_text += "\n🏢 品牌/竞品动态:\n"
        for item in raw_data["brands"][:2]:
            report_text += f"- {item['title']}\n  🔗 {item['url']}\n"

    # 推送逻辑
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
    if webhook_url:
        now = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
        payload = {
            "msg_type": "text",
            "content": {
                "text": f"📊 私域运营深度内参 | {now.strftime('%Y-%m-%d')}\n\n{report_text}"
            }
        }
        requests.post(webhook_url, json=payload, timeout=10)
    
    print("--- 运行结束 ---")

if __name__ == "__main__":
    main()
