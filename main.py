from content_manager.content_database import ContentDatabase
from content_manager.content_manager import ContentManager

if __name__ == "__main__":
    SERVER = "45.149.76.141"
    DATABASE = "ContentGenerator"
    USERNAME = "admin"
    PASSWORD = "HTTTHFocBbW5CM"
    SESSION_HASH = "amir"
    
    content_db = ContentDatabase(SERVER, DATABASE, USERNAME, PASSWORD)
    content_manager = ContentManager(SESSION_HASH, content_db)

    content_manager.process_incomplete_contents()

