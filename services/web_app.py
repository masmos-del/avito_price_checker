"""
🌍 Web приложение с поддержкой множественных парсеров
Поддерживает: Avito, OLX, Авто.ру, Юла
"""

from flask import Flask, render_template, jsonify, request
from functools import wraps
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ===== ИСПРАВЛЕНИЕ ПУТЕЙ =====
# Получаем корневую директорию проекта (родитель папки services)
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

# ===== КОНФИГУРАЦИЯ =====
load_dotenv()

PARSERS_CONFIG = {
    'avito': {
        'name': '🔵 Avito',
        'url': 'https://avito.ru',
        'description': 'Крупнейшая доска объявлений России',
        'icon': '🔵',
        'categories': ['electronics', 'cars', 'property', 'general'],
        'delay': 2,
    },
    'olx': {
        'name': '🟠 OLX',
        'url': 'https://olx.ua',
        'description': 'Популярная площадка в Восточной Европе',
        'icon': '🟠',
        'categories': ['general', 'electronics', 'property'],
        'delay': 2,
    },
    'auto_ru': {
        'name': '🚗 Авто.ру',
        'url': 'https://auto.ru',
        'description': 'Крупнейший сайт продажи автомобилей',
        'icon': '🚗',
        'categories': ['cars'],
        'delay': 2,
    },
    'yula': {
        'name': '🟡 Юла',
        'url': 'https://yula.kz',
        'description': 'Доска объявлений Казахстана и Украины',
        'icon': '🟡',
        'categories': ['general', 'electronics'],
        'delay': 2,
    },
}

# ===== ЛОГИРОВАНИЕ =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===== ИНИЦИАЛИЗАЦИЯ FLASK =====
app = Flask(
    __name__, 
    template_folder=os.path.join(os.path.dirname(__file__), "templates")
)
app.config['JSON_SORT_KEYS'] = False

# ===== ПАРСЕРЫ =====
parsers: Dict = {}
article_broker = None
product_broker = None


def initialize_app():
    """Инициализация приложения: парсеры, брокеры, блюпринты"""
    global article_broker, product_broker, parsers
    
    logger.info(f"📁 PROJECT_ROOT: {PROJECT_ROOT}")
    logger.info(f"📁 sys.path[0]: {sys.path[0]}")
    
    # Инициализация парсеров
    try:
        from parsers import AvitoParser, OLXParser, AutoRuParser, YulaParser
        
        parsers = {
            'avito': AvitoParser(),
            'olx': OLXParser(),
            'auto_ru': AutoRuParser(),
            'yula': YulaParser(),
        }
        logger.info(f"✅ Парсеры инициализированы: {list(parsers.keys())}")
    except ImportError as e:
        logger.warning(f"⚠️ Не удалось загрузить парсеры: {e}")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации парсеров: {e}", exc_info=True)
    
    # Инициализация Redis брокеров (опционально)
    try:
        from messaging.redis_broker import RedisBroker
        article_broker = RedisBroker(stream="article_jobs")
        product_broker = RedisBroker(stream="product_jobs")
        logger.info("✅ Redis брокеры инициализированы")
    except ImportError:
        logger.warning("⚠️ Модуль messaging недоступен - Redis функции отключены")
    except Exception as e:
        logger.warning(f"⚠️ Ошибка инициализации Redis: {e}")
    
    # Регистрация блюпринтов (опционально - если они существуют)
    try:
        from services.blueprints.article import article_bp
        from services.blueprints.product import product_bp
        
        app.register_blueprint(article_bp, url_prefix="/articles")
        app.register_blueprint(product_bp, url_prefix="/products")
        logger.info("✅ Блюпринты зарегистрированы")
    except ImportError as e:
        logger.debug(f"ℹ️ Блюпринты не загружены (это нормально): {e}")


# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

def require_json(f):
    """Декоратор для проверки Content-Type"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({
                "status": "error",
                "message": "Content-Type must be application/json"
            }), 400
        return f(*args, **kwargs)
    return decorated_function


def require_redis(f):
    """Декоратор для проверки Redis доступности"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if article_broker is None or product_broker is None:
            return jsonify({
                "status": "error",
                "message": "Redis not available"
            }), 503
        return f(*args, **kwargs)
    return decorated_function


def validate_parser(parser_name: str) -> Tuple[bool, Optional[str]]:
    """Валидация имени парсера. Возвращает (valid, error_message)"""
    if not parser_name or parser_name not in parsers:
        available = list(parsers.keys()) if parsers else "none"
        return False, f"Parser '{parser_name}' not found. Available: {available}"
    return True, None


def safe_parser_call(parser_name: str, query: str, min_price=None, max_price=None, limit: int = 50):
    """Безопасный вызов парсера с обработкой ошибок"""
    try:
        if parser_name not in parsers:
            return {"status": "error", "error": f"Parser {parser_name} not available", "products": [], "count": 0}
        
        parser = parsers[parser_name]
        products = parser.search_products(
            query=query,
            min_price=min_price,
            max_price=max_price,
            limit=limit
        )
        return {"status": "success", "products": products, "count": len(products)}
    except Exception as e:
        logger.error(f"❌ Ошибка парсера {parser_name}: {e}", exc_info=True)
        return {"status": "error", "error": str(e), "products": [], "count": 0}


# ===== API: ГЛАВНЫЕ МАРШРУТЫ =====

@app.route("/")
def dashboard():
    """🏠 Главная страница дашборда"""
    logger.info("📍 Запрос главной страницы")
    try:
        return render_template("dashboard_advanced.html")
    except Exception as e:
        logger.warning(f"⚠️ Template не найден: {e}")
        return (
            "<h1>Dashboard</h1>"
            "<p>Парсеры работают, но шаблон dashboard_advanced.html не найден</p>"
        ), 200


@app.route("/health")
def health_check():
    """🏥 Проверка здоровья приложения"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "parsers": list(parsers.keys()),
        "redis_available": article_broker is not None,
    }), 200


# ===== API: ИНФОРМАЦИЯ О ПАРСЕРАХ =====

@app.route("/api/parsers", methods=["GET"])
def get_parsers():
    """📋 API: Получить список всех доступных парсеров"""
    logger.info("📍 Запрос списка парсеров")
    
    parsers_info = {
        name: {
            **config,
            'enabled': name in parsers,
        }
        for name, config in PARSERS_CONFIG.items()
    }
    
    return jsonify({
        "status": "success",
        "count": len([p for p in parsers_info.values() if p['enabled']]),
        "parsers": parsers_info,
    }), 200


@app.route("/api/parser/<parser_name>", methods=["GET"])
def get_parser_info(parser_name):
    """📖 API: Получить информацию о конкретном парсере"""
    logger.info(f"📍 Запрос информации о парсере: {parser_name}")
    
    valid, error = validate_parser(parser_name)
    if not valid:
        logger.warning(f"⚠️ {error}")
        return jsonify({"status": "error", "message": error}), 404
    
    config = PARSERS_CONFIG.get(parser_name, {})
    return jsonify({
        "status": "success",
        "parser": config
    }), 200


# ===== API: ПОИСК ПО ПАРСЕРАМ =====

@app.route("/api/search", methods=["POST"])
@require_json
def search_products():
    """🔍 API: Поиск товаров по запросу"""
    data = request.get_json()
    
    query = data.get("query", "").strip()
    parser_name = data.get("parser", "avito")
    limit = min(data.get("limit", 50), 200)  # Ограничение для безопасности
    min_price = data.get("min_price")
    max_price = data.get("max_price")
    
    logger.info(f"🔍 Поиск: '{query}' на {parser_name}")
    
    if not query:
        return jsonify({
            "status": "error",
            "message": "Query parameter is required"
        }), 400
    
    valid, error = validate_parser(parser_name)
    if not valid:
        return jsonify({"status": "error", "message": error}), 404
    
    result = safe_parser_call(parser_name, query, min_price, max_price, limit)
    status_code = 200 if result["status"] == "success" else 500
    
    return jsonify({
        "status": result["status"],
        "parser": parser_name,
        "query": query,
        "count": result["count"],
        "products": result["products"],
        **({"error": result.get("error")} if result["status"] == "error" else {})
    }), status_code


@app.route("/api/search/multi", methods=["POST"])
@require_json
def search_multi_parsers():
    """🌐 API: Поиск одновременно по нескольким парсерам"""
    data = request.get_json()
    
    query = data.get("query", "").strip()
    parser_list = data.get("parsers", list(parsers.keys()))
    limit = min(data.get("limit", 30), 200)
    min_price = data.get("min_price")
    max_price = data.get("max_price")
    
    logger.info(f"🌐 Мультипоиск: '{query}' по {len(parser_list)} парсерам")
    
    if not query:
        return jsonify({
            "status": "error",
            "message": "Query parameter is required"
        }), 400
    
    all_results = {}
    total_products = 0
    
    for parser_name in parser_list:
        if parser_name not in parsers:
            logger.warning(f"⚠️ Парсер {parser_name} пропущен")
            all_results[parser_name] = {
                "count": 0,
                "products": [],
                "status": "not_available",
                "error": f"Parser '{parser_name}' not initialized"
            }
            continue
        
        result = safe_parser_call(parser_name, query, min_price, max_price, limit)
        all_results[parser_name] = result
        total_products += result["count"]
        
        logger.info(f"✅ {parser_name}: {result['count']} товаров")
    
    logger.info(f"📊 Итого найдено: {total_products} товаров")
    
    return jsonify({
        "status": "success",
        "query": query,
        "total_count": total_products,
        "results": all_results,
    }), 200


# ===== API: REDIS РАБОТЫ (LEGACY) =====

@app.route("/api/jobs/<job_type>", methods=["GET"])
@require_redis
def get_jobs(job_type):
    """📋 API: Получить список заданий"""
    
    if job_type not in ("article", "product"):
        return jsonify({
            "status": "error",
            "message": "Invalid job_type. Must be 'article' or 'product'"
        }), 400
    
    broker = article_broker if job_type == "article" else product_broker
    
    try:
        messages = broker.redis.xrevrange(broker.stream, count=20)
        jobs = [
            {
                "id": msg_id.decode() if isinstance(msg_id, bytes) else msg_id,
                "data": {
                    k.decode() if isinstance(k, bytes) else k: 
                    v.decode() if isinstance(v, bytes) else v 
                    for k, v in fields.items()
                }
            }
            for msg_id, fields in messages
        ]
        
        logger.info(f"📋 Получено {len(jobs)} заданий типа {job_type}")
        return jsonify({"status": "success", "jobs": jobs}), 200
    
    except Exception as e:
        logger.error(f"❌ Ошибка получения заданий: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/jobs/<job_type>/delete/<job_id>", methods=["POST"])
@require_redis
def delete_job(job_type, job_id):
    """🗑️ API: Удалить задание"""
    
    if job_type not in ("article", "product"):
        return jsonify({
            "status": "error",
            "message": "Invalid job_type. Must be 'article' or 'product'"
        }), 400
    
    broker = article_broker if job_type == "article" else product_broker
    
    try:
        broker.redis.xdel(broker.stream, job_id)
        logger.info(f"🗑️ Задание {job_id} удалено")
        return jsonify({"status": "deleted", "job_id": job_id}), 200
    
    except Exception as e:
        logger.error(f"❌ Ошибка удаления: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/jobs/<job_type>/requeue/<job_id>", methods=["POST"])
@require_redis
def requeue_job(job_type, job_id):
    """🔄 API: Переставить задание в очередь"""
    
    if job_type not in ("article", "product"):
        return jsonify({
            "status": "error",
            "message": "Invalid job_type. Must be 'article' or 'product'"
        }), 400
    
    broker = article_broker if job_type == "article" else product_broker
    
    try:
        msg = broker.redis.xrange(broker.stream, min=job_id, max=job_id)
        if not msg:
            return jsonify({"status": "not_found", "job_id": job_id}), 404
        
        _, fields = msg[0]
        broker.publish(fields)
        logger.info(f"🔄 Задание {job_id} переставлено в очередь")
        return jsonify({"status": "requeued", "job_id": job_id}), 200
    
    except Exception as e:
        logger.error(f"❌ Ошибка переставки: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


# ===== API: СТАТИСТИКА =====

@app.route("/api/stats", methods=["GET"])
def get_stats():
    """📊 API: Получить статистику"""
    logger.info("📊 Запрос статистики")
    
    stats = {
        "timestamp": datetime.now().isoformat(),
        "parsers_available": len(parsers),
        "parsers_list": list(parsers.keys()),
        "redis_available": article_broker is not None,
    }
    
    return jsonify({
        "status": "success",
        "stats": stats
    }), 200


# ===== ОБРАБОТКА ОШИБОК =====

@app.errorhandler(404)
def not_found(error):
    """404 ошибка"""
    logger.warning(f"404: {error}")
    return jsonify({
        "status": "error",
        "message": "Not found",
        "code": 404
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """500 ошибка"""
    logger.error(f"500: {error}", exc_info=True)
    return jsonify({
        "status": "error",
        "message": "Internal server error",
        "code": 500
    }), 500


@app.errorhandler(405)
def method_not_allowed(error):
    """405 ошибка"""
    logger.warning(f"405: {error}")
    return jsonify({
        "status": "error",
        "message": "Method not allowed",
        "code": 405
    }), 405


# ===== HOOKS =====

@app.before_request
def before_request():
    """Логирование перед запросом"""
    logger.debug(f"→ {request.method} {request.path}")


@app.after_request
def after_request(response):
    """Логирование после запроса"""
    logger.debug(f"← {response.status_code} {request.path}")
    return response


# ===== ЗАПУСК ПРИЛОЖЕНИЯ =====

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🚀 Инициализация приложения")
    logger.info("=" * 60)
    
    initialize_app()
    
    logger.info("=" * 60)
    logger.info("🚀 Запуск Flask приложения")
    logger.info("=" * 60)
    logger.info(f"📍 http://127.0.0.1:5000")
    logger.info(f"🔗 API: http://127.0.0.1:5000/api/parsers")
    logger.info(f"🔗 API: http://127.0.0.1:5000/api/search")
    logger.info(f"🔗 API: http://127.0.0.1:5000/api/search/multi")
    logger.info(f"🔗 Health: http://127.0.0.1:5000/health")
    logger.info("=" * 60)
    
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.run(debug=debug, host="127.0.0.1", port=5000)
