#!/usr/bin/env python3
"""
Скрипт для просмотра индексов PaperQA2.
Показывает информацию о глобальном индексе и индексах сессий.
"""

import os
import json
import pickle
from pathlib import Path
from datetime import datetime

DATA_VOLUME = Path(__file__).parent / "data_volume"
GLOBAL_INDEX_PATH = DATA_VOLUME / "global_index"
INDICES_PATH = DATA_VOLUME / "indices"


def get_file_size_mb(path: Path) -> float:
    """Размер файла в МБ."""
    return path.stat().st_size / (1024 * 1024) if path.exists() else 0


def get_dir_size_mb(path: Path) -> float:
    """Размер директории в МБ."""
    total = 0
    if path.exists():
        for p in path.rglob('*'):
            if p.is_file():
                total += p.stat().st_size
    return total / (1024 * 1024)


def view_pickle_info(pkl_path: Path) -> dict:
    """Чтение информации из pickle файла PaperQA."""
    if not pkl_path.exists():
        return {"error": "Файл не найден"}
    
    try:
        with open(pkl_path, 'rb') as f:
            docs = pickle.load(f)
        
        info = {
            "type": type(docs).__name__,
            "doc_count": 0,
            "texts_count": 0,
        }
        
        # PaperQA Docs объект
        if hasattr(docs, 'docnames'):
            info["doc_count"] = len(docs.docnames) if docs.docnames else 0
        if hasattr(docs, 'texts'):
            info["texts_count"] = len(docs.texts) if docs.texts else 0
        
        # Получаем названия документов
        if hasattr(docs, 'docnames') and docs.docnames:
            info["documents"] = list(docs.docnames)
        
        return info
    except Exception as e:
        return {"error": str(e)}


def view_global_index():
    """Просмотр глобального индекса."""
    print("\n" + "=" * 60)
    print("📚 ГЛОБАЛЬНЫЙ ИНДЕКС")
    print("=" * 60)
    
    if not GLOBAL_INDEX_PATH.exists():
        print(f"❌ Глобальный индекс не найден: {GLOBAL_INDEX_PATH}")
        return
    
    print(f"\n📁 Путь: {GLOBAL_INDEX_PATH}")
    print(f"📊 Размер: {get_dir_size_mb(GLOBAL_INDEX_PATH):.2f} МБ")
    
    # Основные файлы
    docs_pkl = GLOBAL_INDEX_PATH / "docs.pkl"
    docs_json = GLOBAL_INDEX_PATH / "docs.json"
    papers_dir = GLOBAL_INDEX_PATH / "papers"
    documents_dir = GLOBAL_INDEX_PATH / "documents"
    
    print(f"\n📄 Файлы:")
    if docs_pkl.exists():
        print(f"   • docs.pkl — {get_file_size_mb(docs_pkl):.2f} МБ")
        print(f"     Последнее изменение: {datetime.fromtimestamp(docs_pkl.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("   • docs.pkl — не найден")
    
    if docs_json.exists():
        print(f"   • docs.json — {get_file_size_mb(docs_json):.2f} МБ")
    else:
        print("   • docs.json — не найден")
    
    print(f"\n📁 papers/ — {get_dir_size_mb(papers_dir):.2f} МБ")
    if papers_dir.exists():
        papers = list(papers_dir.glob('*'))
        print(f"   Файлов: {len(papers)}")
        for p in papers[:10]:
            print(f"     - {p.name} ({get_file_size_mb(p):.2f} МБ)")
        if len(papers) > 10:
            print(f"     ... и ещё {len(papers) - 10}")
    
    print(f"\n📁 documents/ — {get_dir_size_mb(documents_dir):.2f} МБ")
    if documents_dir.exists():
        docs = list(documents_dir.glob('*'))
        print(f"   Файлов: {len(docs)}")
        for d in docs[:10]:
            print(f"     - {d.name} ({get_file_size_mb(d):.2f} МБ)")
        if len(docs) > 10:
            print(f"     ... и ещё {len(docs) - 10}")
    
    # Информация из pickle
    if docs_pkl.exists():
        print(f"\n📊 Информация из docs.pkl:")
        info = view_pickle_info(docs_pkl)
        if "error" not in info:
            print(f"   Тип: {info['type']}")
            print(f"   Документов: {info['doc_count']}")
            print(f"   Текстовых фрагментов: {info['texts_count']}")
            if info.get('documents'):
                print(f"\n   Список документов:")
                for doc in info['documents'][:20]:
                    print(f"     • {doc}")
                if len(info['documents']) > 20:
                    print(f"     ... и ещё {len(info['documents']) - 20}")
        else:
            print(f"   ❌ Ошибка чтения: {info['error']}")


def view_session_indices():
    """Просмотр индексов сессий."""
    print("\n" + "=" * 60)
    print("👥 ИНДЕКСЫ СЕССИЙ")
    print("=" * 60)
    
    if not INDICES_PATH.exists():
        print(f"❌ Индексы сессий не найдены: {INDICES_PATH}")
        return
    
    print(f"\n📁 Путь: {INDICES_PATH}")
    
    session_dirs = [d for d in INDICES_PATH.iterdir() if d.is_dir()]
    
    if not session_dirs:
        print("\n⚠️ Сессии не найдены")
        return
    
    print(f"\n📊 Всего сессий: {len(session_dirs)}")
    
    for session_dir in session_dirs:
        print(f"\n{'─' * 60}")
        print(f"📂 Сессия: {session_dir.name}")
        print(f"   Путь: {session_dir}")
        print(f"   Размер: {get_dir_size_mb(session_dir):.2f} МБ")
        
        docs_pkl = session_dir / "docs.pkl"
        papers_dir = session_dir / "papers"
        
        if docs_pkl.exists():
            print(f"\n   📄 docs.pkl — {get_file_size_mb(docs_pkl):.2f} МБ")
            print(f"      Изменён: {datetime.fromtimestamp(docs_pkl.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
            
            info = view_pickle_info(docs_pkl)
            if "error" not in info:
                print(f"   Документов: {info['doc_count']}")
                print(f"   Текстовых фрагментов: {info['texts_count']}")
                if info.get('documents'):
                    print(f"\n   Документы в сессии:")
                    for doc in info['documents'][:10]:
                        print(f"     • {doc}")
                    if len(info['documents']) > 10:
                        print(f"     ... и ещё {len(info['documents']) - 10}")
        else:
            print("   ❌ docs.pkl не найден")
        
        if papers_dir.exists():
            papers = list(papers_dir.glob('*'))
            print(f"\n   📁 papers/ — {len(papers)} файлов, {get_dir_size_mb(papers_dir):.2f} МБ")
            for p in papers[:5]:
                print(f"     - {p.name} ({get_file_size_mb(p):.2f} МБ)")
            if len(papers) > 5:
                print(f"     ... и ещё {len(papers) - 5}")


def view_sessions_json():
    """Просмотр информации о сессиях из sessions.json."""
    print("\n" + "=" * 60)
    print("📋 ИНФОРМАЦИЯ О СЕССИЯХ (sessions.json)")
    print("=" * 60)
    
    sessions_file = DATA_VOLUME / "sessions.json"
    if not sessions_file.exists():
        print(f"❌ sessions.json не найден")
        return
    
    try:
        with open(sessions_file, 'r', encoding='utf-8') as f:
            sessions = json.load(f)
        
        print(f"\n📊 Всего сессий: {len(sessions)}")
        
        for session_id, session_data in sessions.items():
            print(f"\n{'─' * 60}")
            print(f"ID: {session_id}")
            print(f"   Пользователь: {session_data.get('user_id', 'N/A')}")
            print(f"   Название: {session_data.get('name', 'Без названия')}")
            print(f"   Статус: {session_data.get('status', 'unknown')}")
            
            created = session_data.get('created_at')
            if created:
                print(f"   Создана: {created}")
            
            last_activity = session_data.get('last_activity')
            if last_activity:
                print(f"   Последняя активность: {last_activity}")
            
            expires = session_data.get('expires_at')
            if expires:
                print(f"   Истекает: {expires}")
            
            projects = session_data.get('projects', [])
            print(f"   Проектов: {len(projects)}")
            
            docs = session_data.get('documents', [])
            print(f"   Документов: {len(docs)}")
            for doc in docs[:5]:
                print(f"     • {doc.get('name', 'N/A')} [{doc.get('category', 'N/A')}]")
            if len(docs) > 5:
                print(f"     ... и ещё {len(docs) - 5}")
    
    except Exception as e:
        print(f"❌ Ошибка чтения sessions.json: {e}")


def main():
    print("\n" + "🔍" * 30)
    print("ПРОСМОТР ИНДЕКСОВ PAPERQA2")
    print("🔍" * 30)
    print(f"\nData volume: {DATA_VOLUME}")
    print(f"Дата проверки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    view_global_index()
    view_session_indices()
    view_sessions_json()
    
    print("\n" + "=" * 60)
    print("✅ Просмотр завершён")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
