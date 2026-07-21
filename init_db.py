#!/usr/bin/env python3
"""
Инициализация базы данных
"""

import sys
import os

# Добавляем путь проекта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import init_db

print("🔄 Инициализация базы данных...")
init_db()
print("✅ База данных создана успешно!")
print("\nТеперь можешь запустить: python main.py")