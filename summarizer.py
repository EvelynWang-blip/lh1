import os
from openai import OpenAI
import json

class NewsSummarizer:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)

    def summarize_and_select(self, en_news, cn_news):
        all_news = en_news[:6] + cn_news[:4]
        results = []
        
        # 尝试调用 AI 进行翻译和总结
        try:
            prompt = "You are an AI news curator. For English news, provide a bilingual title and Chinese summary. For Chinese news, provide a Chinese summary. Output JSON with key 'news'."
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": prompt}, {"role": "user", "content": json.dumps(all_news, ensure_ascii=False)}],
                response_format={"type": "json_object"}
            )
            results = json.loads(response.choices[0].message.content).get("news", [])
        except Exception as e:
            print(f"DEBUG: AI 总结失败 (原因: {e})，将使用原始标题推送。")
            # 兜底：如果 AI 报错（如额度不足），直接返回原始数据
            for item in all_news:
                results.append({
                    "title": item["title"],
                    "summary": "（AI 摘要生成失败，请点击链接查看原文）",
                    "url": item["url"],
                    "source": item["source"]
                })
        return results[:10]
