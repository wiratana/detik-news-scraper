
# Detik News Scraper



Website Scraper that use power of OpenAI chat completion, deep translation, and advance error handling. gether article, reshape the structure, data processing, and save it to mongoDB.
## Run Locally

Clone the project

```bash
  git clone https://github.com/wiratana/detik-news-scraper
```

Go to the project directory

```bash
  cd detik-news-scraper
```

Initialize Environment Variable

```bash
  cp example.env .env
  nano .env
```

Build the Container with Docker

```bash
  docker build -t detik-news-scraper .
```

Start the Container with Docker

```bash
  docker run -i detik-news-scraper
```


## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

`OPEN_API_KEY`

`DB_URI`

`DB_NAME`

`PROMPT`


## Authors

- [@wiratana](https://github.com/wiratana)