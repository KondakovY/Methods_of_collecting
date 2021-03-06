from pymongo import MongoClient

MONGO_HOST = 'mongodb://localhost:27017/'
DB_NAME = 'Lesson_6'


class JobScraperPipeline:
    def __init__(self):
        client = MongoClient(MONGO_HOST)
        self.db = client[DB_NAME]

    def process_item(self, item, spider):
        collection = self.db[spider.name]
        if collection.count_documents(item) == 0:
            collection.insert_one(item)
        return item
