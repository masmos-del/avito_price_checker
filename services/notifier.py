import requests
import logging
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from models import get_session, Product, mark_product_as_sent, is_product_already_sent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Notifier:
    """Система уведомлений в Telegram"""
    
    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.api_url = f"https://api.telegram.org/bot{self.token}"
    
    def send_products_to_telegram(self, products):
        """Отправить товары в Telegram"""
        if not self.token or not self.chat_id:
            logger.warning("⚠️ TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID не установлены!")
            return False
        
        if not products:
            logger.info("📭 Нет товаров для отправки")
            return True
        
        # Фильтруем товары: отправляем только новые
        new_products = self._filter_new_products(products)
        
        if not new_products:
            logger.info("✅ Все товары уже отправлены")
            return True
        
        logger.info(f"📤 Отправка {len(new_products)} НОВЫХ товаров в Telegram...")
        
        sent_count = 0
        for product in new_products:
            try:
                message = self._format_product_message(product)
                if self._send_message(message):
                    # Помечаем товар как отправленный
                    self._save_product_to_db(product)
                    sent_count += 1
            except Exception as e:
                logger.error(f"❌ Ошибка отправки: {e}")
        
        logger.info(f"✅ Отправлено товаров: {sent_count}")
        return True
    
    def _filter_new_products(self, products):
        """Фильтровать только новые товары (не отправленные раньше)"""
        new_products = []
        for product in products:
            if not is_product_already_sent(product['url']):
                new_products.append(product)
            else:
                logger.info(f"⏭️  Уже отправлен: {product['title']}")
        
        return new_products
    
    def _save_product_to_db(self, product):
        """Сохранить товар в БД"""
        try:
            session = get_session()
            
            # Проверяем, есть ли уже в БД
            existing = session.query(Product).filter_by(url=product['url']).first()
            
            if existing:
                existing.is_sent_to_telegram = True
                existing.sent_at = datetime.utcnow()
                logger.info(f"✏️  Обновлён товар в БД: {product['title']}")
            else:
                # Создаём новый товар
                prod = Product(
                    avito_id=product['url'],
                    title=product['title'],
                    category='electronics',
                    price=product['price'],
                    market_price=product.get('market_price'),
                    discount_percent=product.get('discount_percent'),
                    url=product['url'],
                    seller_name=product.get('seller_name', 'Неизвестно'),
                    location=product.get('location', 'Неизвестно'),
                    is_profitable=True,
                    is_sent_to_telegram=True,
                    sent_at=datetime.utcnow(),
                )
                session.add(prod)
                logger.info(f"✨ Добавлен новый товар в БД: {product['title']}")
            
            session.commit()
            session.close()
            logger.info(f"💾 Товар сохранён в БД: {product['title']}")
        
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения в БД: {e}")
    
    def _format_product_message(self, product):
        """Форматировать сообщение о товаре"""
        title = product['title']
        price = product['price']
        market_price = product.get('market_price', 'N/A')
        discount = product.get('discount_percent', 0)
        url = product['url']
        location = product.get('location', 'Неизвестно')
        seller = product.get('seller_name', 'Частное лицо')
        
        message = (
            f"💰 <b>ВЫГОДНОЕ ПРЕДЛОЖЕНИЕ!</b>\n\n"
            f"📦 <b>{title}</b>\n\n"
            f"💵 Цена на Авито: <b>{price}₽</b>\n"
            f"💲 Средняя цена рынка: {market_price}₽\n"
            f"🎉 Скидка: <b>{discount}%</b>\n\n"
            f"📍 Локация: {location}\n"
            f"👤 Продавец: {seller}\n\n"
            f"🔗 <a href='{url}'>Перейти к товару</a>"
        )
        
        return message
    
    def _send_message(self, message):
        """Отправить сообщение в Telegram"""
        data = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': False,
        }
        
        response = requests.post(
            f"{self.api_url}/sendMessage",
            data=data,
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info("✅ Сообщение отправлено в Telegram")
            return True
        else:
            logger.error(f"❌ Ошибка Telegram: {response.text}")
            return False