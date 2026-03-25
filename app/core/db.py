from pymongo import MongoClient

class DatabaseManager:
    def __init__(self):
        self.initialized = False

    def init_database(self, URI, DB_NAME):
        try:
            self.client = MongoClient(URI, serverSelectionTimeoutMS=3000)
            self.client.server_info() 
            self.db = self.client[DB_NAME]
            self.initialized = True
            print("Mongo bağlandı")
        except Exception as e:
            print("Mongo bağlantı hatası:", e)
            self.initialized = False
    
    def get_collection(self, collection_name):
        if  self.initialized:
            return self.db[collection_name]
        return None
        