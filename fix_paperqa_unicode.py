#!/usr/bin/env python3
"""
Исправление проблемы Unicode в paper-qa utils.py
Проблема: UnicodeEncodeError при обработке PDF с суррогатными символами
Решение: Добавляем errors="replace" при кодировании в UTF-8
"""

import sys
import os

def fix_paperqa_utils():
    """Исправляет utils.py в установке paper-qa"""
    
    # Путь к utils.py (может отличаться в зависимости от окружения)
    possible_paths = [
        "/usr/local/lib/python3.11/site-packages/paperqa/utils.py",
        "/usr/local/lib/python3.10/site-packages/paperqa/utils.py",
        "/usr/local/lib/python3.9/site-packages/paperqa/utils.py",
    ]
    
    utils_path = None
    for path in possible_paths:
        if os.path.exists(path):
            utils_path = path
            break
    
    if not utils_path:
        print("❌ Не удалось найти paper-qa/utils.py")
        print("Попробуйте указать путь вручную:")
        print("  python fix_paperqa_unicode.py /path/to/paperqa/utils.py")
        return False
    
    print(f"Найден файл: {utils_path}")
    
    with open(utils_path, 'r') as f:
        content = f.read()
    
    old = 'data = data.encode("utf-8")'
    new = 'data = data.encode("utf-8", errors="replace")'
    
    if new in content:
        print("✅ Исправление уже применено")
        return True
    
    if old in content:
        content = content.replace(old, new)
        with open(utils_path, 'w') as f:
            f.write(content)
        print("✅ Исправление применено!")
        return True
    else:
        print("❌ Строка не найдена. Возможно, структура файла изменилась")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Ручное указание пути
        utils_path = sys.argv[1]
        if not os.path.exists(utils_path):
            print(f"❌ Файл не найден: {utils_path}")
            sys.exit(1)
        
        with open(utils_path, 'r') as f:
            content = f.read()
        
        old = 'data = data.encode("utf-8")'
        new = 'data = data.encode("utf-8", errors="replace")'
        
        if new in content:
            print("✅ Исправление уже применено")
        elif old in content:
            content = content.replace(old, new)
            with open(utils_path, 'w') as f:
                f.write(content)
            print("✅ Исправление применено!")
        else:
            print("❌ Строка не найдена")
            sys.exit(1)
    else:
        fix_paperqa_utils()
