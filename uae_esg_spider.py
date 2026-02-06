import re
import urllib.parse
from collections import defaultdict

import scrapy
from scrapy.http import Request


class UaeEsgSpider(scrapy.Spider):
    name = "uae_esg_spider"

    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (compatible; UaeEsgSpider/1.0; +https://example.com)",
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_DELAY": 0.5,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 0.5,
        "AUTOTHROTTLE_MAX_DELAY": 8.0,
        "LOG_LEVEL": "INFO",
    }

    keywords = [
        "sustainability",
        "sustainable",
        "green",
        "eco",
        "environment",
        "climate",
        "net zero",
        "carbon",
        "emissions",
        "energy efficiency",
        "renewable energy",
        "resource efficiency",
        "circular economy",
        "closed loop",
        "full circle",
        "lifecycle",
        "end to end",
        "value chain",
        "product stewardship",
        "waste reduction",
        "reuse",
        "recycling",
        "zero waste",
        "epr",
        "extended producer responsibility",
        "producer responsibility",
        "take back",
        "packaging waste",
        "waste collection",
        "recycling targets",
        "compliance",
        "reporting",
        "eco labeling",
        "csr",
        "corporate responsibility",
        "social responsibility",
        "community",
        "social impact",
        "ethical",
        "responsible business",
        "volunteering",
        "local engagement",
        "esg",
        "environmental social governance",
        "governance",
        "transparency",
        "accountability",
        "risk management",
        "esg reporting",
        "sustainability reporting",
        "uae sustainability",
        "dubai sustainability",
        "abu dhabi sustainability",
        "net zero 2050",
        "uae green agenda",
        "vision 2030",
        "smart waste",
        "green economy",
        "green solutions",
    ]


    search_queries = [
        "UAE company ESG",
        "Dubai sustainability report company",
        "UAE corporate social responsibility company",
        "UAE net zero company",
        "Dubai climate action company",
        "UAE impact report company",
        "site:.ae sustainability report",
    ]

    max_search_pages = 3
    max_pages_per_domain = 25
    max_depth = 2
    uae_only = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.domain_counts = defaultdict(int)
        self.domain_seen = set()
        self.visited_urls = set()

        if "max_search_pages" in kwargs:
            self.max_search_pages = int(kwargs["max_search_pages"])
        if "max_pages_per_domain" in kwargs:
            self.max_pages_per_domain = int(kwargs["max_pages_per_domain"])
        if "max_depth" in kwargs:
            self.max_depth = int(kwargs["max_depth"])
        if "uae_only" in kwargs:
            self.uae_only = str(kwargs["uae_only"]).lower() in {"1", "true", "yes"}

    def start_requests(self):
        yield from self._build_start_requests()

    async def start(self):
        for request in self._build_start_requests():
            yield request

    def _build_start_requests(self):
        for query in self.search_queries:
            for page in range(self.max_search_pages):
                offset = page * 30
                search_url = self._duckduckgo_search_url(query, offset)
                yield Request(search_url, callback=self.parse_search, meta={"query": query}, dont_filter=True)

    def parse_search(self, response):
        selectors = [
            "a.result__a::attr(href)",
            "a[data-testid='result-title-a']::attr(href)",
            "article[data-testid='result'] a::attr(href)",
            "a[href*='uddg=']::attr(href)",
        ]

        links = []
        for selector in selectors:
            links.extend(response.css(selector).getall())

        unique_links = []
        seen = set()
        for link in links:
            if link in seen:
                continue
            seen.add(link)
            unique_links.append(link)

        for link in unique_links:
            raw_url = response.urljoin(link)
            url = self._extract_duckduckgo_target(raw_url)
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme not in {"http", "https"}:
                continue

            domain = self._normalize_domain(parsed.netloc)
            if not domain:
                continue
            if self.uae_only and not self._is_uae_domain(domain, url):
                continue
            if domain in self.domain_seen:
                continue

            self.domain_seen.add(domain)
            yield Request(
                url,
                callback=self.parse_company,
                meta={"domain": domain, "depth": 0, "query": response.meta.get("query")},
                dont_filter=True,
            )

    def parse_company(self, response):
        depth = response.meta.get("depth", 0)
        current_domain = self._normalize_domain(urllib.parse.urlparse(response.url).netloc)
        domain = response.meta.get("domain") or current_domain

        if not domain:
            return

        if self.domain_counts[domain] >= self.max_pages_per_domain:
            return

        clean_url = self._strip_fragment(response.url)
        if clean_url in self.visited_urls:
            return
        self.visited_urls.add(clean_url)

        self.domain_counts[domain] += 1

        page_text = " ".join(response.css("body *::text").getall())
        matched_keywords = self._match_keywords(page_text)

        if matched_keywords:
            yield {
                "url": response.url,
                "domain": domain,
                "company_name": self._extract_company_name(response),
                "title": response.css("title::text").get(default="").strip(),
                "query": response.meta.get("query"),
                "matched_keywords": matched_keywords,
            }

        if depth >= self.max_depth:
            return

        for href in response.css("a::attr(href)").getall():
            next_url = response.urljoin(href)
            parsed_next = urllib.parse.urlparse(next_url)
            if parsed_next.scheme not in {"http", "https"}:
                continue

            next_domain = self._normalize_domain(parsed_next.netloc)
            if next_domain != domain:
                continue

            if self.domain_counts[domain] >= self.max_pages_per_domain:
                break

            if self._strip_fragment(next_url) in self.visited_urls:
                continue

            yield Request(
                next_url,
                callback=self.parse_company,
                meta={"domain": domain, "depth": depth + 1, "query": response.meta.get("query")},
            )

    def _match_keywords(self, text):
        normalized = re.sub(r"\s+", " ", text.lower())
        return [keyword for keyword in self.keywords if keyword in normalized]

    @staticmethod
    def _duckduckgo_search_url(query, offset):
        encoded = urllib.parse.quote(query)
        return f"https://duckduckgo.com/html/?q={encoded}&s={offset}"

    @staticmethod
    def _extract_duckduckgo_target(url):
        parsed = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed.query)

        if "uddg" in query_params and query_params["uddg"]:
            return urllib.parse.unquote(query_params["uddg"][0])

        if "rut" in query_params and query_params["rut"]:
            return urllib.parse.unquote(query_params["rut"][0])

        return url

    @staticmethod
    def _normalize_domain(domain):
        domain = (domain or "").lower().strip()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain

    @staticmethod
    def _strip_fragment(url):
        parsed = urllib.parse.urlparse(url)
        return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, parsed.query, ""))

    @staticmethod
    def _extract_company_name(response):
        candidates = [
            response.css("meta[property='og:site_name']::attr(content)").get(),
            response.css("meta[name='application-name']::attr(content)").get(),
            response.css("title::text").get(),
        ]
        for value in candidates:
            if value and value.strip():
                return value.strip()
        return ""

    @staticmethod
    def _is_uae_domain(domain, url):
        if domain.endswith(".ae"):
            return True

        lowered = url.lower()
        uae_tokens = [
            "/uae",
            "-uae",
            ".ae/",
            ".ae?",
            "dubai",
            "abu-dhabi",
            "abudhabi",
            "sharjah",
        ]
        return any(token in lowered for token in uae_tokens)
