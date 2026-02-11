import os
import sys

# Добавляем текущую директорию в путь, чтобы видеть app
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app import models


def create_placeholders():
    session = SessionLocal()

    # Папка для книг
    books_dir = os.path.join("app", "static", "books")
    os.makedirs(books_dir, exist_ok=True)

    # Берем все книги из базы
    books = session.query(models.Book).order_by(models.Book.position).all()
    print(f"Найдено книг в базе: {len(books)}")

    updated_count = 0
    created_count = 0

    for book in books:
        # 1. Генерируем правильное имя файла: 001_slug.pdf
        # Если slug пустой, ставим заглушку 'unknown', чтобы не сломать имя
        slug = book.slug if book.slug else "unknown"
        filename = f"{str(book.position).zfill(3)}_{slug}.pdf"

        file_path = os.path.join(books_dir, filename)
        web_path = f"/static/books/{filename}"

        # 2. Создаем физический файл-пустышку, если его нет
        if not os.path.exists(file_path):
            with open(file_path, 'wb') as f:
                # Пишем пару байт, чтобы файл не был абсолютно пустым (иногда винда ругается)
                f.write(b"%PDF-1.4 empty placeholder")
            print(f"[+] Создан файл: {filename}")
            created_count += 1
        else:
            # print(f"[skip] Файл уже есть: {filename}")
            pass

        # 3. Обновляем ссылку в базе данных, чтобы клик работал
        if book.pdf_file != web_path:
            book.pdf_file = web_path
            updated_count += 1

    session.commit()
    session.close()

    print("-" * 30)
    print(f"Итог:")
    print(f"Создано новых файлов-заглушек: {created_count}")
    print(f"Обновлено ссылок в базе данных: {updated_count}")


if __name__ == "__main__":
    create_placeholders()