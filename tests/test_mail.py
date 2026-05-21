import sys
import os
import time
import requests
resp = requests.get("https://api.mail.tm/domains", timeout=10)
print(resp.json())
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.mail_wrapper import MailService
import requests

BASE_URL = "https://api.guerrillamail.com/ajax.php"


def test_mailbox():
    print("\n" + "═" * 50)
    print("   Guerrillamail — тест почтового ящика")
    print("═" * 50)

    mail = MailService()

    # [1] Создаём ящик
    print("\n[1] Создаём ящик...")
    try:
        email = mail.create_account()
        print(f"    ✅ Адрес: {email}")
    except Exception as e:
        print(f"    ❌ Ошибка создания ящика: {e}")
        return

    # [2] Просим отправить письмо
    print(f"\n[2] Отправь письмо на: {email}")
    print("    Потом нажми Enter...")
    input()

    # [3] Ждём 30 секунд
    print("\n[3] Ждём 30 секунд пока письмо дойдёт...")
    for i in range(30, 0, -5):
        print(f"    ⏳ Осталось {i} сек...")
        time.sleep(5)

    # [4] Проверяем входящие
    print("\n[4] Проверяем входящие...")
    resp   = requests.get(BASE_URL, params={
        "f":         "get_email_list",
        "offset":    0,
        "sid_token": mail.email_key,
        "seq":       0,
    }, timeout=10)
    emails = resp.json().get("list", [])
    print(f"    📬 Писем в ящике: {len(emails)}")

    for msg in emails:
        print(f"\n    --- Письмо ---")
        print(f"    От:   {msg.get('mail_from', '?')}")
        print(f"    Тема: {msg.get('mail_subject', '?')}")

        full = requests.get(BASE_URL, params={
            "f":         "fetch_email",
            "email_id":  msg["mail_id"],
            "sid_token": mail.email_key,
        }, timeout=10).json()

        text = mail._extract_text(full.get("mail_body", ""))
        print(f"    Текст (первые 300 символов):\n    {text[:300]}")

        code = mail._extract_code(text)
        if code:
            print(f"    🔑 Найден код: {code}")
        else:
            print("    ℹ️  Код не найден в тексте.")

    print("\n" + "═" * 50)
    print("   Тест завершён.")
    print("═" * 50 + "\n")


if __name__ == "__main__":
    test_mailbox()