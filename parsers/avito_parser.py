import logging
import requests
import time
import sys
import os
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from datetime import datetime

# Добавляем путь проекта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import REQUEST_DELAY
from models import get_session, Product

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AvitoParser:
    """Парсер Avito"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.base_url = "https://www.avito.ru"
        self.session = requests.Session()
    
    def _get_headers(self):
        """Получить заголовки запроса"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    def search_products(self, query, max_price=None, min_price=None, limit=50):
        """Поиск товаров на Avito"""
        logger.info(f"🔍 Поиск: {query}")
        
        products = []
        
        try:
            # Формируем URL поиска
            search_url = f"{self.base_url}/s"
            params = {
                'q': query,
                'p': 1,
            }
            
            if max_price:
                params['pmax'] = max_price
            if min_price:
                params['pmin'] = min_price
            
            # Задержка перед запросом
            time.sleep(REQUEST_DELAY)
            
            # Делаем запрос
            response = self.session.get(
                search_url,
                params=params,
                headers=self._get_headers(),
                timeout=10
            )
            
            response.raise_for_status()
            
            # Парсим HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Ищем товары
            items = soup.find_all('div', {'data-item-id': True})
            
            logger.info(f"✅ Найдено товаров на странице: {len(items)}")
            
            for item in items[:limit]:
                try:
                    product = self._parse_item(item)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка парсинга товара: {e}")
                    continue
            
            return products
        
        except Exception as e:
            logger.error(f"❌ Ошибка поиска: {e}")
            return []
    
    def _parse_item(self, item):
        """Парсить товар из элемента"""
        try:
            # ID товара
            item_id = item.get('data-item-id')
            if not item_id:
                return None
            
            # Название
            title_elem = item.find('h3', class_='title')
            title = title_elem.get_text(strip=True) if title_elem else "Unknown"
            
            # Цена
            price_elem = item.find('span', class_='price')
            price_text = price_elem.get_text(strip=True) if price_elem else "0"
            price = self._parse_price(price_text)
            
            # URL товара
            link_elem = item.find('a', class_='title-link')
            url = link_elem['href'] if link_elem else ""
            if not url.startswith('http'):
                url = self.base_url + url
            
            # Информация о продавце
            seller_elem = item.find('p', class_='seller-info')
            seller_name = seller_elem.get_text(strip=True) if seller_elem else "Unknown"
            
            # Локация
            location_elem = item.find('span', class_='geo')
            location = location_elem.get_text(strip=True) if location_elem else "Unknown"
            
            # Рейтинг продавца
            rating_elem = item.find('span', class_='rating')
            seller_rating = float(rating_elem.get_text()) if rating_elem else 0.0
            
            product = {
                'avito_id': item_id,
                'title': title,
                'price': price,
                'url': url,
                'seller_name': seller_name,
                'seller_rating': seller_rating,
                'location': location,
                'category': 'electronics',
                'market_price': price * 1.2,  # Примерная рыночная цена
                'discount_percent': 0,
            }
            
            return product
        
        except Exception as e:
            logger.warning(f"⚠️ Ошибка парсинга: {e}")
            return None
    
    def _parse_price(self, price_text):
        """Распарсить цену из текста"""
        try:
            # Удаляем все нецифровые символы кроме точки
            price_str = ''.join(c for c in price_text if c.isdigit() or c == '.')
            return float(price_str) if price_str else 0.0
        except Exception as e:
            logger.warning(f"⚠️ Ошибка парсинга цены: {e}")
            return 0.0
