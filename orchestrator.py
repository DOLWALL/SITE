import subprocess
import sys
import time
import threading
import os

# --- АРХИТЕКТУРА ДВОЙНОГО ЗАПУСКА С 3 УРОВНЯМИ РЕЗЕРВИРОВАНИЯ ---

def run_process(script_name):
    print(f"[ORCHESTRATOR] Инициализация {script_name}...")
    
    # Резервный вариант 1: Стандартный subprocess (Основной)
    try:
        process = subprocess.Popen([sys.executable, script_name])
        process.wait()
    except Exception as e:
        print(f"[ERROR] Subprocess упал для {script_name}: {e}. Переход к запасному варианту 2...")
        
        # Резервный вариант 2: Обертка через os.system
        try:
            os.system(f"{sys.executable} {script_name}")
        except Exception as e2:
            print(f"[CRITICAL] os.system упал для {script_name}: {e2}. Переход к запасному варианту 3...")
            
            # Резервный вариант 3: Динамический импорт модуля
            try:
                module_name = script_name.replace('.py', '')
                __import__(module_name)
            except Exception as e3:
                print(f"[FATAL] Все 3 варианта запуска {script_name} завершились ошибкой: {e3}")

if __name__ == '__main__':
    # Убеждаемся, что файлы существуют (создаем пустой main.py, если его нет для теста)
    if not os.path.exists('main.py'):
        with open('main.py', 'w') as f:
            f.write('print("Main bot template loaded.")\n# Сюда положи код своего второго бота\n')

    # Запускаем генератор в отдельном потоке
    gen_thread = threading.Thread(target=run_process, args=('generator.py',))
    main_thread = threading.Thread(target=run_process, args=('main.py',))

    gen_thread.start()
    time.sleep(2) # Даем фору для инициализации
    main_thread.start()

    gen_thread.join()
    main_thread.join()
