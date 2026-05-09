from firecrawl import FirecrawlApp

app = FirecrawlApp(api_key="")

# Crawl a website:
crawl_status = app.crawl_url(
  'https://scouting.org', 
  params={
    'limit': 50, 
    'scrapeOptions': {'formats': ['markdown']}
  },
  poll_interval=30
)
print(crawl_status)
