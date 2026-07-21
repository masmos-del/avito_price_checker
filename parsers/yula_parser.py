import logging
import requests
import time
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from datetime import datetime
from config import REQUEST_DELAY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class YulaParser:
    """Парсер Юла"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.base_url = "https://yula.kz"  # или https://yula.ua
        self.session = requests.Session()
    
    def _get_headers(self):
        """Получить заголовки запроса"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
    
    def search_products(self, query, max_price=None, min_price=None, limit=50):
        """Поиск товаров на Юла"""
        logger.info(f"🔍 Юла поиск: {query}")
        
        products = []
        
        try:
            search_url = f"{self.base_url}/search"
            
            params = {
                'q': query,
            }
            
            if max_price:
                params['price_to'] = max_price
            if min_price:
                params['price_from'] = min_price
            
            time.sleep(REQUEST_DELAY)
            
            response = self.session.get(
                search_url,
                params=params,
                headers=self._get_headers(),
                timeout=10
            )
            
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Ищем карточки объявлений
            items = soup.find_all('div', class_='product-item')
            
            logger.info(f"✅ Найдено товаров на Юла: {len(items)}")
            
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
            logger.error(f"❌ Ошибка поиска Юла: {e}")
            return []
    
    def _parse_item(self, item):
        """Парсить товар из элемента Юла"""
        try:
            # Ссылка и ID
            link_elem = item.find('a', class_='product-link')
            if not link_elem:
                return None
            
            url = link_elem.get('href', '')
            item_id = url.split('/')[-1] if url else None
            
            # Название
            title_elem = item.find('h2', class_='product-title')
            title = title_elem.get_text(strip=True) if title_elem else "Unknown"
            
            # Цена
            price_elem = item.find('span', class_='product-price')
            price_text = price_elem.get_text(strip=True) if price_elem else "0"
            price = self._parse_price(price_text)
            
            # Локация
            location_elem = item.find('span', class_='product-location')
            location = location_elem.get_text(strip=True) if location_elem else "Unknown"
            
            product = {
                'avito_id': item_id,
                'title': title,
                'price': price,
                'url': url if url.startswith('http') else f"{self.base_url}{url}",
                'seller_name': 'Юла',
                'seller_rating': 0.0,
                'location': location,
                'category': 'general',
                'market_price': price * 1.15,
                'discount_percent': 0,
            }
            
            return product
        
        except Exception as e:
            logger.debug(f"⚠️ Ошибка парсинга Юла: {e}")
            return None
    
    def _parse_price(self, price_text):
        """Распарсить цену"""
        try:
            price_str = ''.join(c for c in price_text if c.isdigit())
            return float(price_str) if price_str else 0.0
        except:
            return 0.0