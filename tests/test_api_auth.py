import json
import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app.api.router import current_telegram_id


class ApiAuthTests(unittest.TestCase):
    @patch.dict(os.environ, {"BOT_TOKEN": "test-token"}, clear=False)
    @patch("app.api.router.validate_telegram_init_data")
    def test_current_telegram_id_extracts_authenticated_user(self, validate):
        validate.return_value = {"user": json.dumps({"id": 987654321})}
        self.assertEqual(current_telegram_id("signed-data"), 987654321)
        validate.assert_called_once_with("signed-data", "test-token")

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_bot_token_returns_server_error(self):
        with self.assertRaises(HTTPException) as ctx:
            current_telegram_id("signed-data")
        self.assertEqual(ctx.exception.status_code, 500)

    @patch.dict(os.environ, {"BOT_TOKEN": "test-token"}, clear=False)
    @patch("app.api.router.validate_telegram_init_data")
    def test_invalid_telegram_data_returns_unauthorized(self, validate):
        validate.side_effect = ValueError("bad signature")
        with self.assertRaises(HTTPException) as ctx:
            current_telegram_id("bad-data")
        self.assertEqual(ctx.exception.status_code, 401)

    @patch.dict(os.environ, {"BOT_TOKEN": "test-token"}, clear=False)
    @patch("app.api.router.validate_telegram_init_data")
    def test_malformed_user_returns_unauthorized(self, validate):
        validate.return_value = {"user": "not-json"}
        with self.assertRaises(HTTPException) as ctx:
            current_telegram_id("signed-data")
        self.assertEqual(ctx.exception.status_code, 401)

    @patch.dict(os.environ, {"BOT_TOKEN": "test-token"}, clear=False)
    @patch("app.api.router.validate_telegram_init_data")
    def test_missing_user_id_returns_unauthorized(self, validate):
        validate.return_value = {"user": json.dumps({"first_name": "Test"})}
        with self.assertRaises(HTTPException) as ctx:
            current_telegram_id("signed-data")
        self.assertEqual(ctx.exception.status_code, 401)
