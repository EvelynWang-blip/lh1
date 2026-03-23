import os
import json
from fetcher import NewsFetcher
from summarizer import NewsSummarizer
from pusher import FeishuPusher

def main():
    print("--- 启动推送系统 ---")
    fetcher = NewsFetcher()
    en_news = fetcher.fetch_en_news()
    cn_news = fetcher.fetch_cn_news()
    print(f"DEBUG: 抓取到 {len(en_news)} 条英文, {len(cn_news)} 条中文")

    summarizer = NewsSummarizer()
    selected_news = summarizer.summarize_and_select(en_news, cn_news)
    print(f"DEBUG: 准备推送 {len(selected_news)} 条热点")

    webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
    if webhook_url:
        pusher = FeishuPusher(webhook_url)
        pusher.push(selected_news)
    else:
        print("错误: 未找到 FEISHU_WEBHOOK_URL 环境变量")
    print("--- 运行结束 ---")

if __name__ == "__main__":
    main()
