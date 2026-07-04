import chromadb

DB_PATH = "./chroma_db"
COLLECTION_NAME = "course_notice"


def get_chroma_collection():
    client = chromadb.PersistentClient(path=DB_PATH)
    return client.get_or_create_collection(name=COLLECTION_NAME)
