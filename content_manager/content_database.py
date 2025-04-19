from content_manager.sql_server_database import SQLServerDatabase

class ContentDatabase:
    def __init__(self, server, database, username, password):
        self.db = SQLServerDatabase(server, database, username, password)

    def connect(self):
        self.db.connect()

    def disconnect(self):
        self.db.disconnect()

    def get_purecontent_without_description(self):
        query = """
            SELECT Id, Title 
            FROM dbo.TblPureContent 
            WHERE (Description IS NULL OR ContentCategoryId IS NULL)
            AND Title IS NOT NULL
        """
        return self.db.select(query)

    def get_purecontent_with_null_title(self):
        query = """
            SELECT Id, Description 
            FROM dbo.TblPureContent 
            WHERE Title IS NULL
            AND Description IS NOT NULL
        """
        return self.db.select(query)

    def get_purecontent_with_empty_title(self):
        query = """
            SELECT Id, Description 
            FROM dbo.TblPureContent 
            WHERE (Title = '' OR Title = 'None' OR Title = 'Untitled Content')
            AND Description IS NOT NULL
        """
        return self.db.select(query)

    def get_category(self):
        query = "SELECT Id, Title FROM dbo.TblContentCategory"
        return self.db.select(query)

    def update_pure_content(self, content_id, title=None, description=None, content_category_id=None):
        update_query = '''
            UPDATE dbo.TblPureContent
            SET 
                Title = COALESCE(?, Title), 
                Description = COALESCE(?, Description), 
                ContentCategoryId = COALESCE(?, ContentCategoryId), 
                CompleteDatetime = GETDATE()
            WHERE Id = ?
        '''
        self.db.update(update_query, (title, description, content_category_id, content_id))
        return True

    def get_all_purecontents(self):
        """دریافت تمامی محتواها (با عنوان، توضیحات و دسته‌بندی)"""
        query = """
            SELECT Id, Title, Description, ContentCategoryId
            FROM dbo.TblPureContent
        """
        return self.db.select(query)
