import os
import re
import time
import random
import string
import xml.etree.ElementTree as ET


# ── XML / координаты ──────────────────────────────────────────

def get_coords_by_text(xml_path, target_text):
    """Возвращает (x, y) центра элемента по атрибуту text."""
    if not os.path.exists(xml_path):
        return None
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError:
        return None

    for node in root.iter('node'):
        text = node.get('text', '')
        if target_text.lower() in text.lower():
            bounds = node.get('bounds')
            if bounds:
                coords = list(map(int, re.findall(r'\d+', bounds)))
                if len(coords) == 4:
                    x1, y1, x2, y2 = coords
                    return (x1 + x2) // 2, (y1 + y2) // 2
    return None


def get_coords_by_desc(xml_path, target_desc):
    """Возвращает (x, y) центра элемента по атрибуту content-desc."""
    if not os.path.exists(xml_path):
        return None
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError:
        return None

    for node in root.iter('node'):
        desc = node.get('content-desc', '')
        if target_desc.lower() in desc.lower():
            bounds = node.get('bounds')
            if bounds:
                coords = list(map(int, re.findall(r'\d+', bounds)))
                if len(coords) == 4:
                    x1, y1, x2, y2 = coords
                    return (x1 + x2) // 2, (y1 + y2) // 2
    return None


# ── Работа с дампом экрана ────────────────────────────────────

def dump_screen(device, xml_path):
    """Сохраняет XML-дамп текущего экрана эмулятора на диск."""
    device.shell("uiautomator dump /sdcard/window_dump.xml")
    device.pull("/sdcard/window_dump.xml", xml_path)
    device.shell("rm /sdcard/window_dump.xml")


def screen_has(device, xml_path, *hints) -> bool:
    """Обновляет дамп и проверяет, есть ли хотя бы один из текстов на экране."""
    dump_screen(device, xml_path)
    return any(get_coords_by_text(xml_path, h) for h in hints)


# ── Клики по text ─────────────────────────────────────────────

def get_click_on_button(device, xml_path, target) -> bool:
    """Обновляет дамп и кликает по элементу с нужным text."""
    dump_screen(device, xml_path)
    coords = get_coords_by_text(xml_path, target)
    if coords:
        x, y = coords
        device.shell(f"input tap {x} {y}")
        return True
    return False


def wait_and_click(device, xml_path, target, retries=6, delay=3) -> bool:
    """Ждёт появления элемента по text и кликает по нему."""
    for attempt in range(1, retries + 1):
        if get_click_on_button(device, xml_path, target):
            print(f"    ✓ Клик: «{target}»")
            time.sleep(1.5)
            return True
        print(f"    ⏳ «{target}» не найден ({attempt}/{retries})...")
        time.sleep(delay)
    print(f"    ✗ «{target}» так и не появился.")
    return False


def wait_and_click_any(device, xml_path, targets: list, retries=6, delay=3) -> bool:
    """Пробует кликнуть по первому найденному тексту из списка вариантов."""
    for attempt in range(1, retries + 1):
        dump_screen(device, xml_path)
        for target in targets:
            coords = get_coords_by_text(xml_path, target)
            if coords:
                x, y = coords
                device.shell(f"input tap {x} {y}")
                print(f"    ✓ Клик: «{target}»")
                time.sleep(1.5)
                return True
        print(f"    ⏳ Не найдено {targets} ({attempt}/{retries})...")
        time.sleep(delay)
    print(f"    ✗ Ничего не найдено из: {targets}")
    return False


# ── Клики по content-desc ─────────────────────────────────────

def click_by_desc(device, xml_path, target_desc) -> bool:
    """Обновляет дамп и кликает по элементу с нужным content-desc."""
    dump_screen(device, xml_path)
    coords = get_coords_by_desc(xml_path, target_desc)
    if coords:
        x, y = coords
        device.shell(f"input tap {x} {y}")
        return True
    return False


def wait_and_click_by_desc(device, xml_path, target_desc, retries=6, delay=3) -> bool:
    """Ждёт появления элемента по content-desc и кликает по нему."""
    for attempt in range(1, retries + 1):
        if click_by_desc(device, xml_path, target_desc):
            print(f"    ✓ Клик (desc): «{target_desc}»")
            time.sleep(1.5)
            return True
        print(f"    ⏳ «{target_desc}» не найден ({attempt}/{retries})...")
        time.sleep(delay)
    print(f"    ✗ «{target_desc}» так и не появился.")
    return False


def click_next(device, xml_path) -> bool:
    """
    Нажимает кнопку «далее» — пробует content-desc на русском и английском,
    если не нашёл — жмёт Enter как fallback.
    """
    dump_screen(device, xml_path)
    for desc in ["Готово", "Done", "Next", "Далее"]:
        coords = get_coords_by_desc(xml_path, desc)
        if coords:
            x, y = coords
            device.shell(f"input tap {x} {y}")
            print(f"    ✓ Клик (desc): «{desc}»")
            time.sleep(1.5)
            return True
    # Fallback — Enter
    print("    ✓ Enter (fallback)")
    device.shell("input keyevent 66")
    time.sleep(1.5)
    return True


# ── Ввод текста / клавиши ─────────────────────────────────────

def type_text(device, text: str):
    """Вводит текст в активное поле ввода."""
    escaped = text.replace('"', '\\"').replace("'", "\\'").replace(" ", "%s")
    device.shell(f'input text "{escaped}"')
    time.sleep(1)


def press_enter(device):
    device.shell("input keyevent 66")
    time.sleep(1)


def press_back(device):
    device.shell("input keyevent 4")
    time.sleep(1)


# ── Генераторы данных ─────────────────────────────────────────

def generate_name() -> str:
    """Генерирует случайное имя для профиля."""
    return (random.choice(string.ascii_uppercase) +
            ''.join(random.choices(string.ascii_lowercase, k=random.randint(4, 7))))