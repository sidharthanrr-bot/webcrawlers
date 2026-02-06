import re
import urllib.parse
from collections import defaultdict

import scrapy
from scrapy.http import Request


class UaeEsgSpider(scrapy.Spider):
    name = "uae_esg_spider"

    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (compatible; UaeEsgSpider/1.0; +https://example.com)",
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 1.0,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 1.0,
        "AUTOTHROTTLE_MAX_DELAY": 10.0,
        "LOG_LEVEL": "INFO",
    }

    keywords = [
        "sustainability",
        "esg",
        "corporate social responsibility",
        "environmental responsibility",
        "climate action",
        "net zero",
        "ethical business",
        "responsible sourcing",
        "impact report",
    ]

    search_queries = [
        "UAE company sustainability",
        "Dubai ESG report",
        "UAE corporate social responsibility",
        "Dubai net zero strategy company",
        "UAE ethical business report",
        "UAE responsible sourcing",
        "Dubai impact report",
    ]

    max_search_pages = 3
    max_pages_per_domain = 25
    max_depth = 2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.domain_counts = defaultdict(int)
        self.domain_seen = set()

        if "max_search_pages" in kwargs:
            self.max_search_pages = int(kwargs["max_search_pages"])
        if "max_pages_per_domain" in kwargs:
            self.max_pages_per_domain = int(kwargs["max_pages_per_domain"])
        if "max_depth" in kwargs:
            self.max_depth = int(kwargs["max_depth"])

    def start_requests(self):
        for query in self.search_queries:
            for page in range(self.max_search_pages):
                offset = page * 30
                search_url = self._duckduckgo_search_url(query, offset)
                yield Request(search_url, callback=self.parse_search, meta={"query": query})

    def parse_search(self, response):
        result_links = response.css("a.result__a::attr(href)").getall()
        for link in result_links:
            url = response.urljoin(link)
            domain = urllib.parse.urlparse(url).netloc
            if not domain:
                continue
            if not self._is_uae_domain(domain, url):
                continue
            if domain in self.domain_seen:
                continue
            self.domain_seen.add(domain)
            yield Request(url, callback=self.parse_company, meta={"domain": domain, "depth": 0})

    def parse_company(self, response):
        domain = response.meta.get("domain")
        depth = response.meta.get("depth", 0)

        if not domain:
            domain = urllib.parse.urlparse(response.url).netloc

        if self.domain_counts[domain] >= self.max_pages_per_domain:
            return

        self.domain_counts[domain] += 1

        page_text = " ".join(response.css("body *::text").getall())
        matched_keywords = self._match_keywords(page_text)

        if matched_keywords:
            yield {
                "url": response.url,
                "domain": domain,
                "title": response.css("title::text").get(default="").strip(),
                "matched_keywords": matched_keywords,
            }

        if depth >= self.max_depth:
            return

        for href in response.css("a::attr(href)").getall():
            next_url = response.urljoin(href)
            next_domain = urllib.parse.urlparse(next_url).netloc
            if next_domain != domain:
                continue
            if self.domain_counts[domain] >= self.max_pages_per_domain:
                break
            yield Request(
                next_url,
                callback=self.parse_company,
                meta={"domain": domain, "depth": depth + 1},
            )

    def _match_keywords(self, text):
        normalized = re.sub(r"\s+", " ", text.lower())
        matched = []
        for keyword in self.keywords:
            if keyword in normalized:
                matched.append(keyword)
        return matched

    @staticmethod
    def _duckduckgo_search_url(query, offset):
        encoded = urllib.parse.quote(query)
        return f"https://duckduckgo.com/html/?q={encoded}&s={offset}"

    @staticmethod
    def _is_uae_domain(domain, url):
        if domain.endswith(".ae"):
            return True
        if ".ae/" in url or ".ae?" in url:
            return True
        return False
