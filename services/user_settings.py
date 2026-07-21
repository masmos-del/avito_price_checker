import json
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserSettings:
    """Управление настройками пользователя"""
    
    SETTINGS_FILE = "user_settings.json"
    
    def __init__(self):
        self.settings = self._load_settings()
    
    def _load_settings(self):
        """Загрузить настройки из файла"""
        if Path(self.SETTINGS_FILE).exists():
            try:
                with open(self.SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"❌ Ошибка загрузки настроек: {e}")
                return self._default_settings()
        return self._default_settings()
    
    def _default_settings(self):
        """Настройки по умолчанию"""
        return {
            'min_discount': 20,
            'max_price': 100000,
            'min_rating': 0.0,
            'scan_interval_hours': 1,
            'tracked_products': [
                'iPhone 13',
                'iPhone 14',
                'Samsung S23'
            ],
            'blacklist_sellers': [],
            'last_updated': datetime.now().isoformat(),
        }
    
    def _save_settings(self):
        """Сохранить настройки в файл"""
        try:
            self.settings['last_updated'] = datetime.now().isoformat()
            with open(self.SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            logger.info("💾 Настройки сохранены")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения настроек: {e}")
            return False
    
    # ===== СКИДКА =====
    def get_min_discount(self):
        """Получить минимальную скидку"""
        return self.settings.get('min_discount', 20)
    
    def set_min_discount(self, discount):
        """Установить минимальную скидку"""
        try:
            discount = int(discount)
            if 0 <= discount <= 100:
                self.settings['min_discount'] = discount
                self._save_settings()
                logger.info(f"✅ Минимальная скидка: {discount}%")
                return True
            else:
                logger.warning("⚠️ Скидка должна быть от 0 до 100")
                return False
        except ValueError:
            logger.warning("⚠️ Скидка должна быть числом")
            return False
    
    # ===== МАКСИМАЛЬНАЯ ЦЕНА =====
    def get_max_price(self):
        """Получить максимальную цену"""
        return self.settings.get('max_price', 100000)
    
    def set_max_price(self, price):
        """Установить максимальную цену"""
        try:
            price = int(price)
            if price > 0:
                self.settings['max_price'] = price
                self._save_settings()
                logger.info(f"✅ Максимальная цена: {price}₽")
                return True
            else:
                logger.warning("⚠️ Цена должна быть больше нуля")
                return False
        except ValueError:
            logger.warning("⚠️ Цена должна быть числом")
            return False
    
    # ===== МИНИМАЛЬНЫЙ РЕЙТИНГ =====
    def get_min_rating(self):
        """Получить минимальный рейтинг"""
        return self.settings.get('min_rating', 0.0)
    
    def set_min_rating(self, rating):
        """Установить минимальный рейтинг"""
        try:
            rating = float(rating)
            if 0 <= rating <= 5:
                self.settings['min_rating'] = rating
                self._save_settings()
                logger.info(f"✅ Минимальный рейтинг: {rating}")
                return True
            else:
                logger.warning("⚠️ Рейтинг должен быть от 0 до 5")
                return False
        except ValueError:
            logger.warning("⚠️ Рейтинг должен быть числом")
            return False
    
    # ===== ТОВАРЫ =====
    def get_tracked_products(self):
        """Получить список отслеживаемых товаров"""
        return self.settings.get('tracked_products', [])
    
    def add_tracked_product(self, product):
        """Добавить товар для отслеживания"""
        products = self.get_tracked_products()
        if product not in products:
            products.append(product)
            self.settings['tracked_products'] = products
            self._save_settings()
            logger.info(f"✅ Товар добавлен: {product}")
            return True
        else:
            logger.warning(f"⚠️ Товар уже отслеживается: {product}")
            return False
    
    def remove_tracked_product(self, product):
        """Удалить товар из отслеживания"""
        products = self.get_tracked_products()
        if product in products:
            products.remove(product)
            self.settings['tracked_products'] = products
            self._save_settings()
            logger.info(f"✅ Товар удалён: {product}")
            return True
        else:
            logger.warning(f"⚠️ Товар не найден: {product}")
            return False
    
    # ===== ЧЁРНЫЙ СПИСОК =====
    def get_blacklist(self):
        """Получить чёрный список продавцов"""
        return self.settings.get('blacklist_sellers', [])
    
    def add_to_blacklist(self, seller):
        """Добавить продавца в чёрный список"""
        blacklist = self.get_blacklist()
        if seller not in blacklist:
            blacklist.append(seller)
            self.settings['blacklist_sellers'] = blacklist
            self._save_settings()
            logger.info(f"✅ Продавец добавлен в чёрный список: {seller}")
            return True
        else:
            logger.warning(f"⚠️ Продавец уже в списке: {seller}")
            return False
    
    def remove_from_blacklist(self, seller):
        """Удалить продавца из чёрного списка"""
        blacklist = self.get_blacklist()
        if seller in blacklist:
            blacklist.remove(seller)
            self.settings['blacklist_sellers'] = blacklist
            self._save_settings()
            logger.info(f"✅ Продавец удалён из чёрного списка: {seller}")
            return True
        else:
            logger.warning(f"⚠️ Продавец не найден: {seller}")
            return False
    
    # ===== ИНТЕРВАЛ СКАНИРОВАНИЯ =====
    def get_scan_interval(self):
        """Получить интервал сканирования"""
        return self.settings.get('scan_interval_hours', 1)
    
    def set_scan_interval(self, hours):
        """Установить интервал сканирования"""
        try:
            hours = int(hours)
            if hours > 0:
                self.settings['scan_interval_hours'] = hours
                self._save_settings()
                logger.info(f"✅ Интервал сканирования: {hours} часов")
                return True
            else:
                logger.warning("⚠️ Интервал должен быть больше нуля")
                return False
        except ValueError:
            logger.warning("⚠️ Интервал должен быть числом")
            return False
    
    # ===== ОБЩЕЕ =====
    def get_all_settings(self):
        """Получить все настройки"""
        return self.settings
    
    def reset_to_default(self):
        """Сбросить на стандартные настройки"""
        self.settings = self._default_settings()
        self._save_settings()
        logger.info("✅ Настройки сброшены на стандартные")
        return True


# Глобальный объект настроек
user_settings = UserSettings()