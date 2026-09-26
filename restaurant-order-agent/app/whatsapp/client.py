from __future__ import annotations

import httpx


class WhatsAppClient:
    """Sends outgoing messages through the WhatsApp Cloud API.

    Docs: https://developers.facebook.com/docs/whatsapp/cloud-api/reference/messages
    """

    def __init__(self, access_token: str, phone_number_id: str, api_version: str = "v20.0"):
        self._access_token = access_token
        self._phone_number_id = phone_number_id
        self._base_url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"

    def send_text_message(self, to: str, body: str) -> None:
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": body},
        }
        headers = {"Authorization": f"Bearer {self._access_token}"}
        response = httpx.post(self._base_url, json=payload, headers=headers, timeout=10.0)
        response.raise_for_status()
