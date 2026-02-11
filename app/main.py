from fastapi import FastAPI, Request, Depends, HTTPException, Body
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from . import models, database
import os

app = FastAPI()

# Подключаем папку static, откуда будут отдаваться обложки и PDF
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/")
def read_root(request: Request, db: Session = Depends(database.get_db)):
    """
    Главная страница: Выводит полки с книгами.
    Сортировка: Хронологическая (по полю position), чтобы соблюсти порядок.
    """
    # Используем position для правильной хронологии
    # Если поле position еще не заполнено, можно временно заменить на models.Book.sort_year
    books = db.query(models.Book).join(models.Author).order_by(
        models.Book.position.asc()
    ).all()

    # Разбиваем книги на "стопки" по 10 и "полки" по 3 стопки
    stack_size = 10
    stacks = [books[i:i + stack_size] for i in range(0, len(books), stack_size)]
    rows = [stacks[i:i + 3] for i in range(0, len(stacks), 3)]

    return templates.TemplateResponse("index.html", {"request": request, "rows": rows})


@app.get("/book/{book_id}")
def read_book(book_id: int, db: Session = Depends(database.get_db)):
    """
    Чтение книги: ВМЕСТО глючного ридера мы просто перенаправляем браузер
    на прямой файл PDF. Chrome/Firefox/Edge откроют его своим нативным,
    быстрым и красивым просмотрщиком.
    """
    book = db.query(models.Book).filter(models.Book.id == book_id).first()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Проверяем, есть ли ссылка на PDF
    if not book.pdf_file:
        raise HTTPException(status_code=404, detail="PDF file not assigned for this book")

    # Редирект на статический файл (например: /static/books/001_sobor.pdf)
    return RedirectResponse(url=book.pdf_file)


@app.get("/sync-files")
def sync_book_files(db: Session = Depends(database.get_db)):
    """
    Сканер файлов: Ищет .pdf файлы в папке books и привязывает их к базе.
    Поддерживает формат имени: '001_slug.pdf' (по позиции).
    """
    books_dir = "app/static/books"
    os.makedirs(books_dir, exist_ok=True)

    updated_count = 0

    # Сканируем папку
    for filename in os.listdir(books_dir):
        name_part, ext = os.path.splitext(filename)

        # Работаем только с PDF
        if ext.lower() == '.pdf':
            # Пытаемся понять, к какой книге относится файл
            # Вариант 1: Имя файла начинается с позиции (например, 005_sobor.pdf)
            if "_" in name_part:
                possible_pos = name_part.split("_")[0]
                if possible_pos.isdigit():
                    pos = int(possible_pos)
                    book = db.query(models.Book).filter(models.Book.position == pos).first()

                    if book:
                        book.pdf_file = f"/static/books/{filename}"
                        updated_count += 1

            # Вариант 2 (запасной): Имя файла это просто ID (например, 379.pdf)
            elif name_part.isdigit():
                book_id = int(name_part)
                book = db.query(models.Book).filter(models.Book.id == book_id).first()

                if book:
                    book.pdf_file = f"/static/books/{filename}"
                    updated_count += 1

    db.commit()
    return {
        "status": "success",
        "updated_books": updated_count,
        "message": f"Синхронизация завершена! Привязано PDF-книг: {updated_count}"
    }

# Роут для закладок удален, так как браузерный PDF хранит прогресс локально сам.