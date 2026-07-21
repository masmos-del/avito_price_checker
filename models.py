from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import DATABASE_URL

Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)


class Product(Base):
    """Модель товара"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    avito_id = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    market_price = Column(Float, nullable=True)
    discount_percent = Column(Float, nullable=True)
    url = Column(String, nullable=False, unique=True)
    seller_name = Column(String, nullable=True)
    seller_rating = Column(Float, nullable=True)
    location = Column(String, nullable=True)
    is_profitable = Column(Boolean, default=False)
    is_sent_to_telegram = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Product {self.title} - {self.price}₽>"


class PriceHistory(Base):
    """История изменения цен"""
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, nullable=False, index=True)
    price = Column(Float, nullable=False)
    discount_percent = Column(Float, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<PriceHistory product_id={self.product_id} price={self.price}>"


def init_db():
    """Инициализировать базу данных"""
    Base.metadata.create_all(engine)
    print("✓ База данных инициализирована")


def get_session():
    """Получить сессию БД"""
    return Session()


def is_product_already_sent(url):
    """Проверить, отправляли ли уже этот товар"""
    session = get_session()
    product = session.query(Product).filter_by(url=url, is_sent_to_telegram=True).first()
    session.close()
    return product is not None


def mark_product_as_sent(url):
    """Пометить товар как отправленный"""
    session = get_session()
    product = session.query(Product).filter_by(url=url).first()
    if product:
        product.is_sent_to_telegram = True
        product.sent_at = datetime.utcnow()
        session.commit()
    session.close()


def get_statistics():
    """Получить статистику по товарам"""
    session = get_session()
    
    try:
        total_products = session.query(Product).count()
        profitable_products = session.query(Product).filter_by(is_profitable=True).count()
        sent_products = session.query(Product).filter_by(is_sent_to_telegram=True).count()
        
        avg_discount = session.query(func.avg(Product.discount_percent)).filter(
            Product.is_profitable == True
        ).scalar()
        
        max_discount = session.query(func.max(Product.discount_percent)).scalar()
        
        stats = {
            'total_products': total_products,
            'profitable_products': profitable_products,
            'sent_products': sent_products,
            'avg_discount': round(avg_discount or 0, 1),
            'max_discount': round(max_discount or 0, 1),
        }
        
        return stats
    except Exception as e:
        print(f"❌ Ошибка получения статистики: {e}")
        return {
            'total_products': 0,
            'profitable_products': 0,
            'sent_products': 0,
            'avg_discount': 0,
            'max_discount': 0,
        }
    finally:
        session.close()


def get_recent_products(limit=5):
    """Получить последние товары"""
    session = get_session()
    try:
        products = session.query(Product).order_by(
            Product.created_at.desc()
        ).limit(limit).all()
        return products
    finally:
        session.close()


def get_best_deals(limit=5):
    """Получить топ скидок"""
    session = get_session()
    try:
        products = session.query(Product).filter_by(
            is_profitable=True
        ).order_by(
            Product.discount_percent.desc()
        ).limit(limit).all()
        return products
    finally:
        session.close()