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
    # 1. Fetch news
    print("Fetching news...")
    fetcher = NewsFetcher()
    en_news = fetcher.fetch_en_news()
    cn_news = fetcher.fetch_cn_news()
    
    if not en_news and not cn_news:
        print("No news found. Exiting.")
        return

    # 2. Summarize and select
    print(f"Summarizing {len(en_news)} EN and {len(cn_news)} CN news...")
    summarizer = NewsSummarizer()
    selected_news = summarizer.summarize_and_select(en_news, cn_news)
    
    if not selected_news:
        print("No news selected. Exiting.")
        return

    # 3. Push to Feishu
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
    if not webhook_url:
        print("FEISHU_WEBHOOK_URL not set. Exiting.")
        # Print for debug
        print(json.dumps(selected_news, indent=2, ensure_ascii=False))
        return

    print("Pushing to Feishu...")
    pusher = FeishuPusher(webhook_url)
    pusher.push(selected_news)
    print("Done!")

if __name__ == "__main__":
    main()
