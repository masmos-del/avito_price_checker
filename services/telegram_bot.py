import logging
import requests
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from models import (
    get_session, Product, get_statistics, 
    get_recent_products, get_best_deals
)
from services.telegram_keyboard import KeyboardBuilder
from services.user_settings import user_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram бот с кнопками и настройками"""
    
    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        self.user_state = {}  # Для отслеживания состояния пользователя
    
    def send_message(self, text, parse_mode='HTML', reply_markup=None):
        """Отправить сообщение с клавиатурой"""
        data = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': parse_mode,
        }
        
        if reply_markup:
            import json
            data['reply_markup'] = json.dumps(reply_markup)
        
        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("✅ Сообщение отправлено")
                return True
            else:
                logger.error(f"❌ Ошибка отправки: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Ошибка подключения: {e}")
            return False
    
    def answer_callback(self, callback_query_id, text=None, show_alert=False):
        """Ответить на callback запрос"""
        data = {
            'callback_query_id': callback_query_id,
        }
        
        if text:
            data['text'] = text
            data['show_alert'] = show_alert
        
        try:
            requests.post(
                f"{self.api_url}/answerCallbackQuery",
                data=data,
                timeout=10
            )
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка ответа: {e}")
            return False
    
    def edit_message(self, message_id, text, reply_markup=None):
        """Отредактировать сообщение"""
        data = {
            'chat_id': self.chat_id,
            'message_id': message_id,
            'text': text,
            'parse_mode': 'HTML',
        }
        
        if reply_markup:
            import json
            data['reply_markup'] = json.dumps(reply_markup)
        
        try:
            response = requests.post(
                f"{self.api_url}/editMessageText",
                data=data,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ Ошибка редактирования: {e}")
            return False
    
    def send_start_message(self):
        """Приветственное сообщение"""
        message = (
            f"🤖 <b>AVITO PRICE CHECKER</b>\n\n"
            f"✅ Бот запущен и готов к работе\n\n"
            f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"📋 Используй кнопки ниже для навигации"
        )
        self.send_message(message, reply_markup=KeyboardBuilder.main_menu())
    
    # ===== ОСНОВНЫЕ КОМАНДЫ =====
    
    def show_main_menu(self):
        """Показать главное меню"""
        message = (
            f"📱 <b>ГЛАВНОЕ МЕНЮ</b>\n\n"
            f"Выбери действие:"
        )
        self.send_message(message, reply_markup=KeyboardBuilder.main_menu())
    
    def send_statistics(self):
        """Статистика"""
        stats = get_statistics()
        
        message = (
            f"📊 <b>СТАТИСТИКА МОНИТОРИНГА</b>\n\n"
            f"📦 Всего товаров: <b>{stats['total_products']}</b>\n"
            f"💰 Выгодных предложений: <b>{stats['profitable_products']}</b>\n"
            f"📤 Отправлено в Telegram: <b>{stats['sent_products']}</b>\n\n"
            f"📈 Средняя скидка: <b>{stats['avg_discount']}%</b>\n"
            f"🔥 Максимальная скидка: <b>{stats['max_discount']}%</b>\n\n"
            f"⏰ Обновлено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        self.send_message(message, reply_markup=KeyboardBuilder.back_button())
    
    def send_recent_products(self):
        """Последние товары"""
        products = get_recent_products(limit=5)
        
        if not products:
            message = "❌ Товаров нет"
        else:
            message = "📦 <b>ПОСЛЕДНИЕ 5 ТОВАРОВ</b>\n\n"
            
            for i, product in enumerate(products, 1):
                discount_str = f" ({product.discount_percent}%)" if product.discount_percent else ""
                message += (
                    f"{i}. {product.title}\n"
                    f"   💵 {product.price}₽{discount_str}\n"
                    f"   📍 {product.location}\n"
                    f"   🔗 <a href='{product.url}'>Открыть</a>\n\n"
                )
        
        self.send_message(message, reply_markup=KeyboardBuilder.back_button())
    
    def send_best_deals(self):
        """Топ скидок"""
        products = get_best_deals(limit=5)
        
        if not products:
            message = "❌ Выгодных предложений нет"
        else:
            message = "🔥 <b>ТОП 5 СКИДОК</b>\n\n"
            
            for i, product in enumerate(products, 1):
                message += (
                    f"{i}. {product.title}\n"
                    f"   💵 Цена: {product.price}₽\n"
                    f"   💲 Рынок: {product.market_price}₽\n"
                    f"   🎉 Скидка: <b>{product.discount_percent}%</b>\n"
                    f"   🔗 <a href='{product.url}'>Открыть</a>\n\n"
                )
        
        self.send_message(message, reply_markup=KeyboardBuilder.back_button())
    
    # ===== НАСТРОЙКИ =====
    
    def show_settings(self):
        """Показать меню настроек"""
        min_discount = user_settings.get_min_discount()
        max_price = user_settings.get_max_price()
        min_rating = user_settings.get_min_rating()
        scan_interval = user_settings.get_scan_interval()
        products_count = len(user_settings.get_tracked_products())
        blacklist_count = len(user_settings.get_blacklist())
        
        message = (
            f"⚙️ <b>НАСТРОЙКИ</b>\n\n"
            f"📝 Отслеживаемые товары: <b>{products_count}</b>\n"
            f"💰 Минимальная скидка: <b>{min_discount}%</b>\n"
            f"💵 Макс цена: <b>{max_price}₽</b>\n"
            f"⭐ Минимальный рейтинг: <b>{min_rating}</b>\n"
            f"🚫 В чёрном списке: <b>{blacklist_count}</b> продавцов\n"
            f"⏱️ Интервал сканирования: <b>{scan_interval} часов</b>\n\n"
            f"Выбери что изменить:"
        )
        self.send_message(message, reply_markup=KeyboardBuilder.settings_menu())
    
    def show_products_selection(self):
        """Показать меню выбора товаров"""
        products = user_settings.get_tracked_products()
        
        message = (
            f"📦 <b>ВЫБОР ТОВАРОВ</b>\n\n"
            f"Сейчас отслеживаем:\n"
        )
        
        for product in products:
            message += f"  ✅ {product}\n"
        
        message += f"\n📊 Всего: {len(products)} товаров\n\n"
        message += "Выбери товар или добавь свой:"
        
        self.send_message(message, reply_markup=KeyboardBuilder.products_selection())
    
    def show_my_products(self):
        """Показать мои товары"""
        products = user_settings.get_tracked_products()
        
        if not products:
            message = "❌ Ты не отслеживаешь никакие товары\n\nДобавь первый товар!"
        else:
            message = "📦 <b>МОИ ТОВАРЫ</b>\n\n"
            
            for i, product in enumerate(products, 1):
                message += f"{i}. {product}\n"
            
            message += f"\n📊 Всего: {len(products)} товаров"
        
        self.send_message(message, reply_markup=KeyboardBuilder.back_button())
    
    def show_help(self):
        """Справка"""
        message = (
            f"<b>📖 СПРАВКА</b>\n\n"
            f"<b>🎮 КНОПКИ МЕНЮ:</b>\n"
            f"  📊 Статистика - показывает цифры\n"
            f"  🔥 Топ скидок - лучшие предложения\n"
            f"  📦 Последние - новые товары\n"
            f"  ⚙️ Настройки - управление\n\n"
            f"<b>⚙️ НАСТРОЙКИ:</b>\n"
            f"  📝 Товары - какие отслеживать\n"
            f"  💰 Скидка - минимальная скидка\n"
            f"  💵 Цена - максимальная цена\n"
            f"  ⭐ Рейтинг - минимум рейтинг\n"
            f"  🚫 Чёрный список - плохие продавцы\n"
            f"  ⏱️ Интервал - как часто сканировать\n\n"
            f"<b>💡 СОВЕТЫ:</b>\n"
            f"  • Добавь товары в настройках\n"
            f"  • Установи минимальную скидку\n"
            f"  • Добавь плохих продавцов в список\n"
            f"  • Включи уведомления в Telegram\n\n"
            f"❓ Вопросы? Напиши /help"
        )
        self.send_message(message, reply_markup=KeyboardBuilder.back_button())
    
    # ===== ИЗМЕНЕНИЕ НАСТРОЕК =====
    
    def add_product_template(self, product_name):
        """Добавить товар"""
        if user_settings.add_tracked_product(product_name):
            message = f"✅ <b>{product_name}</b> добавлен в отслеживание!"
        else:
            message = f"⚠️ <b>{product_name}</b> уже отслеживается!"
        
        self.send_message(message, reply_markup=KeyboardBuilder.products_selection())
    
    def request_custom_product(self):
        """Запросить пользовательский товар"""
        message = (
            f"✍️ <b>ДОБАВИТЬ ТОВАР</b>\n\n"
            f"Напиши название товара которое нужно отслеживать:\n\n"
            f"Например: MacBook Air, Samsung Galaxy S24"
        )
        self.user_state['waiting_for'] = 'custom_product'
        self.send_message(message, reply_markup=KeyboardBuilder.back_button())
    
    def request_min_discount(self):
        """Запросить минимальную скидку"""
        current = user_settings.get_min_discount()
        message = (
            f"💰 <b>МИНИМАЛЬНАЯ СКИДКА</b>\n\n"
            f"Текущее значение: <b>{current}%</b>\n\n"
            f"Введи новое значение (0-100):"
        )
        self.user_state['waiting_for'] = 'min_discount'
        self.send_message(message, reply_markup=KeyboardBuilder.back_button())
    
    def request_max_price(self):
        """Запросить максимальную цену"""
        current = user_settings.get_max_price()
        message = (
            f"💵 <b>МАКСИМАЛЬНАЯ ЦЕНА</b>\n\n"
            f"Текущее значение: <b>{current}₽</b>\n\n"
            f"Введи новое значение (в рублях):"
        )
        self.user_state['waiting_for'] = 'max_price'
        self.send_message(message, reply_markup=KeyboardBuilder.back_button())
    
    def request_min_rating(self):
        """Запросить минимальный рейтинг"""
        current = user_settings.get_min_rating()
        message = (
            f"⭐ <b>МИНИМАЛЬНЫЙ РЕЙТИНГ</b>\n\n"
            f"Текущее значение: <b>{current}</b>\n\n"
            f"Введи новое значение (0-5):"
        )
        self.user_state['waiting_for'] = 'min_rating'
        self.send_message(message, reply_markup=KeyboardBuilder.back_button())
    
    def request_scan_interval(self):
        """Запросить интервал сканирования"""
        current = user_settings.get_scan_interval()
        message = (
            f"⏱️ <b>ИНТЕРВАЛ СКАНИРОВАНИЯ</b>\n\n"
            f"Текущее значение: <b>{current} часов</b>\n\n"
            f"Введи новое значение (в часах):"
        )
        self.user_state['waiting_for'] = 'scan_interval'
        self.send_message(message, reply_markup=KeyboardBuilder.back_button())
    
    def process_user_input(self, text):
        """Обработать ввод пользователя"""
        waiting_for = self.user_state.get('waiting_for')
        
        if waiting_for == 'custom_product':
            self.add_product_template(text)
            self.user_state.pop('waiting_for', None)
        
        elif waiting_for == 'min_discount':
            if user_settings.set_min_discount(text):
                message = f"✅ Минимальная скидка установлена: {text}%"
            else:
                message = f"❌ Ошибка! Введи число от 0 до 100"
            self.send_message(message, reply_markup=KeyboardBuilder.settings_menu())
            self.user_state.pop('waiting_for', None)
        
        elif waiting_for == 'max_price':
            if user_settings.set_max_price(text):
                message = f"✅ Максимальная цена установлена: {text}₽"
            else:
                message = f"❌ Ошибка! Введи положительное число"
            self.send_message(message, reply_markup=KeyboardBuilder.settings_menu())
            self.user_state.pop('waiting_for', None)
        
        elif waiting_for == 'min_rating':
            if user_settings.set_min_rating(text):
                message = f"✅ Минимальный рейтинг установлен: {text}"
            else:
                message = f"❌ Ошибка! Введи число от 0 до 5"
            self.send_message(message, reply_markup=KeyboardBuilder.settings_menu())
            self.user_state.pop('waiting_for', None)
        
        elif waiting_for == 'scan_interval':
            if user_settings.set_scan_interval(text):
                message = f"✅ Интервал сканирования установлен: {text} часов"
            else:
                message = f"❌ Ошибка! Введи положительное число"
            self.send_message(message, reply_markup=KeyboardBuilder.settings_menu())
            self.user_state.pop('waiting_for', None)
    
    def handle_callback(self, callback_data):
        """Обработать нажатие кнопки"""
        logger.info(f"🔘 Callback: {callback_data}")
        
        handlers = {
            'main_menu': self.show_main_menu,
            'stats': self.send_statistics,
            'recent': self.send_recent_products,
            'best': self.send_best_deals,
            'settings': self.show_settings,
            'help': self.show_help,
            'select_products': self.show_products_selection,
            'my_products': self.show_my_products,
            'add_product_smartphones': lambda: self.add_product_template('iPhone'),
            'add_product_watches': lambda: self.add_product_template('Apple Watch'),
            'add_product_laptops': lambda: self.add_product_template('MacBook'),
            'add_product_headphones': lambda: self.add_product_template('AirPods'),
            'add_product_cameras': lambda: self.add_product_template('Canon'),
            'add_product_consoles': lambda: self.add_product_template('PlayStation'),
            'custom_product': self.request_custom_product,
            'min_discount': self.request_min_discount,
            'max_price': self.request_max_price,
            'min_rating': self.request_min_rating,
            'scan_interval': self.request_scan_interval,
        }
        
        handler = handlers.get(callback_data)
        if handler:
            try:
                handler()
            except Exception as e:
                logger.error(f"❌ Ошибка обработки: {e}")
                self.send_message(f"❌ Ошибка: {e}", reply_markup=KeyboardBuilder.main_menu())