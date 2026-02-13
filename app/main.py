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
    # Сортировка по позиции (хронологии)
    books = db.query(models.Book).join(models.Author).order_by(models.Book.position.asc()).all()

    stack_size = 10
    stacks = [books[i:i + stack_size] for i in range(0, len(books), stack_size)]
    rows = [stacks[i:i + 3] for i in range(0, len(stacks), 3)]

    return templates.TemplateResponse("index.html", {"request": request, "rows": rows})

@app.get("/book/{book_id}")
def read_book(book_id: int, db: Session = Depends(database.get_db)):
    # Прямой редирект на PDF файл (браузер откроет сам)
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book or not book.pdf_file:
        raise HTTPException(status_code=404, detail="PDF не найден. Запустите sync_library.py")
    return RedirectResponse(url=book.pdf_file)