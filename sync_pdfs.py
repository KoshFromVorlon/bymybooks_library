import os
import sys

sys.path.append(os.getcwd())

from app.database import SessionLocal
from app import models


def sync_pdfs():
    session = SessionLocal()
    books_dir = os.path.join("app", "static", "books")

    # Получаем все книги
    books = session.query(models.Book).all()
    print(f"Проверка {len(books)} книг на наличие PDF...")

    updated_count = 0

    for book in books:
        # Формируем ожидаемое имя файла: 001_slug.pdf
        expected_filename = f"{str(book.position).zfill(3)}_{book.slug}.pdf"
        file_path = os.path.join(books_dir, expected_filename)

        # Проверяем, лежит ли такой файл в папке
        if os.path.exists(file_path):
            # Путь для веба (как он будет виден браузеру)
            web_path = f"/static/books/{expected_filename}"

            # Если в базе путь другой или пустой — обновляем
            if book.pdf_file != web_path:
                book.pdf_file = web_path
                updated_count += 1
                print(f"[+] Привязан PDF: {expected_filename}")
        else:
            # Можно раскомментировать, если хочешь видеть, чего не хватает
            # print(f"[-] Не найден файл: {expected_filename}")
            pass

    session.commit()
    print(f"\nГотово! Обновлено записей: {updated_count}")
    session.close()


if __name__ == "__main__":
    sync_pdfs()