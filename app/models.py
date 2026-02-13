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

    pdf_file = Column(String, nullable=True)     # Ссылка на веб-путь
    cover_image = Column(String, nullable=True)  # Ссылка на веб-путь обложки
    pages = Column(Integer, default=0)           # Для толщины
    position = Column(Integer, index=True)       # Хронологический номер
    slug = Column(String, nullable=False)        # Техническое имя

    author = relationship("Author", back_populates="books")