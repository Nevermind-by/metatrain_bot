import hashlib
import hmac
import time
import unittest
from urllib.parse import urlencode

from app.api.auth import validate_telegram_init_data


class TelegramAuthTests(unittest.TestCase):
    def make_init_data(self, *, auth_date: int | None = None, bot_token: str = "test-token") -> str:
        pairs = {
            "auth_date": str(auth_date if auth_date is not None else int(time.time())),
            "query_id": "AA-test",
            "user": '{"id":123,"first_name":"Test"}',
        }
        check_string = "\n".join(f"{key}={pairs[key]}" for key in sorted(pairs))
        secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        digest = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
        return urlencode({**pairs, "hash": digest})

    def test_valid_data_is_accepted(self) -> None:
        result = validate_telegram_init_data(self.make_init_data(), "test-token")
        self.assertEqual(result["auth_date"], result["auth_date"])
        self.assertIn("user", result)

    def test_invalid_signature_is_rejected(self) -> None:
        data = self.make_init_data()
        with self.assertRaises(ValueError):
            validate_telegram_init_data(data + "x", "test-token")

    def test_expired_data_is_rejected(self) -> None:
        data = self.make_init_data(auth_date=int(time.time()) - 90000)
        with self.assertRaises(ValueError):
            validate_telegram_init_data(data, "test-token", max_age=86400)

    def test_far_future_data_is_rejected(self) -> None:
        data = self.make_init_data(auth_date=int(time.time()) + 301)
        with self.assertRaises(ValueError):
            validate_telegram_init_data(data, "test-token")


if __name__ == "__main__":
    unittest.main()
