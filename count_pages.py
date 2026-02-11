import os
import sys
from pypdf import PdfReader

sys.path.append(os.getcwd())
from app.database import SessionLocal
from app import models


def scan_pages():
    session = SessionLocal()
    books = session.query(models.Book).filter(models.Book.pdf_file.isnot(None)).all()

    print(f"Найдено книг с PDF: {len(books)}")
    updated = 0

    for book in books:
        # Превращаем веб-путь в реальный путь на диске
        # /static/books/... -> app/static/books/...
        relative_path = book.pdf_file.lstrip("/")
        real_path = os.path.join(os.getcwd(), "app", relative_path.replace("/", os.sep))

        if os.path.exists(real_path):
            try:
                reader = PdfReader(real_path)
                count = len(reader.pages)

                if book.pages != count:
                    book.pages = count
                    updated += 1
                    print(f"[OK] {book.title}: {count} стр.")
            except Exception as e:
                print(f"[ERR] Ошибка чтения {book.title}: {e}")
        else:
            print(f"[404] Файл не найден: {real_path}")

    session.commit()
    print(f"Обновлено книг: {updated}")
    session.close()


if __name__ == "__main__":
    scan_pages()