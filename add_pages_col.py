import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def add_column():
    try:
        # Получаем URL из .env или используем дефолтный локальный
        db_url = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/dbname")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        cursor.execute("ALTER TABLE books ADD COLUMN IF NOT EXISTS pages INTEGER DEFAULT 0;")

        conn.commit()
        conn.close()
        print("Колонка 'pages' успешно добавлена!")
    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    add_column()