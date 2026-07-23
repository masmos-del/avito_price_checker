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


class AutoRuParser:
    """Парсер Авто.ру"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.base_url = "https://auto.ru"
        self.session = requests.Session()
    
    def _get_headers(self):
        """Получить заголовки запроса"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
    
    def search_products(self, query, max_price=None, min_price=None, limit=50):
        """Поиск автомобилей на Авто.ру"""
        logger.info(f"🚗 Авто.ру поиск: {query}")
        
        products = []
        
        try:
            search_url = f"{self.base_url}/cars/all/"
            
            params = {
                'search_tag': query,
                'body_type_group': 'SEDAN',
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
            
            items = soup.find_all('div', {'data-auto-test-id': 'listingLot'})
            
            logger.info(f"✅ Найдено авто на Авто.ру: {len(items)}")
            
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
            logger.error(f"❌ Ошибка поиска Авто.ру: {e}")
            return []
    
    def _parse_item(self, item):
        """Парсить автомобиль из элемента"""
        try:
            link_elem = item.find('a', class_='ListingItemContent__link')
            if not link_elem:
                return None
            
            url = link_elem.get('href', '')
            item_id = url.split('/')[-1] if url else None
            
            title_elem = item.find('h2', class_='ListingItemTitle__title')
            title = title_elem.get_text(strip=True) if title_elem else "Unknown"
            
            price_elem = item.find('span', class_='ListingPriceInfo__price')
            price_text = price_elem.get_text(strip=True) if price_elem else "0"
            price = self._parse_price(price_text)
            
            specs = item.find_all('li', class_='ListingItemCharacteristics__item')
            specs_text = ', '.join([s.get_text(strip=True) for s in specs[:3]])
            
            product = {
                'avito_id': item_id,
                'title': f"{title} - {specs_text}",
                'price': price,
                'url': url if url.startswith('http') else f"{self.base_url}{url}",
                'seller_name': 'Авто.ру',
                'seller_rating': 0.0,
                'location': 'Unknown',
                'category': 'cars',
                'market_price': price * 1.1,
                'discount_percent': 0,
            }
            
            return product
        
        except Exception as e:
            logger.debug(f"⚠️ Ошибка парсинга Авто.ру: {e}")
            return None
    
    def _parse_price(self, price_text):
        """Распарсить цену"""
        try:
            price_str = ''.join(c for c in price_text if c.isdigit())
            return float(price_str) if price_str else 0.0
        except:
            return 0.0
