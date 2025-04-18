from content_manager.content_database import ContentDatabase
from content_manager.content_manager import ContentManager

if __name__ == "__main__":
    SERVER = "45.149.76.141"
    DATABASE = "ContentGenerator"
    USERNAME = "admin"
    PASSWORD = "HTTTHFocBbW5CM"
    SESSION_HASH = "amir"

    # اتصال به دیتابیس
    content_db = ContentDatabase(SERVER, DATABASE, USERNAME, PASSWORD)
    
    # اتصال به دیتابیس
    content_db.connect()
    
    # مدیریت محتوا
    content_manager = ContentManager(SESSION_HASH, content_db)
    content_manager.process_contents()  # پردازش محتوای اولیه

    # قطع اتصال از دیتابیس بعد از پردازش
    content_db.disconnect()
