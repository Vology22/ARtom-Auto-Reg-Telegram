import time
import requests
import config.config as cfg


class SmsService:
    def __init__(self,
                 api_key=cfg.API_SMS,
                 base_url="https://hero-sms.com/stubs/handler_api.php?action="):
        self.api_key = api_key
        self.base_url = base_url
        self.service = "tg"

    def _get(self, action, **kwargs):
        params = {"api_key": self.api_key}
        params.update(kwargs)
        try:
            response = requests.get(self.base_url + action, params=params, timeout=15)
            return response.text
        except requests.RequestException:
            return "ERROR_CONNECTION"

    def get_balance(self) -> float:
        result = self._get("getBalance")
        if "ACCESS_BALANCE" in result:
            return float(result.split(":")[1])
        return 0.0

    def get_number(self, country_code):
        result = self._get("getNumber", service=self.service, country=country_code)
        if "ACCESS_NUMBER" in result:
            _, order_id, phone = result.split(":")
            return order_id, phone
        return None, result

    def set_status(self, order_id, status):
        return self._get("setStatus", id=order_id, status=status)

    def wait_for_code(self, order_id, timeout=120, check_interval=5):
        start_time = time.time()
        while time.time() - start_time < timeout:
            result = self._get("getStatus", id=order_id)
            if "STATUS_OK" in result:
                return result.split(":")[1]
            elif "STATUS_CANCEL" in result:
                return "CANCELLED"
            time.sleep(check_interval)
        return "TIMEOUT"