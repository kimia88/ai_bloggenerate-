import pyodbc

class SQLServerDatabase:
    def __init__(self, server, database, username, password):
        self.connection_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};DATABASE={database};UID={username};PWD={password}"
        )
        self.connection = None

    def connect(self):
        """اتصال به پایگاه داده"""
        try:
            self.connection = pyodbc.connect(self.connection_string)
            print("Database connection established.")
        except Exception as e:
            print(f"Failed to connect to database: {e}")
            raise

    def disconnect(self):
        """قطع اتصال از پایگاه داده"""
        if self.connection and not self.connection.closed:
            self.connection.close()
            print("Database connection closed.")
        else:
            print("❗ Connection is already closed.")

    def _execute_query(self, query, params=None, fetch=False):
        """اجرای کوئری SQL عمومی"""
        if not self.connection or self.connection.closed:
            print("❗ Cannot execute query, connection is closed.")
            return None
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or [])
            if fetch:
                rows = cursor.fetchall()
                return rows
            else:
                self.connection.commit()
        except Exception as e:
            print(f"Failed to execute query: {e}")
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def select(self, query):
        """اجرای کوئری SELECT و بازگشت نتایج"""
        return self._execute_query(query, fetch=True)

    def insert_and_get_id(self, insert_query):
        """اجرای کوئری INSERT و بازگشت شناسه رکورد وارد شده"""
        self._execute_query(insert_query, fetch=False)
        query = "SELECT SCOPE_IDENTITY();"
        result = self.select(query)
        return result[0][0] if result else None

    def update(self, query, params=None):
        """اجرای کوئری UPDATE"""
        self._execute_query(query, params)

    def check_connection(self):
        """بررسی وضعیت اتصال"""
        if self.connection and not self.connection.closed:
            print("✅ Connection is open.")
            return True
        else:
            print("❗ Connection is closed or not established.")
            return False

    def get_category(self):
        """دریافت دسته‌بندی‌ها از پایگاه داده"""
        query = "SELECT id, title FROM categories"
        return self.select(query)

    def get_purecontent_with_null_title(self):
        """دریافت محتوای با عنوان NULL از پایگاه داده"""
        query = "SELECT id, description FROM pure_content WHERE title IS NULL"
        return self.select(query)

    def get_purecontent_with_empty_title(self):
        """دریافت محتوای با عنوان خالی از پایگاه داده"""
        query = "SELECT id, description FROM pure_content WHERE title = ''"
        return self.select(query)

    def get_purecontent_without_description(self):
        """دریافت محتوای بدون توضیحات از پایگاه داده"""
        query = "SELECT id, title FROM pure_content WHERE description IS NULL OR description = ''"
        return self.select(query)

    def update_pure_content(self, content_id, title=None, description=None, content_category_id=None):
        """بروزرسانی محتوای خالی یا نادرست"""
        set_clauses = []
        params = []

        if title:
            set_clauses.append("title = ?")
            params.append(title)
        if description:
            set_clauses.append("description = ?")
            params.append(description)
        if content_category_id:
            set_clauses.append("content_category_id = ?")
            params.append(content_category_id)

        if set_clauses:
            set_clause = ", ".join(set_clauses)
            query = f"UPDATE pure_content SET {set_clause} WHERE id = ?"
            params.append(content_id)
            self.update(query, tuple(params))
