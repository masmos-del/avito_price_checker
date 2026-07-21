#!/usr/bin/env python3
"""
Главный скрипт сервиса Avito Price Checker
Версия 3.1 с поддержкой Avito, OLX, Авто.ру, Юла
"""

import logging
import schedule
import time
import threading
from datetime import datetime
from parsers.avito_parser import AvitoParser
from parsers.olx_parser import OLXParser
from parsers.auto_ru_parser import AutoRuParser
from parsers.yula_parser import YulaParser
from services.price_analyzer import PriceAnalyzer
from services.notifier import Notifier
from services.telegram_bot import TelegramBot
from services.telegram_polling import TelegramPoller
from services.web_app import app as web_app
from models import init_db
from config import SEARCH_PARAMS, MONITOR_INTERVAL_HOURS, LOG_FILE, DEBUG

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MultiSiteMonitor:
    """Мониторинг нескольких сайтов (Avito, OLX, Авто.ру, Юла)"""
    
    def __init__(self):
        self.parsers = {
            'avito': AvitoParser(),
            'olx': OLXParser(),
            'auto_ru': AutoRuParser(),
            'yula': YulaParser(),
        }
        
        self.parser_names = {
            'avito': '🔵 Avito',
            'olx': '🟠 OLX',
            'auto_ru': '🚗 Авто.ру',
            'yula': '🟡 Юла',
        }
        
        self.analyzer = PriceAnalyzer()
        self.notifier = Notifier()
        self.bot = TelegramBot()
        init_db()
        logger.info("✅ MultiSiteMonitor инициализирован")
    
    def run_full_scan(self):
        """Запустить полное сканирование всех платформ"""
        logger.info("🚀 СТАРТ СКАНИРОВАНИЯ")
        logger.info("=" * 70)
        
        all_deals = []
        total_products = 0
        total_sites = len(self.parsers)
        processed_sites = 0
        
        for site_key, parser in self.parsers.items():
            site_name = self.parser_names[site_key]
            processed_sites += 1
            
            logger.info(f"\n📍 [{processed_sites}/{total_sites}] Сканирование {site_name}...")
            logger.info("-" * 70)
            
            site_deals = 0
            
            for category, params in SEARCH_PARAMS.items():
                logger.info(f"\n🏷️  Категория: {category}")
                
                for keyword in params['keywords']:
                    logger.info(f"  🔎 Ищем: '{keyword}'")
                    
                    try:
                        # Получаем товары с сайта
                        products = parser.search_products(
                            query=keyword,
                            max_price=params.get('max_price'),
                            min_price=params.get('min_price'),
                        )
                        
                        if not products:
                            logger.info(f"  ❌ Товаров не найдено")
                            continue
                        
                        total_products += len(products)
                        logger.info(f"  📦 Получено товаров: {len(products)}")
                        
                        # Анализируем выгодность
                        profitable = self.analyzer.analyze_products(products)
                        
                        if profitable:
                            site_deals += len(profitable)
                            all_deals.extend(profitable)
                            logger.info(f"  ✅ Выгодных товаров: {len(profitable)} на {site_name}!")
                        else:
                            logger.info(f"  ⚠️ Выгодных товаров не найдено")
                    
                    except Exception as e:
                        logger.error(f"  ❌ Ошибка при поиске на {site_name}: {e}")
                        continue
            
            if site_deals > 0:
                logger.info(f"\n✅ {site_name}: {site_deals} выгодных товаров найдено")
            else:
                logger.info(f"\n⚠️ {site_name}: выгодных товаров не найдено")
        
        logger.info("\n" + "=" * 70)
        logger.info(f"📊 ИТОГОВАЯ СТАТИСТИКА:")
        logger.info(f"  📦 Всего товаров проанализировано: {total_products}")
        logger.info(f"  💰 Выгодных товаров найдено: {len(all_deals)}")
        logger.info(f"  🌍 Площадок отсканировано: {total_sites}")
        
        if all_deals:
            logger.info(f"\n📤 Отправляем результаты в Telegram...")
            self.notifier.send_products_to_telegram(all_deals)
            logger.info(f"✅ {len(all_deals)} товаров отправлено в Telegram")
        else:
            logger.info("ℹ️  Нет выгодных товаров для отправки")
        
        logger.info("✓ Сканирование завершено\n")
        return all_deals


def job():
    """Задача для запуска по расписанию"""
    logger.info(f"\n{'='*70}")
    logger.info(f"⏰ ПЛАНОВОЕ СКАНИРОВАНИЕ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"{'='*70}")
    
    monitor = MultiSiteMonitor()
    monitor.run_full_scan()


def run_once():
    """Запустить один раз"""
    logger.info("🎯 Режим: ОДИН РАЗ")
    monitor = MultiSiteMonitor()
    monitor.bot.send_start_message()
    monitor.run_full_scan()
    monitor.bot.send_statistics()


def run_scheduler():
    """Запустить с периодичностью + Polling + Web"""
    logger.info(f"🎯 Режим: ПЕРИОДИЧЕСКИЙ МОНИТОРИНГ + TELEGRAM POLLING + ВЕБ")
    logger.info(f"⏱️  Интервал: каждые {MONITOR_INTERVAL_HOURS} часов")
    logger.info(f"🌍 Поддерживаемые сайты: Avito, OLX, Авто.ру, Юла")
    
    monitor = MultiSiteMonitor()
    
    # 🌐 Запускаем веб-интерфейс в отдельном потоке
    web_thread = threading.Thread(target=lambda: web_app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False
    ), daemon=True)
    web_thread.start()
    logger.info("🌐 Веб-интерфейс запущен: http://0.0.0.0:5000")
    
    # Даём Flask время на инициализацию
    logger.info("⏳ Даём Flask время на инициализацию (5 сек)...")
    time.sleep(5)
    
    # Запускаем Polling
    logger.info("🚀 Запуск Telegram Polling...")
    poller = TelegramPoller()
    poller.start()
    
    # Ещё одна задержка
    time.sleep(2)
    
    # Отправляем стартовое сообщение
    monitor.bot.send_start_message()
    
    # Первый запуск сразу
    job()
    
    # Затем по расписанию
    schedule.every(MONITOR_INTERVAL_HOURS).hours.do(job)
    
    logger.info("✅ Расписание установлено")
    logger.info("✅ Telegram Polling активирован")
    logger.info("✅ Веб-интерфейс активирован")
    logger.info("✅ Ожидаем следующего запуска...\n")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("\n⛔ Приложение остановлено")
        poller.stop()


def interactive_mode():
    """Интерактивный режим для тестирования команд"""
    logger.info("🎯 Режим: ИНТЕРАКТИВНЫЙ")
    
    monitor = MultiSiteMonitor()
    monitor.bot.send_start_message()
    
    print("\n" + "="*70)
    print("🤖 ИНТЕРАКТИВНЫЙ РЕЖИМ")
    print("="*70)
    print("\nДоступные команды:")
    print("  /stats  - Статистика")
    print("  /recent - Последние товары")
    print("  /best   - Топ скидок")
    print("  /help   - Справка")
    print("  /scan   - Запустить сканирование")
    print("  /exit   - Выход")
    print("\n" + "="*70 + "\n")
    
    while True:
        try:
            command = input("Введи команду: ").strip()
            
            if command == '/exit':
                print("👋 До свидания!")
                break
            elif command == '/scan':
                print("\n🚀 Запуск сканирования...\n")
                monitor.run_full_scan()
                print("\n✅ Сканирование завершено\n")
            else:
                monitor.bot.handle_callback(command)
        
        except KeyboardInterrupt:
            print("\n\n👋 До свидания!")
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")


def main():
    """Главная функция"""
    import sys
    
    logger.info("🚀 ЗАПУСК AVITO PRICE CHECKER v3.1 (Multi-Site)")
    logger.info(f"⚙️  DEBUG режим: {DEBUG}")
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        
        if mode == '--once':
            run_once()
        elif mode == '--interactive':
            interactive_mode()
        else:
            print(f"❌ Неизвестный режим: {mode}")
            print("\nДоступные режимы:")
            print("  python main.py              - Периодический мониторинг + Web + Polling")
            print("  python main.py --once       - Один раз")
            print("  python main.py --interactive - Интерактивный режим")
    else:
        run_scheduler()


if __name__ == "__main__":
    main()
