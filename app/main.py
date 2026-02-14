import os
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from . import models, database

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/")
def read_root(request: Request, db: Session = Depends(database.get_db)):
    # Получаем все книги, отсортированные по позиции
    books = db.query(models.Book).join(models.Author).order_by(models.Book.position.asc()).all()

    # === ЛОГИКА УМНОЙ ГРУППИРОВКИ ===
    stacks = []
    current_stack = []
    current_height = 0

    # Настройки "вместимости" одной стопки
    MAX_BOOKS_PER_STACK = 9  # Максимум книг в стопке (как вы просили)
    MAX_PIXEL_HEIGHT = 750  # Максимальная высота стопки в пикселях (чтобы не улетала в небеса)

    for book in books:
        # 1. Рассчитываем визуальную толщину книги (формула 1-в-1 как в index.html)
        # Если страниц 0 (заглушка), считаем как 300 стр.
        pages = book.pages if book.pages > 0 else 300
        thickness = 50 + (pages * 0.12)

        # Ограничение толщины одной книги (как в CSS)
        if thickness > 150:
            thickness = 150

        # 2. Проверяем, влезает ли книга в текущую стопку
        # Если книг уже 9 ИЛИ добавление этой книги превысит лимит высоты -> новая стопка
        if len(current_stack) >= MAX_BOOKS_PER_STACK or (current_height + thickness) > MAX_PIXEL_HEIGHT:
            stacks.append(current_stack)
            current_stack = []
            current_height = 0

        # 3. Добавляем книгу в текущую
        current_stack.append(book)
        current_height += thickness

    # Не забываем добавить последнюю стопку, если она не пустая
    if current_stack:
        stacks.append(current_stack)

    # Разбиваем стопки по полкам (по 3 стопки на одну полку шкафа)
    rows = [stacks[i:i + 3] for i in range(0, len(stacks), 3)]

    return templates.TemplateResponse("index.html", {"request": request, "rows": rows})


@app.get("/book/{book_id}")
def read_book(book_id: int, db: Session = Depends(database.get_db)):
    # Прямой редирект на PDF файл (браузер откроет сам)
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book or not book.pdf_file:
        raise HTTPException(status_code=404, detail="PDF не найден. Запустите sync_library.py")
    return RedirectResponse(url=book.pdf_file)