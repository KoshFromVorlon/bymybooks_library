import os
import re
import random
from collections import defaultdict
from pypdf import PdfReader
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app import models

# Палитра "Антикварная библиотека"
COLORS = [
    "#2A1B15",  # Глубокий коричневый (старая кожа)
    "#3D2314",  # Темный каштан
    "#4A2511",  # Ржавая кожа
    "#1F2621",  # Очень темный зеленый
    "#2C3A2E",  # Темный изумруд
    "#1B2430",  # Полуночный синий
    "#2E1B1E",  # Глубокий винный (бордо)
    "#3C2A2A"  # Выцветший коричневый
]


def generate_slug(text):
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
    """Читает TXT и возвращает список словарей с правильным годом."""
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.read().strip().split('\n')

    parsed = []
    for line in lines:
        line = line.strip()
        if not line or not re.match(r'^\d+\.', line): continue

        date_str = "Неизвестно"
        start_paren, end_paren = line.rfind('('), line.rfind(')')
        content_part = line

        if start_paren != -1 and end_paren != -1:
            date_str = line[start_paren + 1:end_paren].strip()
            content_part = line[:start_paren].strip()

        content_part = re.sub(r'^\d+\.\s*', '', content_part)
        if " — " in content_part:
            author, title = content_part.split(" — ", 1)
        else:
            author, title = "Классика / Аноним", content_part

        title = title.replace('«', '').replace('»', '').strip()
        author = author.strip()

        # Парсинг года
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
            "author": author, "title": title, "year_raw": date_str, "sort_year": sort_year, "slug": generate_slug(title)
        })
    return parsed


def sync_library():
    print("🚀 Старт глобальной синхронизации...\n")

    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 1. СИНХРОНИЗАЦИЯ БАЗЫ (Добавляем новые из TXT)
    books_data = parse_txt_file("books_list.txt")
    for item in books_data:
        author = db.query(models.Author).filter_by(full_name=item['author']).first()
        if not author:
            author = models.Author(full_name=item['author'])
            db.add(author)
            db.flush()

        book = db.query(models.Book).filter_by(title=item['title']).first()
        if not book:
            book = models.Book(
                title=item['title'], author_id=author.id, year_raw=item['year_raw'],
                sort_year=item['sort_year'], hex_color=random.choice(COLORS), slug=item['slug']
            )
            db.add(book)
            print(f"[БД] Добавлена новая книга: {book.title}")
    db.commit()

    # =========================================================================
    # 2. ПЕРЕРАСЧЕТ ХРОНОЛОГИИ (С УМНОЙ ГРУППИРОВКОЙ)
    # =========================================================================
    all_books = db.query(models.Book).all()

    authors_dict = defaultdict(list)
    for book in all_books:
        # ИЗОЛИРУЕМ АНОНИМОВ: Если автор "Аноним", кладем книгу в её личную группу (по ID)
        if "Аноним" in book.author.full_name:
            authors_dict[f"anon_{book.id}"].append(book)
        else:
            # Обычных авторов группируем вместе
            authors_dict[book.author_id].append(book)

    # Шаг А: Сортируем книги ВНУТРИ каждого автора по хронологии
    for group_key in authors_dict:
        authors_dict[group_key].sort(key=lambda b: (b.sort_year, b.id))

    # Шаг Б: Сортируем ГРУППЫ по дате выхода их ПЕРВОЙ книги
    sorted_group_keys = sorted(
        authors_dict.keys(),
        key=lambda k: (authors_dict[k][0].sort_year, str(k))
    )

    # Шаг В: Выстраиваем их в одну линию и раздаем новые позиции
    final_sorted_books = []
    for group_key in sorted_group_keys:
        final_sorted_books.extend(authors_dict[group_key])

    for i, book in enumerate(final_sorted_books, start=1):
        book.position = i

    db.commit()
    # =========================================================================

    # 3. РАБОТА С ФАЙЛАМИ И ПАПКАМИ
    books_dir = os.path.join("app", "static", "books")
    covers_dir = os.path.join("app", "static", "covers")
    os.makedirs(books_dir, exist_ok=True)
    os.makedirs(covers_dir, exist_ok=True)

    for book in final_sorted_books:
        target_prefix = f"{book.position:03d}_{book.slug}"
        target_pdf = f"{target_prefix}.pdf"
        target_jpg = f"{target_prefix}.jpg"

        def process_file(directory, extension, target_name):
            target_path = os.path.join(directory, target_name)
            matching_files = [f for f in os.listdir(directory) if book.slug in f and f.endswith(extension)]

            if matching_files and target_name not in matching_files:
                old_path = os.path.join(directory, matching_files[0])
                if not os.path.exists(target_path):
                    os.replace(old_path, target_path)
                    print(f"[ФАЙЛЫ] Переименован: {matching_files[0]} -> {target_name}")

            return target_path if os.path.exists(target_path) else None

        pdf_path = process_file(books_dir, ".pdf", target_pdf)
        cover_path = process_file(covers_dir, ".jpg", target_jpg)

        # 4. ПОДСЧЕТ СТРАНИЦ
        if pdf_path:
            try:
                # Игнорируем пустые файлы-заглушки (меньше 1 КБ), чтобы не спамить ошибками
                if os.path.getsize(pdf_path) > 1024:
                    reader = PdfReader(pdf_path)
                    pages_count = len(reader.pages)
                    if book.pages != pages_count:
                        book.pages = pages_count
                        print(f"[PDF] {book.title} — {pages_count} стр.")
            except Exception:
                pass

                # Обновляем ссылки в БД
        book.pdf_file = f"/static/books/{target_pdf}" if pdf_path else None
        book.cover_image = f"/static/covers/{target_jpg}" if cover_path else None

    db.commit()
    db.close()
    print("\n✅ Синхронизация завершена! Книги выстроены идеально.")


if __name__ == "__main__":
    sync_library()
