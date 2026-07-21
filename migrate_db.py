import sqlite3

db_file = "avito_prices.db"

try:
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    print("🔄 Добавление недостающих колонок...")
    
    # Добавляем is_sent_to_telegram
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN is_sent_to_telegram BOOLEAN DEFAULT 0")
        print("✅ Добавлена колонка: is_sent_to_telegram")
    except sqlite3.OperationalError as e:
        print(f"⚠️ is_sent_to_telegram: {e}")
    
    # Добавляем sent_at
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN sent_at DATETIME")
        print("✅ Добавлена колонка: sent_at")
    except sqlite3.OperationalError as e:
        print(f"⚠️ sent_at: {e}")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Миграция завершена!")
    print("🚀 Теперь можешь запустить: python main.py")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")