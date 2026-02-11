import os
import shutil
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app import models

# Словарь для транслитерации (Русский -> Английский для имен файлов)
TRANSLIT_MAP = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '',
    'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya', ' ': '_'
}


def slugify(text):
    """Превращает 'Эпос о Гильгамеше' в 'epos_o_gilgameshe'"""
    if not text:
        return "unknown"

    slug = ""
    for char in text.lower():
        if char in TRANSLIT_MAP:
            slug += TRANSLIT_MAP[char]
        elif char.isalnum() or char == "_" or char == "-":
            slug += char
        # Все остальные символы (например, двоеточия) игнорируем
    return slug


def fix_everything():
    session = SessionLocal()
    books_dir = "app/static/covers"
    os.makedirs(books_dir, exist_ok=True)

    # Получаем все книги, сортируем по позиции
    books = session.query(models.Book).order_by(models.Book.position).all()

    print(f"Найдено книг: {len(books)}")

    for book in books:
        # 1. Генерируем нормальный слаг из названия
        new_slug = slugify(book.title)

        # Обновляем в базе, если он отличается
        if book.slug != new_slug:
            book.slug = new_slug
            session.add(book)

        # 2. Формируем правильное имя файла: 001_slug.jpg
        # zfill(3) делает из 1 -> 001, из 25 -> 025
        filename = f"{str(book.position).zfill(3)}_{new_slug}.jpg"
        file_path = os.path.join(books_dir, filename)

        # 3. Создаем файл-заглушку, если его нет
        if not os.path.exists(file_path):
            # Создаем пустой файл, чтобы ты мог его потом заменить
            # Или, если у тебя есть какая-то картинка 'template.jpg', можно копировать её
            with open(file_path, 'wb') as f:
                pass  # Просто создаем файл нулевого размера
            print(f"[+] Создан файл: {filename}")
        else:
            print(f"[OK] Файл уже есть: {filename}")

    # Сохраняем изменения в БД
    session.commit()
    print("\nГотово! База обновлена, файлы созданы.")
    session.close()


if __name__ == "__main__":
    fix_everything()