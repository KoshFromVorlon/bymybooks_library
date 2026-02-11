from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from . import models, database

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/")
def read_root(request: Request, db: Session = Depends(database.get_db)):
    # Сортировка по sort_year гарантирует Гильгамеша в первой стопке
    books = db.query(models.Book).join(models.Author).order_by(
        models.Book.sort_year.asc(),
        models.Author.full_name.asc(),
        models.Book.id.asc()
    ).all()

    stack_size = 10
    stacks = [books[i:i + stack_size] for i in range(0, len(books), stack_size)]
    rows = [stacks[i:i + 3] for i in range(0, len(stacks), 3)]

    return templates.TemplateResponse("index.html", {"request": request, "rows": rows})