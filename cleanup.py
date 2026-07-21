import os
import shutil
from pathlib import Path

print("🧹 Очистка проекта...")

# Удаляем БД файлы
for db_file in Path('.').glob('*.db'):
    try:
        db_file.unlink()
        print(f"✅ Удалён: {db_file}")
    except Exception as e:
        print(f"❌ Ошибка удаления {db_file}: {e}")

# Удаляем кеш
for cache_dir in Path('.').rglob('__pycache__'):
    try:
        shutil.rmtree(cache_dir)
        print(f"✅ Удалён: {cache_dir}")
    except Exception as e:
        print(f"❌ Ошибка удаления {cache_dir}: {e}")

print("\n✅ Очистка завершена!")
print("🚀 Запусти: python main.py")