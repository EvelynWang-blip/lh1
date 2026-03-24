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
    print("--- 启动私域运营深度内参系统 ---")
    fetcher = NewsFetcher()
    raw_data = fetcher.fetch_all()
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    try:
        # 核心 AI 处理逻辑：严格按照用户要求的模块输出
        prompt = """
        你是一名顶尖跨境私域运营专家。请根据提供的资讯，严格按照以下格式输出一份运营简报：
        
        ① 内容模块：
        - TikTok：提取3条近期爆款内容/方向
        - IG：提取3个海外审美/视觉趋势
        
        ② 用户模块：
        - Reddit：总结3条高互动讨论（重点提取用户吐槽或未满足的需求）
        - Amazon：基于趋势总结10条典型用户评论特征（风格/价格/偏好）
        
        ③ 竞品模块：
        - 监控2个典型品牌动态（如Casetify或类似DTC品牌的新动作）
        
        ④ 私域与选题：
        - 1个社群玩法/营销案例总结
        - 提供3-5条可直接用于Facebook私域群组的【选题建议】
        
        输出要求：中文，条理清晰，直接给干货。输出JSON，键为'report'。
        """
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": json.dumps(raw_data, ensure_ascii=False)}],
            response_format={"type": "json_object"}
        )
        report_text = json.loads(response.choices[0].message.content).get("report", "生成失败")
    except Exception as e:
        report_text = f"AI 处理出错: {e}"

    # 推送逻辑
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
    if webhook_url:
        now = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
        # 飞书推送格式优化
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
