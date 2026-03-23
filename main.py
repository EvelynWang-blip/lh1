import os
import sys
import json
from fetcher import NewsFetcher
from summarizer import NewsSummarizer
from pusher import FeishuPusher
from dotenv import load_dotenv

# Load environment variables for local testing
load_dotenv()

def main():
    print("--- 开始运行每日 AI 资讯推送系统 ---")
    
    # 1. Fetch news
    print("步骤 1: 正在抓取资讯...")
    fetcher = NewsFetcher()
    en_news = fetcher.fetch_en_news()
    cn_news = fetcher.fetch_cn_news()
    
    print(f"DEBUG: 抓取到英文资讯 {len(en_news)} 条")
    print(f"DEBUG: 抓取到中文资讯 {len(cn_news)} 条")
    
    if not en_news and not cn_news:
        print("错误: 未发现任何资讯，程序退出。")
        return

    # 2. Summarize and select
    print("步骤 2: 正在进行 AI 总结与筛选...")
    summarizer = NewsSummarizer()
    selected_news = summarizer.summarize_and_select(en_news, cn_news)
    
    print(f"DEBUG: AI 筛选后剩余 {len(selected_news)} 条热点")
    
    if not selected_news:
        print("错误: AI 未能筛选出任何热点，程序退出。")
        return

    # 3. Push to Feishu
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
    if not webhook_url:
        print("错误: 未配置 FEISHU_WEBHOOK_URL 环境变量。")
        return

    print(f"步骤 3: 正在推送到飞书 (Webhook 后四位: ...{webhook_url[-4:]})")
    pusher = FeishuPusher(webhook_url)
    pusher.push(selected_news)
    print("--- 运行结束 ---")

if __name__ == "__main__":
    main()
