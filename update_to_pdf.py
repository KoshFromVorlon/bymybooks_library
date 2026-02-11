import os
import psycopg2
from dotenv import load_dotenv

# Загружаем настройки из .env
load_dotenv()


def migrate_to_pdf():
    """
    Добавляет колонку pdf_file в таблицу books.
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not found.")
        return

    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        print("Migrating: Adding 'pdf_file' column...")

        # Добавляем колонку, если её нет
        cursor.execute("ALTER TABLE books ADD COLUMN IF NOT EXISTS pdf_file VARCHAR;")

        # Для порядка можно (но не обязательно) переименовать epub_file -> pdf_file,
        # но проще просто добавить новую, чтобы не терять старые данные, если они важны.

        conn.commit()
        cursor.close()
        conn.close()
        print("Success: Database updated to support PDF.")

    except Exception as e:
        print(f"Migration failed: {e}")


if __name__ == "__main__":
    migrate_to_pdf()