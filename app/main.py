from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from . import models, database
import os

app = FastAPI()

# Подключаем папку со статикой (где будут лежать CSS, обложки и сами файлы книг)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/")
def read_root(request: Request, db: Session = Depends(database.get_db)):
    # Жесткая сортировка по ID (ровно как в файле seed_db.py)
    books = db.query(models.Book).join(models.Author).order_by(
        models.Book.id.asc()
    ).all()

    stack_size = 10
    stacks = [books[i:i + stack_size] for i in range(0, len(books), stack_size)]
    rows = [stacks[i:i + 3] for i in range(0, len(stacks), 3)]

    return templates.TemplateResponse("index.html", {"request": request, "rows": rows})


@app.get("/book/{book_id}")
def read_book(request: Request, book_id: int, db: Session = Depends(database.get_db)):
    # Ищем конкретную книгу в базе для читалки
    book = db.query(models.Book).filter(models.Book.id == book_id).first()

    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")

    return templates.TemplateResponse("reader.html", {"request": request, "book": book})


@app.get("/sync-files")
def sync_book_files(db: Session = Depends(database.get_db)):
    """
    Умный сканер: проходит по папке app/static/books,
    находит файлы вида 379.epub или 15.fb2 и привязывает их к книгам в БД по ID.
    """
    books_dir = "app/static/books"

    # Защита: если папки нет, создаем её автоматически
    os.makedirs(books_dir, exist_ok=True)

    updated_count = 0

    # Сканируем все файлы в папке
    for filename in os.listdir(books_dir):
        # Разбиваем имя файла на название и расширение (например, "379" и ".epub")
        name, ext = os.path.splitext(filename)

        # Если имя состоит только из цифр (это наш ID)
        if name.isdigit():
            book_id = int(name)
            # Ищем книгу в PostgreSQL
            book = db.query(models.Book).filter(models.Book.id == book_id).first()

            if book:
                file_path = f"/static/books/{filename}"
                # Распределяем пути по колонкам в зависимости от формата
                if ext.lower() == '.epub':
                    book.epub_file = file_path
                else:
                    book.original_file = file_path
                updated_count += 1

    db.commit()
    return {
        "status": "success",
        "updated_books": updated_count,
        "message": f"База PostgreSQL успешно синхронизирована! Обновлено книг: {updated_count}"
    }