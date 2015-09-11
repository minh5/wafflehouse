from scrapy.spider import BaseSpider

class waffleSpider(BaseSpider):
    name = "waffles"
    allowed_domains = ["menuism.com"]
    start_urls = [
        "http://www.menuism.com/restaurant-locations/waffle-house-78955/us/al/"
        "http://www.menuism.com/restaurant-locations/waffle-house-78955/us/az/"
    ]

    def parse(self, response):
        filename = response.url.split("/")[-2]
        open(filename, 'wb').write(response.body)
