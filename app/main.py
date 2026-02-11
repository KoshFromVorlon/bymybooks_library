from fastapi import FastAPI, Request, Depends, HTTPException, Body
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from . import models, database
import os

app = FastAPI()

# Mount the static directory for CSS, covers, and book files
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/")
def read_root(request: Request, db: Session = Depends(database.get_db)):
    """
    Main page: Displays books on shelves sorted by their database ID.
    """
    books = db.query(models.Book).join(models.Author).order_by(
        models.Book.id.asc()
    ).all()

    stack_size = 10
    stacks = [books[i:i + stack_size] for i in range(0, len(books), stack_size)]
    rows = [stacks[i:i + 3] for i in range(0, len(stacks), 3)]

    return templates.TemplateResponse("index.html", {"request": request, "rows": rows})


@app.get("/book/{book_id}")
def read_book(request: Request, book_id: int, db: Session = Depends(database.get_db)):
    """
    Reader page: Displays the specific book in the EPUB reader interface.
    """
    book = db.query(models.Book).filter(models.Book.id == book_id).first()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    return templates.TemplateResponse("reader.html", {"request": request, "book": book})


@app.post("/book/{book_id}/bookmark")
def save_bookmark(
        book_id: int,
        cfi: str = Body(..., embed=True),
        db: Session = Depends(database.get_db)
):
    """
    Saves the current reading position (EPUB CFI) to the PostgreSQL database.
    """
    book = db.query(models.Book).filter(models.Book.id == book_id).first()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Update the last_location column with the CFI string from the reader
    book.last_location = cfi
    db.commit()

    return {"status": "success", "cfi": cfi}


@app.get("/sync-files")
def sync_book_files(db: Session = Depends(database.get_db)):
    """
    File scanner: Maps files in app/static/books to books in the DB based on ID.
    Example: '379.epub' will be assigned to the book with ID 379.
    """
    books_dir = "app/static/books"

    # Ensure the directory exists
    os.makedirs(books_dir, exist_ok=True)

    updated_count = 0

    # Scan all files in the books directory
    for filename in os.listdir(books_dir):
        # Extract ID and extension (e.g., "379" and ".epub")
        name, ext = os.path.splitext(filename)

        # Check if the filename is an integer ID
        if name.isdigit():
            book_id = int(name)
            # Find the book in the database
            book = db.query(models.Book).filter(models.Book.id == book_id).first()

            if book:
                file_path = f"/static/books/{filename}"
                # Assign file path based on extension type
                if ext.lower() == '.epub':
                    book.epub_file = file_path
                else:
                    book.original_file = file_path
                updated_count += 1

    db.commit()
    return {
        "status": "success",
        "updated_books": updated_count,
        "message": f"PostgreSQL database synchronized! Updated books: {updated_count}"
    }