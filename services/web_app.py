"""
🌍 Web приложение с поддержкой множественных парсеров
Поддерживает: Avito, OLX, Авто.ру, Юла
"""

from flask import Flask, render_template, jsonify, request
import os
import sys
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

# ===== РЕГИСТРАЦИЯ БЛЮПРИНТОВ (ОПЦИОНАЛЬНО) =====
try:
    from services.blueprints.article import article_bp
    from services.blueprints.product import product_bp
    
    app.register_blueprint(article_bp, url_prefix="/articles")
    app.register_blueprint(product_bp, url_prefix="/products")
    logger.info("✅ Блюпринты зарегистрированы")
except ImportError as e:
    logger.warning(f"⚠️ Не удалось загрузить блюпринты: {e}")

# ===== REDIS БРОКЕРЫ (ОПЦИОНАЛЬНО) =====
article_broker = None
product_broker = None

try:
    from messaging.redis_broker import RedisBroker
    article_broker = RedisBroker(stream="article_jobs")
    product_broker = RedisBroker(stream="product_jobs")
    logger.info("✅ Redis брокеры инициализированы")
except ImportError:
    logger.warning("⚠️ Модуль messaging недоступен - Redis функции отключены")
except Exception as e:
    logger.warning(f"⚠️ Ошибка инициализации Redis: {e}")

# ===== ИНИЦИАЛИЗАЦИЯ ПАРСЕРОВ =====
parsers = {}

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
    logger.error(f"❌ Ошибка инициализации парсеров: {e}")


# ===== ГЛАВНЫЕ МАРШРУТЫ =====

@app.route("/")
def dashboard():
    """🏠 Главная страница дашборда"""
    logger.info("📍 Запрос главной страницы")
    try:
        return render_template("dashboard_advanced.html")
    except Exception as e:
        logger.warning(f"⚠️ Template не найден: {e}")
        return "<h1>Dashboard</h1><p>Парсеры работают, но шаблон dashboard_advanced.html не найден</p>"


@app.route("/health")
def health_check():
    """🏥 Проверка здоровья приложения"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "parsers": list(parsers.keys()),
        "redis_available": article_broker is not None,
    })


# ===== API: ИНФОРМАЦИЯ О ПАРСЕРАХ =====

@app.route("/api/parsers", methods=["GET"])
def get_parsers():
    """📋 API: Получить список всех доступных парсеров"""
    logger.info("📍 Запрос списка парсеров")
    
    parsers_info = {
        'avito': {
            'name': '🔵 Avito',
            'url': 'https://avito.ru',
            'description': 'Крупнейшая доска объявлений России',
            'enabled': 'avito' in parsers,
            'icon': '🔵',
        },
        'olx': {
            'name': '🟠 OLX',
            'url': 'https://olx.ua',
            'description': 'Популярная площадка в Восточной Европе',
            'enabled': 'olx' in parsers,
            'icon': '🟠',
        },
        'auto_ru': {
            'name': '🚗 Авто.ру',
            'url': 'https://auto.ru',
            'description': 'Крупнейший сайт продажи автомобилей',
            'enabled': 'auto_ru' in parsers,
            'icon': '🚗',
        },
        'yula': {
            'name': '🟡 Юла',
            'url': 'https://yula.kz',
            'description': 'Доска объявлений Казахстана и Украины',
            'enabled': 'yula' in parsers,
            'icon': '🟡',
        },
    }
    
    return jsonify({
        "status": "success",
        "count": len([p for p in parsers_info.values() if p['enabled']]),
        "parsers": parsers_info,
    })


@app.route("/api/parser/<parser_name>", methods=["GET"])
def get_parser_info(parser_name):
    """📖 API: Получить информацию о конкретном парсере"""
    logger.info(f"📍 Запрос информации о парсере: {parser_name}")
    
    if parser_name not in parsers:
        logger.warning(f"⚠️ Парсер {parser_name} не найден")
        return jsonify({
            "status": "error",
            "message": f"Parser '{parser_name}' not found"
        }), 404
    
    parser_info = {
        'avito': {
            'name': '🔵 Avito',
            'base_url': 'https://avito.ru',
            'categories': ['electronics', 'cars', 'property', 'general'],
            'delay': 2,
        },
        'olx': {
            'name': '🟠 OLX',
            'base_url': 'https://olx.ua',
            'categories': ['general', 'electronics', 'property'],
            'delay': 2,
        },
        'auto_ru': {
            'name': '🚗 Авто.ру',
            'base_url': 'https://auto.ru',
            'categories': ['cars'],
            'delay': 2,
        },
        'yula': {
            'name': '🟡 Юла',
            'base_url': 'https://yula.kz',
            'categories': ['general', 'electronics'],
            'delay': 2,
        },
    }
    
    return jsonify({
        "status": "success",
        "parser": parser_info.get(parser_name, {})
    })


# ===== API: ПОИСК ПО ПАРСЕРАМ =====

@app.route("/api/search", methods=["POST"])
def search_products():
    """🔍 API: Поиск товаров по запросу"""
    data = request.get_json() or {}
    
    query = data.get("query", "").strip()
    parser_name = data.get("parser", "avito")
    limit = data.get("limit", 50)
    min_price = data.get("min_price")
    max_price = data.get("max_price")
    
    logger.info(f"🔍 Поиск: '{query}' на {parser_name}")
    
    if not query:
        return jsonify({
            "status": "error",
            "message": "Query parameter is required"
        }), 400
    
    if parser_name not in parsers:
        return jsonify({
            "status": "error",
            "message": f"Parser '{parser_name}' not found. Available: {list(parsers.keys())}"
        }), 404
    
    try:
        parser = parsers[parser_name]
        products = parser.search_products(
            query=query,
            min_price=min_price,
            max_price=max_price,
            limit=limit
        )
        
        logger.info(f"✅ Найдено {len(products)} товаров на {parser_name}")
        
        return jsonify({
            "status": "success",
            "parser": parser_name,
            "query": query,
            "count": len(products),
            "products": products,
        })
    
    except Exception as e:
        logger.error(f"❌ Ошибка поиска: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/api/search/multi", methods=["POST"])
def search_multi_parsers():
    """🌐 API: Поиск одновременно по нескольким парсерам"""
    data = request.get_json() or {}
    
    query = data.get("query", "").strip()
    parser_list = data.get("parsers", list(parsers.keys()))
    limit = data.get("limit", 30)
    min_price = data.get("min_price")
    max_price = data.get("max_price")
    
    logger.info(f"🌐 Мультипоиск: '{query}' по {len(parser_list)} парсерам")
    
    if not query:
        return jsonify({
            "status": "error",
            "message": "Query parameter is required"
        }), 400
    
    all_results = {}
    
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
        
        try:
            parser = parsers[parser_name]
            products = parser.search_products(
                query=query,
                min_price=min_price,
                max_price=max_price,
                limit=limit
            )
            
            all_results[parser_name] = {
                "count": len(products),
                "products": products,
                "status": "success"
            }
            
            logger.info(f"✅ {parser_name}: {len(products)} товаров")
        
        except Exception as e:
            logger.error(f"❌ Ошибка {parser_name}: {e}")
            all_results[parser_name] = {
                "count": 0,
                "products": [],
                "status": "error",
                "error": str(e)
            }
    
    total_products = sum(r.get("count", 0) for r in all_results.values())
    logger.info(f"📊 Итого найдено: {total_products} товаров")
    
    return jsonify({
        "status": "success",
        "query": query,
        "total_count": total_products,
        "results": all_results,
    })


# ===== API: REDIS РАБОТЫ (LEGACY) =====

@app.route("/api/jobs/<job_type>", methods=["GET"])
def get_jobs(job_type):
    """📋 API: Получить список заданий (устаревший API)"""
    
    if article_broker is None or product_broker is None:
        return jsonify({
            "status": "error",
            "message": "Redis not available"
        }), 503
    
    broker = article_broker if job_type == "article" else product_broker
    
    try:
        messages = broker.redis.xrevrange(broker.stream, count=20)
        jobs = []
        
        for msg_id, fields in messages:
            jobs.append({
                "id": msg_id.decode(),
                "data": {k.decode(): v.decode() for k, v in fields.items()}
            })
        
        logger.info(f"📋 Получено {len(jobs)} заданий типа {job_type}")
        return jsonify({"status": "success", "jobs": jobs})
    
    except Exception as e:
        logger.error(f"❌ Ошибка получения заданий: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/jobs/<job_type>/delete/<job_id>", methods=["POST"])
def delete_job(job_type, job_id):
    """🗑️ API: Удалить задание"""
    
    if article_broker is None or product_broker is None:
        return jsonify({
            "status": "error",
            "message": "Redis not available"
        }), 503
    
    broker = article_broker if job_type == "article" else product_broker
    
    try:
        broker.redis.xdel(broker.stream, job_id)
        logger.info(f"🗑️ Задание {job_id} удалено")
        return jsonify({"status": "deleted", "job_id": job_id})
    
    except Exception as e:
        logger.error(f"❌ Ошибка удаления: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/jobs/<job_type>/requeue/<job_id>", methods=["POST"])
def requeue_job(job_type, job_id):
    """🔄 API: Переставить задание в очередь"""
    
    if article_broker is None or product_broker is None:
        return jsonify({
            "status": "error",
            "message": "Redis not available"
        }), 503
    
    broker = article_broker if job_type == "article" else product_broker
    
    try:
        msg = broker.redis.xrange(broker.stream, min=job_id, max=job_id)
        if msg:
            _, fields = msg[0]
            broker.publish(fields)
            logger.info(f"🔄 Задание {job_id} переставлено в очередь")
            return jsonify({"status": "requeued", "job_id": job_id})
        
        return jsonify({"status": "not_found", "job_id": job_id}), 404
    
    except Exception as e:
        logger.error(f"❌ Ошибка переставки: {e}")
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
    })


# ===== ОБРАБОТКА ОШИБОК =====

@app.errorhandler(404)
def not_found(error):
    """404 ошибка"""
    logger.warning(f"404: {error}")
    return jsonify({"status": "error", "message": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """500 ошибка"""
    logger.error(f"500: {error}")
    return jsonify({"status": "error", "message": "Internal server error"}), 500


# ===== BEFORE REQUEST / AFTER REQUEST =====

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
    logger.info("🚀 Запуск Flask приложения")
    logger.info("=" * 60)
    logger.info(f"📍 http://127.0.0.1:5000")
    logger.info(f"🔗 API: http://127.0.0.1:5000/api/parsers")
    logger.info(f"🔗 API: http://127.0.0.1:5000/api/search")
    logger.info(f"🔗 API: http://127.0.0.1:5000/api/search/multi")
    logger.info(f"🔗 Health: http://127.0.0.1:5000/health")
    logger.info("=" * 60)
    
    app.run(debug=True, host="127.0.0.1", port=5000)