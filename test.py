import requests
import sys
import time
import random

ESP_IP = "192.168.0.139"
BASE_URL = f"http://{ESP_IP}/command"
STATUS_URL = f"http://{ESP_IP}/status"


def get_status():
    try:
        response = requests.get(STATUS_URL, timeout=2)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    return None


def move_smooth(gripper=None, base=None, elbow=None, wrist=None, duration=1500):
    """
    Плавное движение. ESP32 сам интерполирует.
    duration: время движения в миллисекундах (по умолчанию 1.5 сек)
    """
    payload = {"duration": duration}
    if gripper is not None: payload["gripper"] = int(gripper)
    if base is not None: payload["base"] = int(base)
    if elbow is not None: payload["elbow"] = int(elbow)
    if wrist is not None: payload["wrist"] = int(wrist)

    try:
        response = requests.post(BASE_URL, json=payload, timeout=2)
        if response.status_code == 200:
            print(f"✅ Движение запущено (длительность: {duration}мс)")
            return True
        else:
            print(f"❌ Ошибка: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка связи: {e}")
        return False


def wait_until_stopped(timeout=10):
    """Ждем завершения движения"""
    start = time.time()
    while time.time() - start < timeout:
        status = get_status()
        if status and not status.get('moving', False):
            return True
        time.sleep(0.1)
    return False


# ================= ДЕМО =================

def demo_wave():
    print("\n🎬 ДЕМО: Приветствие")
    for _ in range(3):
        move_smooth(gripper=120, base=45, elbow=110, wrist=140, duration=800)
        wait_until_stopped()
        move_smooth(gripper=60, base=135, elbow=110, wrist=100, duration=800)
        wait_until_stopped()
    move_smooth(gripper=120, base=90, elbow=100, wrist=90, duration=1000)
    wait_until_stopped()


def demo_pick_and_place():
    print("\n🎬 ДЕМО: Взять и положить (Deep Reach)")

    # 1. Подходим к объекту (высоко, база повернута)
    move_smooth(gripper=120, base=45, elbow=140, wrist=90, duration=1500)
    wait_until_stopped()

    # 2. Опускаемся НИЖЕ и ДАЛЬШЕ
    # Локоть опускаем до 85° (почти минимум)
    # Запястье увеличиваем до 120°, чтобы компенсировать наклон и держать клешню горизонтально
    move_smooth(gripper=120, base=45, elbow=60, wrist=160, duration=1800)
    wait_until_stopped()

    # 3. Хватаем
    move_smooth(gripper=16, duration=600)
    wait_until_stopped()
    time.sleep(0.5)

    # 4. Поднимаем объект (синхронно локоть и запястье)
    move_smooth(gripper=16, base=45, elbow=150, wrist=110, duration=1500)
    wait_until_stopped()

    # 5. Поворачиваем базу в другую сторону
    move_smooth(gripper=16, base=135, elbow=140, wrist=110, duration=1500)
    wait_until_stopped()

    # 6. Опускаемся для отпускания (также низко и далеко)
    move_smooth(gripper=16, base=135, elbow=60, wrist=160, duration=1800)
    wait_until_stopped()

    # 7. Отпускаем
    move_smooth(gripper=120, duration=800)
    wait_until_stopped()
    time.sleep(0.5)

    # 8. Возврат домой
    move_smooth(gripper=120, base=90, elbow=100, wrist=90, duration=1500)
    wait_until_stopped()


def demo_random_dance():
    print("\n🎬 ДЕМО: Танец")
    for _ in range(5):
        rand_g = random.choice([16, 60, 120])
        rand_b = random.randint(30, 150)
        rand_w = random.randint(80, 150)
        rand_e = random.randint(100, 150) if rand_w < 90 else random.randint(60, 150)

        move_smooth(gripper=rand_g, base=rand_b, elbow=rand_e, wrist=rand_w, duration=1000)
        wait_until_stopped()
        time.sleep(0.2)

    move_smooth(gripper=120, base=90, elbow=100, wrist=90, duration=1500)
    wait_until_stopped()


def interactive_mode():
    print("\n🤖 Управление клешней (Smooth Mode)")
    print("=" * 55)
    print("Команды:")
    print("  status              - показать статус")
    print("  home                - плавный возврат домой")
    print("  grab / release      - закрыть / открыть клешню")
    print("  set G B E W [T]     - плавный переход (T - время в мс, по умолчанию 1500)")
    print("  demo_wave           - демо: приветствие")
    print("  demo_pick           - демо: взять и положить")
    print("  demo_dance          - демо: танец")
    print("  exit                - выход")
    print("=" * 55)

    while True:
        try:
            cmd = input("\n> ").strip().lower()
            if not cmd:
                continue

            parts = cmd.split()
            action = parts[0]

            if action in ['exit', 'quit']:
                print("👋 Выход")
                break
            elif action == 'status':
                get_status()
            elif action == 'home':
                move_smooth(120, 90, 100, 90, duration=1500)
                wait_until_stopped()
            elif action == 'grab':
                move_smooth(gripper=16, duration=500)
                wait_until_stopped()
            elif action == 'release':
                move_smooth(gripper=120, duration=500)
                wait_until_stopped()
            elif action == 'set' and len(parts) >= 5:
                try:
                    g, b, e, w = map(int, parts[1:5])
                    duration = int(parts[5]) if len(parts) > 5 else 1500
                    move_smooth(g, b, e, w, duration)
                    wait_until_stopped()
                except ValueError:
                    print("❌ Формат: set G B E W [T]")
            elif action == 'demo_wave':
                demo_wave()
            elif action == 'demo_pick':
                demo_pick_and_place()
            elif action == 'demo_dance':
                demo_random_dance()
            else:
                print("❓ Неизвестная команда")
        except KeyboardInterrupt:
            print("\n👋 Выход")
            break


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == 'set' and len(sys.argv) >= 6:
            g, b, e, w = map(int, sys.argv[2:6])
            duration = int(sys.argv[6]) if len(sys.argv) > 6 else 1500
            move_smooth(g, b, e, w, duration)
        else:
            print("Использование: python claw.py set <G> <B> <E> <W> [T]")
    else:
        interactive_mode()