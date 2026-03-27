from pymongo import MongoClient

class DatabaseManager:
    def __init__(self):
        self.initialized = False

    def init_database(self, URI, DB_NAME):
        try:
            self.client = MongoClient(URI)
            self.db = self.client[DB_NAME]
            self.initialized = True
        except Exception as e:
            self.initialized = False
    
    def get_collection(self, collection_name):
        if  self.initialized:
            return self.db[collection_name]
        return None
        