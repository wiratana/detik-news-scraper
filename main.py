import json
import random
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

  html_content = requests.get('https://www.detik.com/tag/bencana-alam/?page={index}'.format(index=index))
  soup = BeautifulSoup(html_content.content, 'lxml')
  article_list = soup.find_all('article')
  
  for article in article_list:
    identical_article_amount = Article.objects(link_to_origin=article.a["href"]).count()
    if identical_article_amount > 0:
      break

    html_content = requests.get(article.a["href"])

    print("get link {}".format(article.a["href"]))

    soup = BeautifulSoup(html_content.content, 'lxml')

    print("parse html")
    
    if soup.find("h3", class_="detail__subtitle"):
      break

    # pre process cleansing
    for i in range(len(soup.find_all('p', class_='para_caption'))):
      soup.find('p', class_='para_caption').decompose()

    headline = {
      "id": (soup.find('h1', class_='detail__title')).text.strip().replace("\n", ""),
      "en": ''
    }

    content = {
      "id": (' '.join([p.text for p in soup.find_all('p')])).strip(),
      "en": ''
    }

    date_string, timezone = (soup.find('div', class_='detail__date')).string.rsplit(' ', 1)

    formatted_prompt = "{prompt}\ntitle : {title}\ncontent : {content}"
    gpt_executed = False

    while not gpt_executed:
      try:
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

        data_obj = json.loads(response.choices[0].message.content)
        gpt_executed = True
        print("gpt processed")
      except Exception as e:
        print(f"failed : {e}")
        sleep(1)

    summary = {
      "id": data_obj["summary"],
      "en": ''
    }

    category = data_obj["category"]


    translation_executed = False

    while not translation_executed:
      try:
        headline["en"] = translator.translate(headline["id"])
        content["en"]  = (' '.join([translator.translate(p.text) if p is not None else "" for p in soup.find_all('p')])).strip()
        summary["en"]  = translator.translate(data_obj["summary"])
        date_string = translator.translate(date_string)
        translation_executed = True
        print("translation processed")
      except Exception as e:
        print(f"failed : {e}")
        sleep(1)

    date_formats = ["%d %b %Y %H:%M", "%b %d %Y %H:%M", "%b %d, %Y %H:%M"]
    date_string = (date_string.split(" "))
    del date_string[0]
    date_string = " ".join(date_string)
    date_formating = False
    format_index = len(date_formats) - 1

    while not date_formating:
      try:
        date = datetime.strptime(date_string, date_formats[format_index])
        date_formating = True
      except Exception as e:
        print(f"failed : {e}")
        format_index = format_index - 1 if format_index > 0 else format_index
        print(date_string)

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
  return detik_scraper(index - 1)

def main():
  connect(db=os.environ.get("DB_NAME"),host=os.environ.get("DB_URI"))
  while True:
    detik_scraper(25)

if __name__ == "__main__":
  main()
