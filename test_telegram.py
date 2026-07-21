import sys
import traceback

print("=" * 60)
print("🧪 ТЕСТИРОВАНИЕ TELEGRAM БОТА")
print("=" * 60)

try:
    print("\n1️⃣  Импортируем конфиг...")
    from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
    print("✅ Config импортирован")
    
    print("\n2️⃣  Проверяем переменные...")
    print(f"   TELEGRAM_BOT_TOKEN: {'Установлен' if TELEGRAM_BOT_TOKEN else '❌ НЕ установлен'}")
    print(f"   TELEGRAM_CHAT_ID: {'Установлен' if TELEGRAM_CHAT_ID else '❌ НЕ установлен'}")
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("\n❌ ОШИБКА: Проверь .env файл!")
        print("   Должны быть заполнены:")
        print("   TELEGRAM_BOT_TOKEN=...")
        print("   TELEGRAM_CHAT_ID=...")
        sys.exit(1)
    
    print(f"\n   Token (первые 20 символов): {str(TELEGRAM_BOT_TOKEN)[:20]}...")
    print(f"   Chat ID: {TELEGRAM_CHAT_ID}")
    
    print("\n3️⃣  Импортируем requests...")
    import requests
    print("✅ Requests импортирован")
    
    token = TELEGRAM_BOT_TOKEN
    chat_id = TELEGRAM_CHAT_ID
    
    print("\n4️⃣  Проверяем бота через API...")
    url = f"https://api.telegram.org/bot{token}/getMe"
    print(f"   URL: {url[:50]}...")
    
    response = requests.get(url, timeout=10)
    print(f"   Статус: {response.status_code}")
    print(f"   Ответ: {response.text[:200]}")
    
    result = response.json()
    print(f"   JSON: {result}")
    
    if result.get('ok'):
        print("✅ Бот работает!")
        bot_info = result.get('result', {})
        print(f"   Имя бота: {bot_info.get('first_name')}")
        print(f"   Username: @{bot_info.get('username')}")
    else:
        print("❌ Ошибка API:")
        print(result)
    
    print("\n5️⃣  Отправляем тестовое сообщение...")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': '🧪 Тестовое сообщение от парсера Авито!',
    }
    
    response = requests.post(url, data=data, timeout=10)
    print(f"   Статус: {response.status_code}")
    print(f"   Ответ: {response.text}")
    
    result = response.json()
    
    if result.get('ok'):
        print("✅ Сообщение отправлено!")
        print(f"   Message ID: {result['result']['message_id']}")
        print("   Проверь Telegram - должно быть сообщение! ✅")
    else:
        print("❌ Ошибка отправки:")
        error = result.get('description', result)
        print(f"   {error}")
    
    print("\n" + "=" * 60)
    print("✅ ТЕСТ ЗАВЕРШЕН")
    print("=" * 60)

except Exception as e:
    print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА:")
    print(f"   {type(e).__name__}: {e}")
    print("\nПолный stack trace:")
    traceback.print_exc()
    sys.exit(1)