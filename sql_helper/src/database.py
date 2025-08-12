import pymysql
import sqlparse
import time

class MySQLConnector:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    def connect(self):
        try:
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            return True
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return False

    def execute_query(self, query):
        """Выполнение SQL-запроса"""
        if not self.connection:
            return "Нет подключения к базе данных"
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                # Для запросов, которые возвращают данные
                if (query.strip().upper().startswith("SELECT") or
                    query.strip().upper().startswith("DESCRIBE") or
                    query.strip().upper().startswith("SHOW")):
                    result = cursor.fetchall()
                    return result
                else:
                    # Для запросов, которые изменяют данные
                    self.connection.commit()
                    affected_rows = cursor.rowcount
                    return f"Запрос выполнен успешно. Затронуто строк: {affected_rows}"
        except Exception as e:
            return f"Ошибка выполнения запроса: {e}"

    def get_tables(self):
        """Получить список таблиц в базе данных"""
        if not self.connection:
            return []
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                table_names = [list(row.values())[0] for row in tables]
                return table_names
        except Exception as e:
            print(f"Ошибка получения списка таблиц: {e}")
            return []

    def validate_query(self, query):
        """Базовая валидация SQL запроса"""
        try:
            parsed = sqlparse.parse(query)
            if not parsed:
                return False, "Неверный формат SQL запроса"
            return True, "Запрос корректен"
        except Exception as e:
            return False, f"Ошибка валидации: {str(e)}"

    def close(self):
        if self.connection:
            self.connection.close()
