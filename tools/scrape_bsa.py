from firecrawl import FirecrawlApp

app = FirecrawlApp(api_key="fc-b72b5fcd92fb4017bad18bdfaa10b922")

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