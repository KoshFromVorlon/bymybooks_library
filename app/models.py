from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)

    books = relationship("Book", back_populates="author")


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    sort_year = Column(Integer)
    year_raw = Column(String)
    hex_color = Column(String)
    author_id = Column(Integer, ForeignKey("authors.id"))

    # === НОВЫЕ ПОЛЯ ДЛЯ ФАЙЛОВ ===
    original_file = Column(String, nullable=True)  # Путь к загруженному файлу (fb2, docx и т.д.)
    epub_file = Column(String, nullable=True)  # Путь к готовому EPUB для читалки

    author = relationship("Author", back_populates="books")