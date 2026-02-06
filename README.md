# UAE ESG Web Crawler (Scrapy)

This repository contains a Scrapy spider that discovers UAE business websites (with a Dubai focus) and extracts pages mentioning:

- sustainability
- ESG
- Corporate Social Responsibility
- Environmental Responsibility
- Climate Action
- Net Zero
- Ethical Business
- Responsible Sourcing
- Impact Report

The spider uses DuckDuckGo HTML search pages to seed company domains and then crawls within each domain to find matching content.

## Run in Google Colab ("Google Notepad")

1. Install Scrapy:

```bash
pip install scrapy
```

2. Upload this repository (or just the `uae_esg_spider.py` file) to your Colab workspace.

3. Run the spider (note the `!` prefix for Colab shell cells):

```bash
!scrapy runspider uae_esg_spider.py -o results.json
```

### Optional arguments

You can tune limits to avoid large crawls:

```bash
!scrapy runspider uae_esg_spider.py \
  -a max_search_pages=2 \
  -a max_pages_per_domain=15 \
  -a max_depth=2 \
  -o results.json
```

If you want to run from a Python cell, patch the event loop first:

```python
import nest_asyncio
nest_asyncio.apply()

from scrapy.crawler import CrawlerProcess
from uae_esg_spider import UaeEsgSpider

process = CrawlerProcess()
process.crawl(UaeEsgSpider)
process.start()
```

## Notes

- The spider disables `robots.txt` filtering by default to reduce empty-result runs in notebook demos (enable it with `-s ROBOTSTXT_OBEY=True` if you need strict compliance).
- If your crawl returns 0 items with many `robotstxt/forbidden` logs (often from DuckDuckGo redirects), try a smaller run and (only if permitted) override with `-s ROBOTSTXT_OBEY=False`.
- Output rows now include `company_name`, `domain`, `url`, `title`, `query`, and `matched_keywords`.
- Search results depend on DuckDuckGo availability and may vary.
- For large-scale crawling, consider using a dedicated search API and stricter filtering.
