import scrapy
from itemloaders import processors


class LeroyScraperItem(scrapy.Item):
    _id = scrapy.Field()
    link = scrapy.Field()
    images = scrapy.Field(
        output_processor=processors.Identity()
    )
    title = scrapy.Field()
    price = scrapy.Field(
        input_processor=processors.Compose(lambda value: [v.replace(' ', '') for v in value])
    )
    features = scrapy.Field(
        output_processor=processors.Identity()
    )
