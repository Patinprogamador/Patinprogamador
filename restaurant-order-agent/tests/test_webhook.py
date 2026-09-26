from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.whatsapp.webhook import parse_incoming_messages, verify_webhook


def test_verify_webhook_returns_challenge_on_match():
    assert verify_webhook("subscribe", "secret", "12345", "secret") == "12345"


def test_verify_webhook_rejects_wrong_token():
    assert verify_webhook("subscribe", "wrong", "12345", "secret") is None


def test_verify_webhook_rejects_wrong_mode():
    assert verify_webhook("unsubscribe", "secret", "12345", "secret") is None


def test_parse_incoming_messages_extracts_text():
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "5511999999999",
                                    "id": "wamid.abc",
                                    "type": "text",
                                    "text": {"body": "Oi, quero um cardápio"},
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    messages = parse_incoming_messages(payload)

    assert len(messages) == 1
    assert messages[0].from_number == "5511999999999"
    assert messages[0].text == "Oi, quero um cardápio"


def test_parse_incoming_messages_ignores_status_updates():
    payload = {"entry": [{"changes": [{"value": {"statuses": [{"status": "delivered"}]}}]}]}
    assert parse_incoming_messages(payload) == []


class StubChatAgent:
    def __init__(self, reply: str):
        self.reply = reply
        self.calls: list[tuple[str, str]] = []

    def handle_message(self, customer_phone: str, user_text: str) -> str:
        self.calls.append((customer_phone, user_text))
        return self.reply


class RecordingWhatsAppClient:
    def __init__(self):
        self.sent: list[tuple[str, str]] = []

    def send_text_message(self, to: str, body: str) -> None:
        self.sent.append((to, body))


def _client(verify_token: str, chat_agent, whatsapp_client) -> TestClient:
    settings = Settings(whatsapp_verify_token=verify_token)
    app = create_app(settings, chat_agent=chat_agent, whatsapp_client=whatsapp_client)
    return TestClient(app)


def test_webhook_get_verification_success():
    client = _client("secret123", StubChatAgent("ok"), RecordingWhatsAppClient())

    response = client.get(
        "/webhook",
        params={"hub.mode": "subscribe", "hub.verify_token": "secret123", "hub.challenge": "999"},
    )

    assert response.status_code == 200
    assert response.text == "999"


def test_webhook_get_verification_failure():
    client = _client("secret123", StubChatAgent("ok"), RecordingWhatsAppClient())

    response = client.get(
        "/webhook",
        params={"hub.mode": "subscribe", "hub.verify_token": "wrong", "hub.challenge": "999"},
    )

    assert response.status_code == 403


def test_webhook_post_routes_message_to_agent_and_sends_reply():
    chat_agent = StubChatAgent("Olá! Aqui está nosso cardápio...")
    whatsapp_client = RecordingWhatsAppClient()
    client = _client("secret123", chat_agent, whatsapp_client)

    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "5511999999999",
                                    "id": "wamid.abc",
                                    "type": "text",
                                    "text": {"body": "Oi"},
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    response = client.post("/webhook", json=payload)

    assert response.status_code == 200
    assert chat_agent.calls == [("5511999999999", "Oi")]
    assert whatsapp_client.sent == [("5511999999999", "Olá! Aqui está nosso cardápio...")]
