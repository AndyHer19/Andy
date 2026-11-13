"""Cliente mínimo de la Bot API de Telegram (long polling)."""

import logging

import requests

log = logging.getLogger(__name__)


class Telegram:
    def __init__(self, token: str, timeout: float = 30.0):
        self.base = f"https://api.telegram.org/bot{token}"
        self.timeout = timeout
        self.session = requests.Session()
        self.offset = 0

    def _call(self, method: str, **params):
        r = self.session.post(f"{self.base}/{method}", json=params, timeout=self.timeout + 10)
        data = r.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram {method} falló: {data.get('description')}")
        return data["result"]

    def send(self, chat_id: str | int, text: str) -> None:
        # Telegram limita los mensajes a 4096 caracteres
        for i in range(0, len(text), 4000):
            try:
                self._call("sendMessage", chat_id=chat_id, text=text[i : i + 4000],
                           parse_mode="HTML", disable_web_page_preview=True)
            except Exception as e:  # no tumbar el bot por un mensaje fallido
                log.error("No se pudo enviar mensaje: %s", e)

    def get_updates(self, timeout: int = 20) -> list[dict]:
        updates = self._call("getUpdates", offset=self.offset, timeout=timeout, allowed_updates=["message"])
        if updates:
            self.offset = updates[-1]["update_id"] + 1
        return updates

    def set_commands(self, commands: list[tuple[str, str]]) -> None:
        try:
            self._call("setMyCommands", commands=[{"command": c, "description": d} for c, d in commands])
        except Exception as e:
            log.warning("No se pudo registrar el menú de comandos: %s", e)
