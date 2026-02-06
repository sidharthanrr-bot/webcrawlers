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

3. Run the spider:

```bash
scrapy runspider uae_esg_spider.py -o results.json
```

### Optional arguments

You can tune limits to avoid large crawls:

```bash
scrapy runspider uae_esg_spider.py \
  -a max_search_pages=2 \
  -a max_pages_per_domain=15 \
  -a max_depth=2 \
  -o results.json
```

## Notes

- The spider respects `robots.txt` by default.
- Search results depend on DuckDuckGo availability and may vary.
- For large-scale crawling, consider using a dedicated search API and stricter filtering.
