import sqlite3

db_file = "avito_prices.db"

try:
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Получи список всех таблиц
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("📊 Таблицы в БД:")
    for table in tables:
        print(f"  - {table[0]}")
    
    print("\n📋 Структура таблицы 'products':")
    cursor.execute("PRAGMA table_info(products);")
    columns = cursor.fetchall()
    
    for column in columns:
        print(f"  - {column[1]} ({column[2]})")
    
    conn.close()
    print("\n✅ БД в порядке!")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")