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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OLXParser:
    """Парсер OLX.ua / OLX.ru"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.base_url = "https://www.olx.ua"
        self.session = requests.Session()
    
    def _get_headers(self):
        """Получить заголовки запроса"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'uk-UA,uk;q=0.9',
        }
    
    def search_products(self, query, max_price=None, min_price=None, limit=50):
        """Поиск товаров на OLX"""
        logger.info(f"🔍 OLX поиск: {query}")
        
        products = []
        
        try:
            search_url = f"{self.base_url}/uk/q-{query}/"
            params = {}
            
            if max_price:
                params['pmax'] = max_price
            if min_price:
                params['pmin'] = min_price
            
            time.sleep(REQUEST_DELAY)
            
            response = self.session.get(
                search_url,
                params=params,
                headers=self._get_headers(),
                timeout=10
            )
            
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            items = soup.find_all('div', {'data-cy': 'l-card'})
            
            logger.info(f"✅ Найдено товаров на OLX: {len(items)}")
            
            for item in items[:limit]:
                try:
                    product = self._parse_item(item)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.debug(f"⚠️ Ошибка парсинга: {e}")
                    continue
            
            return products
        
        except Exception as e:
            logger.error(f"❌ Ошибка поиска OLX: {e}")
            return []
    
    def _parse_item(self, item):
        """Парсить товар из элемента OLX"""
        try:
            link_elem = item.find('a', class_='css-1bbgabe')
            if not link_elem:
                return None
            
            url = link_elem.get('href', '')
            item_id = url.split('/')[-1] if url else None
            
            if not item_id:
                return None
            
            title_elem = item.find('h6', class_='css-16v5mdc')
            title = title_elem.get_text(strip=True) if title_elem else "Unknown"
            
            price_elem = item.find('p', class_='css-90xrc0')
            price_text = price_elem.get_text(strip=True) if price_elem else "0"
            price = self._parse_price(price_text)
            
            location_elem = item.find('p', class_='css-p0voq7')
            location = location_elem.get_text(strip=True) if location_elem else "Unknown"
            
            product = {
                'avito_id': item_id,
                'title': title,
                'price': price,
                'url': url if url.startswith('http') else f"{self.base_url}{url}",
                'seller_name': 'OLX Seller',
                'seller_rating': 0.0,
                'location': location,
                'category': 'general',
                'market_price': price * 1.15,
                'discount_percent': 0,
            }
            
            return product
        
        except Exception as e:
            logger.debug(f"⚠️ Ошибка парсинга OLX: {e}")
            return None
    
    def _parse_price(self, price_text):
        """Распарсить цену"""
        try:
            price_str = ''.join(c for c in price_text if c.isdigit() or c == '.')
            return float(price_str) if price_str else 0.0
        except:
            return 0.0
