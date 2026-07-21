"""
Клавиатуры и кнопки для Telegram бота
"""

from typing import List, Dict


class KeyboardBuilder:
    """Построитель клавиатур"""
    
    @staticmethod
    def main_menu():
        """Главное меню"""
        return {
            'inline_keyboard': [
                [
                    {'text': '📊 Статистика', 'callback_data': 'stats'},
                    {'text': '🔥 Топ скидок', 'callback_data': 'best'},
                ],
                [
                    {'text': '📦 Последние', 'callback_data': 'recent'},
                    {'text': '⚙️ Настройки', 'callback_data': 'settings'},
                ],
                [
                    {'text': '🔍 Поиск товаров', 'callback_data': 'search'},
                    {'text': '🚀 Запустить сканирование', 'callback_data': 'scan'},
                ],
                [
                    {'text': '📖 Справка', 'callback_data': 'help'},
                ],
            ]
        }
    
    @staticmethod
    def settings_menu():
        """Меню настроек"""
        return {
            'inline_keyboard': [
                [
                    {'text': '📝 Выбрать товары', 'callback_data': 'select_products'},
                    {'text': '💰 Минимальная скидка', 'callback_data': 'min_discount'},
                ],
                [
                    {'text': '💵 Макс цена', 'callback_data': 'max_price'},
                    {'text': '⭐ Минимальный рейтинг', 'callback_data': 'min_rating'},
                ],
                [
                    {'text': '🚫 Чёрный список', 'callback_data': 'blacklist'},
                    {'text': '⏱️ Интервал сканирования', 'callback_data': 'scan_interval'},
                ],
                [
                    {'text': '◀️ Назад', 'callback_data': 'main_menu'},
                ],
            ]
        }
    
    @staticmethod
    def products_selection():
        """Меню выбора товаров"""
        return {
            'inline_keyboard': [
                [
                    {'text': '📱 Смартфоны', 'callback_data': 'add_product_smartphones'},
                    {'text': '⌚ Умные часы', 'callback_data': 'add_product_watches'},
                ],
                [
                    {'text': '💻 Ноутбуки', 'callback_data': 'add_product_laptops'},
                    {'text': '🎧 Наушники', 'callback_data': 'add_product_headphones'},
                ],
                [
                    {'text': '📷 Камеры', 'callback_data': 'add_product_cameras'},
                    {'text': '🎮 Консоли', 'callback_data': 'add_product_consoles'},
                ],
                [
                    {'text': '➕ Добавить свой товар', 'callback_data': 'custom_product'},
                    {'text': '👁️ Мои товары', 'callback_data': 'my_products'},
                ],
                [
                    {'text': '◀️ Назад', 'callback_data': 'settings'},
                ],
            ]
        }
    
    @staticmethod
    def yes_no():
        """Кнопки Да/Нет"""
        return {
            'inline_keyboard': [
                [
                    {'text': '✅ Да', 'callback_data': 'yes'},
                    {'text': '❌ Нет', 'callback_data': 'no'},
                ],
            ]
        }
    
    @staticmethod
    def back_button():
        """Кнопка назад"""
        return {
            'inline_keyboard': [
                [
                    {'text': '◀️ Назад', 'callback_data': 'main_menu'},
                ],
            ]
        }
    
    @staticmethod
    def manage_products():
        """Управление товарами"""
        return {
            'inline_keyboard': [
                [
                    {'text': '➕ Добавить', 'callback_data': 'add_product'},
                    {'text': '➖ Удалить', 'callback_data': 'remove_product'},
                ],
                [
                    {'text': '👁️ Мои товары', 'callback_data': 'my_products'},
                ],
                [
                    {'text': '◀️ Назад', 'callback_data': 'settings'},
                ],
            ]
        }