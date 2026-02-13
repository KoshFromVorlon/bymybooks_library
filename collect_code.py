import os

# Налаштування ігнорування
EXCLUDE_DIRS = {'.git', '__pycache__', '.venv', 'venv', 'env', '.idea', '.vscode', 'build', 'dist'}
EXCLUDE_FILES = {'project_context.txt', 'collect_code.py', '.DS_Store'}
ALLOWED_EXTENSIONS = {'.py', '.html', '.css', '.js', '.sql', '.txt', '.md', '.yml', '.yaml', '.ini', '.json'}


def collect_project_code(output_file='project_context.txt'):
    # Отримуємо корінь проекту (папка, де лежить цей скрипт)
    project_root = os.path.dirname(os.path.abspath(__file__))

    output_path = os.path.join(project_root, output_file)

    with open(output_path, 'w', encoding='utf-8') as outfile:
        for root, dirs, files in os.walk(project_root):
            # Виключаємо службові папки
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            for file in files:
                if file in EXCLUDE_FILES:
                    continue

                # Перевірка розширення файлу
                if not any(file.endswith(ext) for ext in ALLOWED_EXTENSIONS):
                    continue

                file_path = os.path.join(root, file)

                # ПРАВИЛЬНИЙ ВИКЛИК: os.path.relpath
                relative_path = os.path.relpath(file_path, project_root)

                try:
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        content = infile.read()

                    # Форматування за вашим запитом
                    outfile.write(f"{relative_path}\n")
                    outfile.write(f"{content}\n\n")
                    # Додаємо роздільник між файлами для зручності
                    outfile.write("-" * 40 + "\n\n")

                except Exception as e:
                    print(f"Пропущено {relative_path}: {e}")

    print(f"Готово! Файл збережено тут: {output_path}")


if __name__ == "__main__":
    collect_project_code()