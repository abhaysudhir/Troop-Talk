import os
import sys
import psutil
import asyncio
import json
from html2text import HTML2Text

__location__ = os.path.dirname(os.path.abspath(__file__))
__output__ = os.path.join(__location__, "output")
os.makedirs(__output__, exist_ok=True)

# Append parent directory to system path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from typing import List
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode


async def crawl_parallel(urls: List[str], max_concurrent: int = 3):
    print("\n=== Parallel Crawling with Browser Reuse + Memory Check ===")

    peak_memory = 0
    process = psutil.Process(os.getpid())
    html_converter = HTML2Text()
    html_converter.ignore_links = False

    def log_memory(prefix: str = ""):
        nonlocal peak_memory
        current_mem = process.memory_info().rss
        if current_mem > peak_memory:
            peak_memory = current_mem
        print(
            f"{prefix} Current Memory: {current_mem // (1024 * 1024)} MB, Peak: {peak_memory // (1024 * 1024)} MB"
        )

    browser_config = BrowserConfig(
        headless=True,
        verbose=False,
        extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
    )
    crawl_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()

    try:
        success_count = 0
        fail_count = 0
        for i in range(0, len(urls), max_concurrent):
            batch = urls[i : i + max_concurrent]
            tasks = []

            for j, url in enumerate(batch):
                session_id = f"parallel_session_{i + j}"
                task = crawler.arun(url=url, config=crawl_config, session_id=session_id)
                tasks.append(task)

            log_memory(prefix=f"Before batch {i//max_concurrent + 1}: ")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            log_memory(prefix=f"After batch {i//max_concurrent + 1}: ")

            for url, result in zip(batch, results):
                if isinstance(result, Exception):
                    print(f"Error crawling {url}: {result}")
                    fail_count += 1
                elif result.success:
                    try:
                        # Convert HTML to markdown
                        markdown_content = html_converter.handle(result.html)

                        # Create JSON data
                        data = {"url": url, "website_content_md": markdown_content}

                        # Create filename from URL
                        filename = url.split("/")[-1]
                        if not filename:
                            filename = url.split("/")[-2]
                        filename = f"{filename}.json"
                        filepath = os.path.join(__output__, filename)

                        # Save to JSON file
                        with open(filepath, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)

                        success_count += 1
                        print(f"Saved {url} to {filename}")
                    except Exception as e:
                        print(f"Error saving {url}: {e}")
                        fail_count += 1
                else:
                    fail_count += 1

        print(f"\nSummary:")
        print(f"  - Successfully crawled and saved: {success_count}")
        print(f"  - Failed: {fail_count}")
        print(f"  - Files saved in: {__output__}")

    finally:
        await crawler.close()
        log_memory(prefix="Final: ")
        print(f"\nPeak memory usage (MB): {peak_memory // (1024 * 1024)}")


async def main():
    from get_urls import get_bsa_urls

    urls = get_bsa_urls()
    if urls:
        print(f"Found {len(urls)} URLs to crawl")
        await crawl_parallel(urls, max_concurrent=10)
    else:
        print("No URLs found to crawl")


if __name__ == "__main__":
    asyncio.run(main())
