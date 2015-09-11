from scrapy.item import Item, Field

class waffItems(Item):
	addresss = Field()
	city = Field()
	zip = Field()


