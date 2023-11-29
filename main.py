import json
from time import sleep

from bs4 import BeautifulSoup #import beautiful soup
import requests
from mongoengine import *
import os
from dotenv import load_dotenv
from deep_translator import GoogleTranslator
from datetime import datetime
import openai

load_dotenv()

class Headline(EmbeddedDocument):
  en = StringField(required=True)
  id = StringField(required=True)

class Content(EmbeddedDocument):
  en = StringField(required=True)
  id = StringField(required=True)

class Summary(EmbeddedDocument):
  en = StringField(required=True)
  id = StringField(required=True)

class Article(Document):
  headline = EmbeddedDocumentField(Headline)
  author = StringField(required=True)
  date_published = DateTimeField()
  content = EmbeddedDocumentField(Content)
  location = StringField()
  link_to_origin = StringField(required=True)
  category = StringField(required=True)
  summary = EmbeddedDocumentField(Summary)
  timezone = StringField(required=True)

translator = GoogleTranslator(source='id', target='en')
openai.api_key = os.environ.get("OPEN_API_KEY")

# scrapper for detik.com/bali/hukum-kriminal Done
def detik_scraper(index):
  if index == 0:
    return 0

  html_content = requests.get('https://www.detik.com/bali/hukum-kriminal/indeks/{index}'.format(index=index))
  soup = BeautifulSoup(html_content.content, 'lxml')
  article_list = soup.find_all('article', class_='list-content__item')
  
  for article in article_list:
    html_content = requests.get(article.a["href"])

    print("get link {}".format(article.a["href"]))

    soup = BeautifulSoup(html_content.content, 'lxml')

    print("parse html")

    # pre process cleansing
    for i in range(len(soup.find_all('p', class_='para_caption'))):
      soup.find('p', class_='para_caption').decompose()

    processed_headline = (soup.find('h1', class_='detail__title')).text.strip().replace("\n", "")
    headline = {
      "id": processed_headline,
      "en": translator.translate(processed_headline)
    }

    print("generate headline")

    processed_content = (' '.join([p.text for p in soup.find_all('p')])).strip()
    en_processed_content = (' '.join([translator.translate(p.text) for p in soup.find_all('p')])).strip()
    content = {
      "id": processed_content,
      "en": en_processed_content
    }

    print("generate content")

    formatted_prompt = "{prompt}\ntitle : {title}\ncontent : {content}"
    response = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=[
        {
          "role": "system",
          "content": formatted_prompt.format(
            prompt=os.environ.get("PROMPT"),
            title=headline["id"],
            content=content["id"]
          )
        }
      ]
    )

    print("gpt process")

    data_obj = json.loads(response.choices[0].message.content)

    summary = {
      "id": data_obj["summary"],
      "en": translator.translate(data_obj["summary"])
    }

    category = translator.translate(data_obj["category"])

    date_string, timezone = (soup.find('div', class_='detail__date')).string.rsplit(' ', 1)
    date_string = translator.translate(date_string)
    date_format = "%d %b %Y %H:%M"
    date = datetime.strptime((date_string.split(", "))[1], date_format)

    article = {
      "headline": Headline(**headline),
      "author": (soup.find('div', class_='detail__author')).text,
      "date_published": date,
      "content": Content(**content),
      "location": data_obj["location"],
      "link_to_origin": article.a["href"],
      "category": category,
      "summary": Summary(**summary),
      "timezone": timezone
    }

    after_process_article = Article(**article)
    after_process_article.save()

    print("data saved")

    sleep(30)
  return detik_scraper(index - 1)

def main():
  connect(db=os.environ.get("DB_NAME"),host=os.environ.get("DB_URI"))
  detik_scraper(100)

if __name__ == "__main__":
  main()
