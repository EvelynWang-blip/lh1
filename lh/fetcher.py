import requests
import feedparser
from bs4 import BeautifulSoup
import datetime
import pytz

class NewsFetcher:
    def __init__(self):
        self.en_sources = [
            {"name": "Hacker News (AI)", "url": "https://hn.algolia.com/api/v1/search?query=AI&tags=story&numericFilters=created_at_i>{timestamp}"},
            {"name": "Reddit Machine Learning", "url": "https://www.reddit.com/r/MachineLearning/hot.json?limit=10"},
            {"name": "OpenAI Blog", "url": "https://openai.com/news/rss.xml"},
            {"name": "DeepMind Blog", "url": "https://deepmind.google/blog/rss.xml"}
        ]
        self.cn_sources = [
            {"name": "机器之心", "url": "https://www.jiqizhixin.com/rss"},
            {"name": "量子位", "url": "https://www.qbitai.com/feed"},
            {"name": "36氪 AI", "url": "https://36kr.com/feed"}
        ]

    def fetch_en_news(self):
        news_list = []
        # Get timestamp for last 24 hours
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
        timestamp = int(yesterday.timestamp())

        # Hacker News
        try:
            hn_url = self.en_sources[0]["url"].format(timestamp=timestamp)
            resp = requests.get(hn_url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                for hit in data.get('hits', [])[:10]:
                    news_list.append({
                        "title": hit['title'],
                        "url": hit.get('url') or f"https://news.ycombinator.com/item?id={hit['objectID']}",
                        "source": "Hacker News",
                        "lang": "en"
                    })
        except Exception as e:
            print(f"Error fetching HN: {e}")

        # Reddit
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(self.en_sources[1]["url"], headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                for post in data['data']['children']:
                    post_data = post['data']
                    news_list.append({
                        "title": post_data['title'],
                        "url": f"https://www.reddit.com{post_data['permalink']}",
                        "source": "Reddit r/ML",
                        "lang": "en"
                    })
        except Exception as e:
            print(f"Error fetching Reddit: {e}")

        return news_list

    def fetch_cn_news(self):
        news_list = []
        for source in self.cn_sources:
            try:
                feed = feedparser.parse(source["url"])
                for entry in feed.entries[:5]:
                    news_list.append({
                        "title": entry.title,
                        "url": entry.link,
                        "source": source["name"],
                        "lang": "cn"
                    })
            except Exception as e:
                print(f"Error fetching {source['name']}: {e}")
        return news_list

if __name__ == "__main__":
    fetcher = NewsFetcher()
    en = fetcher.fetch_en_news()
    cn = fetcher.fetch_cn_news()
    print(f"Fetched {len(en)} English news and {len(cn)} Chinese news.")
