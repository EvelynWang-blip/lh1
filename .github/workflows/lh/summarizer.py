import os
from openai import OpenAI
import json

class NewsSummarizer:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        )

    def summarize_and_select(self, en_news, cn_news):
        """
        Input: Lists of news items
        Goal: Select 10 hottest news (6:4 ratio), summarize and translate if needed
        """
        # Select 6 English news and 4 Chinese news
        selected_en = en_news[:6]
        selected_cn = cn_news[:4]

        all_news = selected_en + selected_cn
        results = []

        prompt = """
        You are an AI news curator. Your task is to:
        1. Review the following news list.
        2. For English news, provide a bilingual (Chinese/English) title and a concise summary in Chinese.
        3. For Chinese news, provide a concise summary in Chinese.
        4. Output the result in a JSON format under the key "news":
           {
             "news": [
               {
                 "title": "Bilingual Title / 中文标题",
                 "summary": "Chinese Summary",
                 "url": "original_url",
                 "source": "source_name",
                 "lang": "en/cn"
               }
             ]
           }
        """

        content = json.dumps(all_news, ensure_ascii=False)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": content}
                ],
                response_format={"type": "json_object"}
            )
            
            summary_data = json.loads(response.choices[0].message.content)
            results = summary_data.get("news", [])
        except Exception as e:
            print(f"Error in summarization: {e}")
            # Fallback to original news if AI fails
            for item in all_news:
                results.append({
                    "title": item["title"],
                    "summary": "AI 摘要生成失败，请点击链接查看原文。",
                    "url": item["url"],
                    "source": item["source"],
                    "lang": item["lang"]
                })

        return results[:10]
