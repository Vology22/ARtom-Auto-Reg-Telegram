import os
import time

from core.adb_manager    import AndroidManager
from core.tg_registrator import (
    dump_screen, screen_has,
    wait_and_click, wait_and_click_any,
    get_coords_by_desc, click_next,
    type_text, press_back, generate_name,
)
from api.sms_wrapper  import SmsService
from api.mail_wrapper import MailService
import config.config as cfg

# ── Пути ──────────────────────────────────────────────────────
PROJECT_ROOT   = os.path.dirname(os.path.abspath(__file__))
XML_PATH       = os.path.join(PROJECT_ROOT, "window_dump.xml")
INDONESIA_CODE = "62"

# ══════════════════════════════════════════════════════════════

def enter_phone(device, full_phone: str):
    """
    Вводит номер в форму Telegram одной строкой.
    Telegram сам раскидывает код страны и номер по полям.
    """
    local_number = (full_phone[len(INDONESIA_CODE):]
                    if full_phone.startswith(INDONESIA_CODE)
                    else full_phone)

    print(f"    📞 Код: +{INDONESIA_CODE}, номер: {local_number}")

    dump_screen(device, XML_PATH)
    coords = get_coords_by_desc(XML_PATH, "Код страны")
    if coords:
        x, y = coords
        device.shell(f"input tap {x} {y}")
        time.sleep(0.5)
        device.shell("input keyevent KEYCODE_CTRL_A")
        device.shell("input keyevent KEYCODE_DEL")
        time.sleep(0.3)
        device.shell(f'input text "{INDONESIA_CODE}{local_number}"')
        time.sleep(1)


# ══════════════════════════════════════════════════════════════

def run_registration() -> bool:
    print("\n" + "═" * 55)
    print("   TG Auto-Registration")
    print("═" * 55)

    # [0] Подключаемся к эмулятору
    print("\n[0] Подключаемся к эмулятору...")
    manager = AndroidManager(ldplayer_path=cfg.LDPLAYER_PATH)
    device  = manager.get_device()
    if device is None:
        print("    ❌ Эмулятор не найден!")
        return False
    print("    ✅ Эмулятор найден.")

    # [1] Чистим данные и запускаем Telegram
    print("\n[1] Запускаем Telegram...")
    device.shell(f"pm clear {cfg.TG_PACKAGE}")
    time.sleep(2)
    device.shell(f"am start -n {cfg.TG_PACKAGE}/{cfg.TG_ACTIVITY}")
    time.sleep(4)

    # [2] Приветственный экран
    print("\n[2] Приветственный экран...")
    wait_and_click_any(device, XML_PATH, ["Начать общение", "Start Messaging"],
                       retries=8, delay=3)

    # [3] Системные диалоги (звонки + уведомления)
    print("\n[3] Системные диалоги...")
    wait_and_click_any(device, XML_PATH, ["Продолжить", "Continue"], retries=4, delay=2)
    wait_and_click_any(device, XML_PATH, ["Разрешить", "Allow"],     retries=4, delay=2)
    wait_and_click_any(device, XML_PATH, ["Разрешить", "Allow"],     retries=4, delay=2)
    wait_and_click_any(device, XML_PATH, ["Отклонить", "Deny"],      retries=3, delay=2)

    # [4] Получаем виртуальный номер (Индонезия)
    print("\n[4] Получаем виртуальный номер...")
    sms     = SmsService()
    balance = sms.get_balance()
    print(f"    💰 Баланс: {balance:.2f} долларов.")
    if balance <= 0:
        print("    ❌ Недостаточно средств!")
        return False

    order_id, full_phone = sms.get_number(country_code=cfg.COUNTRY_CODE)
    if not order_id:
        print(f"    ❌ Ошибка получения номера: {full_phone}")
        return False
    print(f"    ✅ Номер: {full_phone}  (order_id: {order_id})")

# [5] Вводим номер телефона
    print("\n[5] Вводим номер телефона...")
    time.sleep(2)
    enter_phone(device, full_phone)
    click_next(device, XML_PATH)
    time.sleep(2)
    wait_and_click_any(device, XML_PATH, ["Да", "Yes", "OK"],         retries=4, delay=2)
    wait_and_click_any(device, XML_PATH, ["Продолжить", "Continue"],  retries=4, delay=2)  # диалог звонков
    wait_and_click_any(device, XML_PATH, ["Разрешить", "Allow"],      retries=4, delay=2)  # системное окно

    # [6] Ждём SMS-код
    print("\n[6] Ждём SMS-код (таймаут 120 сек)...")
    sms_code = sms.wait_for_code(order_id, timeout=120)

    if sms_code in ["TIMEOUT", "CANCELLED"]:
        print(f"    ⏱ Код не пришел ({sms_code}). Отменяем заказ...")
        sms.set_status(order_id, status=8)
        return False
    print(f"    ✅ SMS-код: {sms_code}")

    # [7] Вводим SMS-код
    print("\n[7] Вводим SMS-код...")
    type_text(device, sms_code)
    time.sleep(3)
    sms.set_status(order_id, status=6)
    print("    ✅ Статус заказа подтверждён.")

    # [8] Резервный e-mail через mail.tm
    print("\n[8] Проверяем экран резервной почты...")
    time.sleep(3)
    EMAIL_HINTS = ["email", "Email", "почта", "e-mail",
                   "резервн", "Электронн", "укажите почту"]

    if screen_has(device, XML_PATH, *EMAIL_HINTS):
        mail       = MailService()
        fake_email = mail.create_account()

        type_text(device, fake_email)
        time.sleep(1)
        click_next(device, XML_PATH)
        time.sleep(3)

        print("    ⏳ Ждём код подтверждения на почту...")
        email_code = mail.wait_for_code(timeout=120)

        if email_code:
            print(f"    ✅ Код из письма: {email_code}")
            type_text(device, email_code)
            time.sleep(1)
            click_next(device, XML_PATH)
        else:
            print("    ⚠️ Код не пришёл, пробуем пропустить...")
            if not wait_and_click_any(device, XML_PATH, ["Пропустить", "Skip"],
                                      retries=3, delay=2):
                press_back(device)
    else:
        print("    ℹ️  Email не запрошен.")

    # [9] Создаём профиль (имя)
    print("\n[9] Проверяем экран создания профиля...")
    time.sleep(2)
    NAME_HINTS = ["имя", "name", "First name", "Ваше имя"]

    if screen_has(device, XML_PATH, *NAME_HINTS):
        first_name = generate_name()
        print(f"    👤 Вводим имя: {first_name}")
        type_text(device, first_name)
        time.sleep(1)
        click_next(device, XML_PATH)
        wait_and_click_any(device, XML_PATH, ["Продолжить", "Continue"], retries=3, delay=2)
    else:
        print("    ℹ️  Экран имени не появился.")

    print("\n" + "═" * 55)
    print("   🎉  Регистрация завершена!")
    print("═" * 55 + "\n")
    return True


if __name__ == "__main__":
    if not run_registration():
        print("❌ Регистрация не удалась.")