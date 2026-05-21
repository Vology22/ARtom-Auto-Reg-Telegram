import re
import time
import requests


BASE_URL = "https://api.guerrillamail.com/ajax.php"


class MailService:
    def __init__(self):
        self.address   = None
        self.email_key = None
        self.seq       = 0

    # ── Создание ящика ────────────────────────────────────────

    def create_account(self) -> str:
        """Создаёт случайный ящик на guerrillamail. Возвращает email."""
        resp = requests.get(BASE_URL, params={"f": "get_email_address"}, timeout=15)
        data = resp.json()

        self.address   = data["email_addr"]
        self.email_key = data["sid_token"]
        self.seq       = 0

        print(f"    📬 Ящик создан: {self.address}")
        return self.address

    # ── Получение кода ────────────────────────────────────────

    def wait_for_code(self, timeout=120, check_interval=5) -> str | None:
        """Ждёт письма и возвращает 5-6-значный код. None если таймаут."""
        start = time.time()

        while time.time() - start < timeout:
            try:
                resp   = requests.get(BASE_URL, params={
                    "f":         "get_email_list",
                    "offset":    0,
                    "sid_token": self.email_key,
                    "seq":       self.seq,
                }, timeout=10)
                emails = resp.json().get("list", [])

                for email in emails:
                    full = requests.get(BASE_URL, params={
                        "f":         "fetch_email",
                        "email_id":  email["mail_id"],
                        "sid_token": self.email_key,
                    }, timeout=10).json()

                    text = self._extract_text(full.get("mail_body", ""))
                    code = self._extract_code(text)
                    if code:
                        return code

            except Exception as e:
                print(f"    ⚠️ Ошибка запроса: {e}")

            print("    ⏳ Ждём письма от Telegram...")
            time.sleep(check_interval)

        return None

    # ── Вспомогательные ──────────────────────────────────────

    def _extract_text(self, body) -> str:
        """Приводит mail_body к строке — guerrillamail иногда возвращает список."""
        if isinstance(body, list):
            return " ".join(body)
        return str(body) if body else ""

    def _extract_code(self, text: str) -> str | None:
        """Вытаскивает 5 или 6-значный код из текста письма."""
        match = re.search(r'\b(\d{5,6})\b', text)
        return match.group(1) if match else None