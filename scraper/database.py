import psycopg2

from scraper.config import Config


class DatabaseManager:
    def __init__(self):
        self.connection = None

    def connect(self):
        try:
            self.connection = psycopg2.connect(Config.DB_URI)
            self._init_schema()
            print("Database connected.")
            return self.connection
        except Exception as e:
            print(f"Database error: {e}")
            exit(1)

    def _init_schema(self):
        cursor = self.connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS INPOSTS (
                id SERIAL PRIMARY KEY,
                author VARCHAR(255),
                content TEXT,
                likes_count VARCHAR(50),
                shares_count VARCHAR(50),
                comments_count VARCHAR(50),
                post_date DATE,
                keywords VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            ALTER TABLE INPOSTS
            ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'PENDING'
        """)
        self.connection.commit()
        cursor.close()

    def exists(self, author, content):
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT id FROM INPOSTS WHERE author = %s AND content = %s",
            (author, content),
        )
        result = cursor.fetchone()
        cursor.close()
        return result is not None

    def insert_post(self, author, content, likes, shares, comments, post_date, keyword):
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO INPOSTS
                (author, content, likes_count, shares_count, comments_count, post_date, keywords)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (author, content, likes, shares, comments, post_date, keyword),
        )
        self.connection.commit()
        cursor.close()

    def close(self):
        if self.connection:
            self.connection.close()
