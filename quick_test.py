#!/usr/bin/env python3
"""
Быстрая проверка извлечения имён документов из контекстов PaperQA.
Без LLM - только проверка структуры данных.
"""

import pickle
from pathlib import Path

def test_context_extraction():
    pkl_path = Path('/app/global_index/docs.pkl')
    with open(pkl_path, 'rb') as f:
        docs = pickle.load(f)
    
    print("📚 Документы в индексе:")
    for name in docs.docnames:
        print(f"  • {name}")
    
    print(f"\n📝 Текстовых фрагментов: {len(docs.texts)}")
    
    print("\n🔍 Проверка извлечения имён:")
    for i, text in enumerate(docs.texts[:5], 1):
        # Так извлекаем имя в paperqa_manager.py
        doc_name = text.name if hasattr(text, 'name') else 'Unknown'
        clean_name = doc_name.split(' pages ')[0] if ' pages ' in doc_name else doc_name
        
        print(f"\n{i}. Полное имя: {doc_name}")
        print(f"   Очищенное: {clean_name}")
        print(f"   Текст: {text.text[:80]}...")
    
    print("\n✅ Проверка завершена")
    print("\nТеперь при запросе через веб-интерфейс:")
    print("1. Откройте http://localhost:8501")
    print("2. Задайте вопрос по документам")
    print("3. В ответе должны быть источники с именами из списка выше")

if __name__ == "__main__":
    test_context_extraction()
