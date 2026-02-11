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

    # Ссылка на PDF файл
    pdf_file = Column(String, nullable=True)

    # Новое поле: Количество страниц (для толщины корешка)
    pages = Column(Integer, default=0)

    # Позиция на полке и техническое имя для файлов
    position = Column(Integer, index=True, nullable=False)
    slug = Column(String, nullable=False)

    author = relationship("Author", back_populates="books")