import requests
import json
import os
from dotenv import load_dotenv

load_dotenv(verbose=True)

client_ID = os.getenv('NAVER_CLIENT_ID')
client_Secret = os.getenv('NAVER_CLIENT_SECRET')

news_url = 'https://openapi.naver.com/v1/search/news.json'
headers = {
  'X-Naver-Client-Id':client_ID,
  'X-Naver-Client-Secret': client_Secret,
}

def get_title(keyword, titles):
  params = {
    'query':keyword,
    'display':titles
  }

  response = requests.get(news_url, params, headers=headers)
  results = json.loads(response.text)['items']

  return results