"""
Risk-check: проверяет что Pymiere может подключиться к открытому Premiere.

Запуск:
    .\.venv\Scripts\python.exe tests\test_pymiere_connection.py

Что должно произойти:
1. Premiere должен быть УЖЕ запущен (открой его руками).
2. CEP-панель Pymiere Link должна быть включена в меню Premiere:
   Window → Extensions → Pymiere Link  (один раз кликнуть, чтобы стартовать).
3. Этот скрипт получит текущий проект (или None, если проекта нет),
   создаст пустой проект и оставит его открытым.
"""
import sys
from pathlib import Path

import pymiere
from pymiere import exe_utils


def main():
    print("=" * 60)
    print("Pymiere ↔ Premiere Pro 2025 — risk-check")
    print("=" * 60)

    # 1. Проверка что Premiere запущен
    print("\n[1/4] Проверяю запущен ли Premiere...")
    if not exe_utils.is_premiere_running():
        print("  ERROR: Premiere не запущен. Открой его и повтори.")
        sys.exit(1)
    print("  OK: Premiere процесс найден.")

    # 2. Проверка CEP-панели
    print("\n[2/4] Проверяю CEP-панель Pymiere Link...")
    try:
        # любой вызов на App вызывает ExtendScript через CEP
        app_version = pymiere.objects.app.version
        print(f"  OK: app.version = {app_version}")
    except Exception as e:
        print(f"  ERROR: CEP-панель не отвечает: {e}")
        print("  Запусти в Premiere: Window → Extensions → Pymiere Link")
        sys.exit(2)

    # 3. Информация о проекте
    print("\n[3/4] Текущий проект:")
    try:
        project = pymiere.objects.app.project
        if project and project.name:
            print(f"  Открыт проект: {project.name}")
            print(f"  Путь: {project.path}")
            seq = project.activeSequence
            if seq:
                print(f"  Активная sequence: {seq.name}")
            else:
                print("  Активной sequence нет.")
        else:
            print("  Проекта нет (это нормально для теста).")
    except Exception as e:
        print(f"  WARN: не смог прочитать project: {e}")

    # 4. Создаём пустой тестовый проект
    print("\n[4/4] Создаю тестовый проект...")
    test_project_path = Path(__file__).parent / "_pymiere_test.prproj"
    try:
        if test_project_path.exists():
            test_project_path.unlink()
        pymiere.objects.app.openDocument(str(test_project_path), False, True)
        print(f"  OK: создал и открыл {test_project_path}")
    except Exception as e:
        # newProject может не работать, попробуем альтернативу
        try:
            pymiere.objects.app.newProject(str(test_project_path))
            print(f"  OK (через newProject): {test_project_path}")
        except Exception as e2:
            print(f"  WARN: создание проекта дало ошибку: {e2}")
            print("  (некритично — основная связь работает)")

    print("\n" + "=" * 60)
    print("УСПЕХ: Pymiere может управлять Premiere.")
    print("=" * 60)


if __name__ == "__main__":
    main()
