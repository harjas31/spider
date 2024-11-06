import scrapy
import random
import logging

class AmazonSpider(scrapy.Spider):
    name = "amazon_spider"
    allowed_domains = ["amazon.in"]
    custom_settings = {
        'DOWNLOAD_DELAY': random.uniform(2, 5),
        'USER_AGENT': random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        ]),
        'RETRY_TIMES': 3,
        'COOKIES_ENABLED': False,
        'ROBOTSTXT_OBEY': False,
    }

    def __init__(self, keywords=None, num_products=30, *args, **kwargs):
        super(AmazonSpider, self).__init__(*args, **kwargs)
        self.keywords = keywords or "laptop"
        self.num_products = int(num_products)
        self.start_urls = [f"https://www.amazon.in/s?k={self.keywords.replace(' ', '+')}"]
        self.products = []

    def parse(self, response):
        products = response.css("div[data-component-type='s-search-result']")
        for product in products:
            if len(self.products) >= self.num_products:
                break

            try:
                asin = product.attrib.get("data-asin", "N/A")
                title = product.css("h2 .a-text-normal::text").get(default="Title not found")
                price = product.css(".a-price-whole::text").get(default="N/A")
                rating = product.css(".a-icon-alt::text").get(default="N/A").split(" ")[0]
                reviews = product.css(".s-underline-text::text").re_first(r'\d+', default="N/A")
                link = f"https://www.amazon.in/dp/{asin}"

                bought_count = "N/A"
                bought_element = product.css(".social-proofing-faceout-title-text, .a-color-secondary::text")
                if bought_element:
                    bought_text = bought_element.get().strip()
                    if "bought in past month" in bought_text.lower():
                        bought_count = bought_text.split()[0]

                sponsored_class = product.attrib.get("class", [])
                product_type = "Sponsored" if "AdHolder" in sponsored_class else "Organic"

                self.products.append({
                    "rank": len(self.products) + 1,
                    "asin": asin,
                    "title": title,
                    "price": price,
                    "link": link,
                    "rating": rating,
                    "reviews": reviews,
                    "bought_last_month": bought_count,
                    "type": product_type,
                })

            except Exception as e:
                logging.error(f"Error processing product: {e}")

        # Follow pagination if required
        next_page = response.css("a.s-pagination-next::attr(href)").get()
        if next_page and len(self.products) < self.num_products:
            yield response.follow(next_page, callback=self.parse)
        else:
            yield {"products": self.products}
