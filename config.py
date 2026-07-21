import os
from dotenv import load_dotenv

load_dotenv()

# Авито
AVITO_BASE_URL = "https://www.avito.ru"

# Поиск товаров
SEARCH_PARAMS = {
    "electronics": {
        "keywords": ["iPhone 13", "iPhone 14", "Samsung S23"],
        "max_price": 50000,
        "min_price": 5000,
    },
}

# База данных
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///avito_prices.db")

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Рыночные цены (справочные)
MARKET_PRICES = {
    "iPhone 13": 40000,
    "iPhone 14": 55000,
    "Samsung S23": 45000,
}

# Минимальная скидка для поиска (в %)
MIN_DISCOUNT_PERCENT = 20

# Задержка между запросами (секунды)
REQUEST_DELAY = 2

# Максимум товаров на поиск
MAX_PRODUCTS_PER_QUERY = 10

# ===== 🆕 НОВЫЕ УЛУЧШЕНИЯ =====

# 1️⃣ ПЕРИОДИЧНОСТЬ МОНИТОРИНГА (в часах)
MONITOR_INTERVAL_HOURS = 1  # Каждый час

# 2️⃣ ЧЁРНЫЙ СПИСОК ПРОДАВЦОВ
BLACKLIST_SELLERS = [
    "Автолавка",  # Пример
    "Маркетплейс",  # Пример
]

# 3️⃣ МИНИМАЛЬНЫЙ РЕЙТИНГ ПРОДАВЦА (если доступен)
MIN_SELLER_RATING = 0.0  # От 0 до 5

# 4️⃣ ВЕДЕНИЕ ЛОГОВ (для отладки)
LOG_FILE = "avito_parser.log"
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# ===== SEARCH PARAMETERS =====
# Параметры поиска для разных категорий

SEARCH_PARAMS = {
    'electronics': {
        'keywords': [
            'iPhone 13',
            'Samsung Galaxy',
            'MacBook',
        ],
        'min_price': 5000,
        'max_price': 200000,
    },
    'cars': {
        'keywords': [
            'Toyota',
            'BMW',
            'Mercedes',
        ],
        'min_price': 100000,
        'max_price': 5000000,
    },
    'general': {
        'keywords': [
            'ноутбук',
            'телефон',
            'планшет',
        ],
        'min_price': 1000,
        'max_price': 100000,
    },
}