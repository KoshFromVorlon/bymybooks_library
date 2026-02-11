from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class Author(Base):
    """
    Model representing book authors.
    """
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)

    # Relationships
    books = relationship("Book", back_populates="author")


class Book(Base):
    """
    Model representing books and their associated files/metadata.
    """
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    sort_year = Column(Integer)
    year_raw = Column(String)
    hex_color = Column(String)
    author_id = Column(Integer, ForeignKey("authors.id"))

    # === FILE STORAGE FIELDS ===
    # Path to the originally uploaded file (fb2, docx, etc.)
    original_file = Column(String, nullable=True)
    # Path to the processed EPUB file used by the reader
    epub_file = Column(String, nullable=True)

    # === READING PROGRESS ===
    # Stores the last reading position as an EPUB CFI string
    last_location = Column(String, nullable=True)

    # Relationships
    author = relationship("Author", back_populates="books")