import logging
import requests
import json
import threading
import time
import sys
import os

# 🆕 Добавляем путь проекта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from services.telegram_bot import TelegramBot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramPoller:
    """Получение сообщений и кнопок от Telegram (Polling)"""
    
    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        self.bot = TelegramBot()
        self.offset = 0
        self.running = False
        self.error_count = 0
        self.max_consecutive_errors = 5
        self.processed_updates = set()
    
    def start(self):
        """Запустить polling в отдельном потоке"""
        self.running = True
        self.error_count = 0
        logger.info("🤖 Запуск Telegram Polling...")
        
        self._cleanup_webhook()
        self._reset_offset()
        
        thread = threading.Thread(target=self._poll_loop, daemon=True, name="TelegramPoller")
        thread.start()
        logger.info("✅ Polling запущен в фоновом потоке")
    
    def stop(self):
        """Остановить polling"""
        self.running = False
        logger.info("⛔ Polling остановлен")
    
    def _cleanup_webhook(self):
        """Очистить webhook перед запуском polling"""
        try:
            logger.info("🧹 Очистка webhook...")
            delete_url = f"{self.api_url}/deleteWebhook"
            
            response = requests.post(delete_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    logger.info("✅ Webhook удалён")
                    time.sleep(1)
        
        except Exception as e:
            logger.debug(f"⚠️ Ошибка при очистке webhook: {e}")
    
    def _reset_offset(self):
        """Получить последний offset"""
        try:
            logger.info("📍 Синхронизация offset...")
            url = f"{self.api_url}/getUpdates"
            params = {'limit': 1, 'timeout': 5}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    updates = data.get('result', [])
                    if updates:
                        self.offset = updates[-1]['update_id'] + 1
                        logger.info(f"✅ Offset синхронизирован: {self.offset}")
        
        except Exception as e:
            logger.debug(f"⚠️ Ошибка синхронизации offset: {e}")
    
    def _poll_loop(self):
        """Основной цикл polling"""
        while self.running:
            try:
                updates = self._get_updates()
                
                if updates:
                    self.error_count = 0
                    
                    for update in updates:
                        update_id = update.get('update_id')
                        
                        if update_id in self.processed_updates:
                            logger.debug(f"⏭️  Обновление {update_id} уже обработано, пропускаем")
                            continue
                        
                        try:
                            self._handle_update(update)
                            self.processed_updates.add(update_id)
                            
                            if len(self.processed_updates) > 100:
                                oldest = min(self.processed_updates)
                                self.processed_updates.remove(oldest)
                        
                        except Exception as e:
                            logger.error(f"❌ Ошибка обработки обновления {update_id}: {e}")
                else:
                    time.sleep(0.5)
            
            except Exception as e:
                logger.error(f"❌ Ошибка в polling: {e}")
                self.error_count += 1
                
                if self.error_count > self.max_consecutive_errors:
                    wait_time = min(60, 5 * self.error_count)
                    logger.warning(f"⚠️ Много ошибок ({self.error_count}). Жду {wait_time} сек...")
                    time.sleep(wait_time)
                else:
                    time.sleep(2)
    
    def _get_updates(self):
        """Получить обновления от Telegram"""
        try:
            url = f"{self.api_url}/getUpdates"
            params = {
                'offset': self.offset,
                'timeout': 25,
                'allowed_updates': ['message', 'callback_query'],
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 409:
                logger.warning("⚠️ HTTP 409: Конфликт polling")
                time.sleep(5)
                self._cleanup_webhook()
                self._reset_offset()
                return []
            
            if response.status_code == 401:
                logger.error("❌ КРИТИЧЕСКАЯ ОШИБКА: Неверный токен!")
                return []
            
            if response.status_code != 200:
                logger.debug(f"⚠️ HTTP {response.status_code}")
                return []
            
            data = response.json()
            
            if not data.get('ok'):
                return []
            
            updates = data.get('result', [])
            
            if updates:
                self.offset = updates[-1]['update_id'] + 1
                logger.debug(f"📨 Получено {len(updates)} обновлений (offset: {self.offset})")
            
            return updates
        
        except requests.exceptions.Timeout:
            return []
        
        except requests.exceptions.ConnectionError:
            logger.debug("❌ Ошибка соединения")
            return []
        
        except Exception as e:
            logger.error(f"❌ Ошибка получения обновлений: {e}")
            return []
    
    def _handle_update(self, update):
        """Обработать обновление от Telegram"""
        try:
            update_id = update.get('update_id')
            
            if 'callback_query' in update:
                self._handle_callback_query(update['callback_query'], update_id)
            
            elif 'message' in update:
                self._handle_message(update['message'], update_id)
        
        except Exception as e:
            logger.error(f"❌ Ошибка обработки обновления: {e}")
    
    def _handle_callback_query(self, callback_query, update_id):
        """Обработать нажатие кнопки"""
        try:
            callback_id = callback_query.get('id')
            callback_data = callback_query.get('data', '')
            from_user = callback_query.get('from', {})
            user_name = from_user.get('first_name', 'Unknown')
            
            logger.info(f"🔘 {user_name} нажал: {callback_data} [ID: {update_id}]")
            
            self.bot.handle_callback(callback_data)
            
            try:
                self.bot.answer_callback(callback_id, text='✅ Выполнено')
            except Exception as e:
                logger.warning(f"⚠️ Ошибка ответа: {e}")
        
        except Exception as e:
            logger.error(f"❌ Ошибка обработки кнопки: {e}")
    
    def _handle_message(self, message, update_id):
        """Обработать текстовое сообщение"""