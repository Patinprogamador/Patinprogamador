from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from app.agent.chat_agent import ChatAgent
from app.agent.gemini_client import GeminiLLMClient
from app.config import Settings, get_settings
from app.domain.menu import Menu
from app.domain.orders import OrderStore
from app.domain.restaurant import RestaurantInfo, load_faq
from app.session_store import SessionStore
from app.whatsapp.client import WhatsAppClient
from app.whatsapp.webhook import parse_incoming_messages, verify_webhook


def create_app(
    settings: Settings,
    chat_agent: ChatAgent | None = None,
    whatsapp_client: WhatsAppClient | None = None,
) -> FastAPI:
    if chat_agent is None:
        menu = Menu.from_json_file(settings.resolved_menu_path())
        faq = load_faq(settings.resolved_faq_path())
        restaurant = RestaurantInfo(
            name=settings.restaurant_name,
            address=settings.restaurant_address,
            phone=settings.restaurant_phone,
        )
        order_store = OrderStore(settings.resolved_database_path())
        llm_client = GeminiLLMClient(settings.gemini_api_key, settings.gemini_model)
        chat_agent = ChatAgent(
            llm_client=llm_client,
            menu=menu,
            faq=faq,
            restaurant=restaurant,
            order_store=order_store,
            session_store=SessionStore(),
        )

    if whatsapp_client is None:
        whatsapp_client = WhatsAppClient(
            access_token=settings.whatsapp_access_token,
            phone_number_id=settings.whatsapp_phone_number_id,
            api_version=settings.whatsapp_api_version,
        )

    app = FastAPI(title="Restaurant Order Agent")
    app.state.settings = settings
    app.state.chat_agent = chat_agent
    app.state.whatsapp_client = whatsapp_client

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/webhook")
    def verify(request: Request):
        result = verify_webhook(
            mode=request.query_params.get("hub.mode"),
            token=request.query_params.get("hub.verify_token"),
            challenge=request.query_params.get("hub.challenge"),
            expected_token=app.state.settings.whatsapp_verify_token,
        )
        if result is None:
            raise HTTPException(status_code=403, detail="Verification failed")
        return PlainTextResponse(result)

    @app.post("/webhook")
    async def receive(request: Request):
        payload = await request.json()
        for message in parse_incoming_messages(payload):
            reply = app.state.chat_agent.handle_message(message.from_number, message.text)
            app.state.whatsapp_client.send_text_message(message.from_number, reply)
        # Meta requires a fast 200 OK regardless of what we did with the message.
        return JSONResponse({"status": "ok"})

    return app


app = create_app(get_settings())
