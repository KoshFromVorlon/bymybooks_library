import os
import re
import shutil
import random
from collections import defaultdict
from pypdf import PdfReader
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app import models
from rich.console import Console
from rich.theme import Theme
from difflib import SequenceMatcher

# Настройка красивого вывода
custom_theme = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "danger": "bold red",
    "success": "bold green",
    "title": "bold gold3",
    "author": "italic wheat1",
    "rename": "bold cyan"
})
console = Console(theme=custom_theme)

# Палитра
COLORS = [
    "#2A1B15", "#3D2314", "#4A2511", "#1F2621",
    "#2C3A2E", "#1B2430", "#2E1B1E", "#3C2A2A"
]


def generate_slug(text):
    """Генерирует чистое имя файла из названия"""
    mapping = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'і': 'i', 'ї': 'yi', 'є': 'ye', 'ґ': 'g'
    }
    slug = ''.join(mapping.get(c, c) for c in text.lower())
    return re.sub(r'[^a-z0-9]+', '_', slug).strip('_')


def roman_to_int(s):
    roman = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    total = prev_value = 0
    for char in reversed(s.upper()):
        value = roman.get(char, 0)
        total += value if value >= prev_value else -value
        prev_value = value
    return total


def parse_txt_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.read().strip().split('\n')

    parsed = []
    for line in lines:
        line = line.strip()
        if not line or not re.match(r'^\d+\.', line): continue

        # Извлекаем дату
        date_str = "Неизвестно"
        start_paren, end_paren = line.rfind('('), line.rfind(')')
        content_part = line
        if start_paren != -1 and end_paren != -1:
            date_str = line[start_paren + 1:end_paren].strip()
            content_part = line[:start_paren].strip()

        # Чистим от номера "1. "
        content_part = re.sub(r'^\d+\.\s*', '', content_part)

        # Разделяем автора и название
        if " — " in content_part:
            author, title = content_part.split(" — ", 1)
        else:
            author, title = "Классика / Аноним", content_part

        title = title.replace('«', '').replace('»', '').strip()
        author = author.strip()

        # Парсим год для сортировки
        sort_year = 2025
        arab_match = re.findall(r'\d+', date_str)
        if arab_match:
            year = int(arab_match[0])
        else:
            roman_match = re.search(r'\b([IVXLCDM]+)\b', date_str, re.IGNORECASE)
            year = roman_to_int(roman_match.group(1)) if roman_match else None

        if year:
            is_bc = "до н" in date_str.lower()
            is_century = any(x in date_str.lower() for x in ["в.", "ст.", "вв."])
            sort_year = (year - 1) * 100 if is_century else year
            if is_bc: sort_year = -sort_year

        parsed.append({
            "author": author,
            "title": title,
            "year_raw": date_str,
            "sort_year": sort_year,
            "slug": generate_slug(title)
        })
    return parsed


def find_best_file_match(target_slug, files_pool):
    """
    Ищет файл в папке, который больше всего похож на target_slug.
    Игнорирует старые номера в начале файла (например '005_').
    """
    best_match = None
    best_ratio = 0.0

    # Нормализуем цель (убираем подчеркивания для сравнения)
    clean_target = target_slug.replace('_', ' ')

    for filename in files_pool:
        # Убираем расширение
        name_no_ext = os.path.splitext(filename)[0]
        # Убираем старый номер в начале (если есть 3 цифры и _)
        clean_name = re.sub(r'^\d{3}[_\s]+', '', name_no_ext).replace('_', ' ').lower()

        # 1. Прямое вхождение (очень надежно)
        if clean_target in clean_name:
            return filename, 1.0  # 100% уверенность

        # 2. Нечеткое сравнение (если есть опечатки или разные форматы)
        ratio = SequenceMatcher(None, clean_target, clean_name).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = filename

    # Считаем совпадением только если похожесть > 60%
    if best_ratio > 0.6:
        return best_match, best_ratio

    return None, 0


def sync_library():
    console.print("\n[bold white on #2A1B15] 🏛️ ГЛОБАЛЬНАЯ СИНХРОНИЗАЦИЯ БИБЛИОТЕКИ [/]\n")

    # 1. ОБНОВЛЕНИЕ СТРУКТУРЫ БД
    # console.print("[info]⟳ Удаление старых таблиц...[/]")
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    # 2. ЧТЕНИЕ СПИСКА (ЭТАЛОН)
    if not os.path.exists("books_list.txt"):
        console.print("[danger]🔥 ОШИБКА: Файл books_list.txt не найден![/]")
        return

    books_data = parse_txt_file("books_list.txt")
    total_books = len(books_data)

    # 3. ЗАПОЛНЕНИЕ БД
    db_books = []  # Сохраним объекты для дальнейшей работы

    for i, item in enumerate(books_data, start=1):
        author = db.query(models.Author).filter_by(full_name=item['author']).first()
        if not author:
            author = models.Author(full_name=item['author'])
            db.add(author)
            db.flush()

        book = models.Book(
            title=item['title'],
            author_id=author.id,
            year_raw=item['year_raw'],
            sort_year=item['sort_year'],
            hex_color=random.choice(COLORS),
            slug=item['slug'],
            position=i  # ВАЖНО: Позиция равна номеру строки в файле
        )
        db.add(book)
        db_books.append(book)

        console.print(f"[dim]#{i}[/] [success]БД:[/success] {book.title}")

    db.commit()

    # 4. СИНХРОНИЗАЦИЯ ФАЙЛОВ (Самая важная часть)
    books_dir = os.path.join("app", "static", "books")
    os.makedirs(books_dir, exist_ok=True)

    console.print(f"\n[bold white on #005f87] 📂 НАВОДИМ ПОРЯДОК В ФАЙЛАХ... [/]\n")

    # Получаем список всех PDF в папке
    files_in_folder = [f for f in os.listdir(books_dir) if f.endswith(".pdf")]

    # Множество уже использованных файлов, чтобы не присвоить один файл двум книгам
    claimed_files = set()

    for book in db_books:
        # Идеальное имя файла, которое ДОЛЖНО быть
        ideal_filename = f"{book.position:03d}_{book.slug}.pdf"
        ideal_path = os.path.join(books_dir, ideal_filename)

        # Сначала проверяем, вдруг файл уже назван идеально
        if ideal_filename in files_in_folder:
            actual_file = ideal_filename
            claimed_files.add(actual_file)
        else:
            # Если идеального нет, ищем "потеряшку" среди свободных файлов
            available_files = [f for f in files_in_folder if f not in claimed_files]
            found_name, confidence = find_best_file_match(book.slug, available_files)

            if found_name:
                # Нашли старый или кривой файл! Переименовываем.
                old_path = os.path.join(books_dir, found_name)

                # Проверка: если целевой файл занят заглушкой, удаляем заглушку
                if os.path.exists(ideal_path):
                    os.remove(ideal_path)

                os.rename(old_path, ideal_path)
                claimed_files.add(ideal_filename)  # Теперь он занят под новым именем

                # Обновляем список файлов в памяти, так как мы переименовали
                files_in_folder = [f for f in os.listdir(books_dir) if f.endswith(".pdf")]

                console.print(f"[rename]✎ ПЕРЕИМЕНОВАНО:[/rename] {found_name} ➔ [bold]{ideal_filename}[/]")
                actual_file = ideal_filename
            else:
                # Файла нет вообще. Создаем ЗАГЛУШКУ, чтобы порядок сохранялся.
                if not os.path.exists(ideal_path):
                    with open(ideal_path, 'wb') as f:
                        pass  # Создаем пустой файл
                    console.print(f"[warning]∅ Заглушка:[/warning] {ideal_filename} (файла не было)")
                actual_file = ideal_filename

        # 5. ПРОВЕРКА СТАТУСА (ЗЕЛЕНЫЙ/КРАСНЫЙ)
        final_path = os.path.join(books_dir, actual_file)
        book.pdf_file = f"/static/books/{actual_file}"

        try:
            file_size = os.path.getsize(final_path)
            # ЛОГИКА: > 50КБ = ЗЕЛЕНЫЙ
            if file_size > 50000:
                # Пытаемся считать страницы для красоты
                try:
                    reader = PdfReader(final_path)
                    cnt = len(reader.pages)
                    book.pages = cnt if cnt > 0 else 1
                except:
                    book.pages = 1  # Не смогли считать, но файл большой -> ставим 1
            else:
                book.pages = 0  # Заглушка -> 0
        except:
            book.pages = 0

    db.commit()
    db.close()
    console.print("\n[bold green]✅ ГОТОВО! ПАПКА СИНХРОНИЗИРОВАНА С TXT СПИСКОМ.[/]\n")


if __name__ == "__main__":
    sync_library()