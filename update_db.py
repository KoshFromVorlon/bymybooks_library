from app.database import engine
from sqlalchemy import text

def add_columns_to_render():
    print("Подключаемся к базе на Рендере...")
    with engine.begin() as conn:
        try:
            # Отправляем команду добавить колонки прямо в таблицу
            conn.execute(text("ALTER TABLE books ADD COLUMN original_file VARCHAR;"))
            conn.execute(text("ALTER TABLE books ADD COLUMN epub_file VARCHAR;"))
            print("Успех! Колонки original_file и epub_file добавлены в базу.")
        except Exception as e:
            print(f"Что-то пошло не так (возможно, колонки уже есть): {e}")

if __name__ == "__main__":
    add_columns_to_render()