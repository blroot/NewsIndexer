from NewsReader import NewsReader

if __name__ == "__main__":
    c = NewsReader("config.ini")
    c.collect_news()
