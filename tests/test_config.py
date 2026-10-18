import os
import pytest
from app.config import Settings, ConfigError

def valid(monkeypatch):
    values = {"BOT_TOKEN":"123456:abcDEF", "ADMIN_TELEGRAM_ID":"123456789", "WEBHOOK_URL":"https://example.onrender.com", "WEBHOOK_SECRET":"a"*32}
    for k,v in values.items(): monkeypatch.setenv(k,v)

def test_config_parses(monkeypatch):
    valid(monkeypatch)
    s = Settings.from_env()
    assert s.admin_id == 123456789 and s.processing_timeout == 600

def test_missing_token_fails(monkeypatch):
    valid(monkeypatch); monkeypatch.delenv("BOT_TOKEN")
    with pytest.raises(ConfigError): Settings.from_env()

def test_bad_admin_fails(monkeypatch):
    valid(monkeypatch); monkeypatch.setenv("ADMIN_TELEGRAM_ID", "not-an-id")
    with pytest.raises(ConfigError): Settings.from_env()

def test_short_secret_fails(monkeypatch):
    valid(monkeypatch); monkeypatch.setenv("WEBHOOK_SECRET", "short")
    with pytest.raises(ConfigError): Settings.from_env()
