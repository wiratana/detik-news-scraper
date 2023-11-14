from bs4 import BeautifulSoup #import beautiful soup
import requests
from mongoengine import *
import os
from dotenv import load_dotenv

load_dotenv()

class Article(Document):
  title = StringField(required=True)
  author = StringField(required=True)
  date_published = StringField(required=True)
  content = StringField(required=True)

# scrapper for detik.com/bali/hukum-kriminal Done
def detik_scraper(index):
  if index == 0:
    return 0

  html_content = requests.get('https://www.detik.com/bali/hukum-kriminal/indeks/{index}'.format(index=index))
  soup = BeautifulSoup(html_content.content, 'lxml')
  article_list = soup.find_all('article', class_='list-content__item')
  
  for article in article_list:
    html_content = requests.get(article.a["href"])
    soup = BeautifulSoup(html_content.content, 'lxml')

    # pre process cleansing
    for i in range(len(soup.find_all('p', class_='para_caption'))):
      soup.find('p', class_='para_caption').decompose()

    article = {
        "title": (soup.find('h1', class_='detail__title')).text,
        "author": (soup.find('div', class_='detail__author')).text,
        "date_published": (soup.find('div', class_='detail__date')).string,
        "content": ' '.join([p.text for p in soup.find_all('p')])
    }

    # pra process cleansing
    article["content"] = article["content"].strip()
    article["title"] = article["title"].strip()
    article["title"] = article["title"].replace("\n", "")

    after_process_article = Article(**article)
    after_process_article.save()
  return detik_scraper(index - 1)

def main():
  connect(db=os.environ.get("DB_NAME"),host=os.environ.get("DB_URI"))
  detik_scraper(100)

if __name__ == "__main__":
  main()
