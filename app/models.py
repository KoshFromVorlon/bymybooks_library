from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship  # Добавь этот импорт
from .database import Base


class Author(Base):
    __tablename__ = "authors"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, unique=True, nullable=False)

    # Добавь эту строку, чтобы автор "видел" свои книги
    books = relationship("Book", back_populates="author")


class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    year_raw = Column(String)
    sort_year = Column(Integer)
    hex_color = Column(String)
    fun_facts = Column(Text)
    content = Column(Text)
    cover_image = Column(String)

    author_id = Column(Integer, ForeignKey("authors.id"))

    # ВОТ ЭТА СТРОКА РЕШИТ ПРОБЛЕМУ:
    # Она создает виртуальное поле .author у каждой книги
    author = relationship("Author", back_populates="books")