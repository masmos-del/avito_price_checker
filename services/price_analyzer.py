import logging
from config import MARKET_PRICES, MIN_DISCOUNT_PERCENT, BLACKLIST_SELLERS, MIN_SELLER_RATING

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PriceAnalyzer:
    """Анализ цен и поиск выгодных предложений"""
    
    def __init__(self):
        self.min_discount = MIN_DISCOUNT_PERCENT
        self.market_prices = MARKET_PRICES
        self.blacklist = BLACKLIST_SELLERS
        self.min_rating = MIN_SELLER_RATING
    
    def analyze_products(self, products):
        """Анализировать товары и найти скидки"""
        profitable_products = []
        
        for product in products:
            # 🆕 Проверяем продавца
            if not self._is_seller_trusted(product):
                logger.warning(f"⛔ Продавец в чёрном списке: {product.get('seller_name')}")
                continue
            
            analyzed = self._analyze_product(product)
            if analyzed:
                profitable_products.append(analyzed)
        
        logger.info(f"📊 Проанализировано: {len(products)}, выгодных: {len(profitable_products)}")
        return profitable_products
    
    def _is_seller_trusted(self, product):
        """Проверить, доверяемый ли продавец"""
        seller_name = product.get('seller_name', '').lower()
        
        # Проверка чёрного списка
        for blacklisted in self.blacklist:
            if blacklisted.lower() in seller_name:
                return False
        
        # Проверка рейтинга (если доступен)
        rating = product.get('seller_rating', 5.0)
        if rating and rating < self.min_rating:
            logger.warning(f"⭐ Низкий рейтинг {rating}: {seller_name}")
            return False
        
        return True
    
    def _analyze_product(self, product):
        """Анализировать один товар"""
        try:
            title = product['title'].lower()
            price = product['price']
            
            # Ищем рыночную цену по названию
            market_price = None
            for key, value in self.market_prices.items():
                if key.lower() in title:
                    market_price = value
                    break
            
            if not market_price:
                return None
            
            # Считаем скидку
            discount = ((market_price - price) / market_price) * 100
            
            # Если скидка достаточно большая
            if discount >= self.min_discount:
                product['market_price'] = market_price
                product['discount_percent'] = round(discount, 1)
                product['is_profitable'] = True
                
                logger.info(f"💰 ВЫГОДНО! {product['title']}: {price}₽ (скидка {discount:.1f}%)")
                return product
        
        except Exception as e:
            logger.warning(f"⚠️ Ошибка анализа: {e}")
        
        return None