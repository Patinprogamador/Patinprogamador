# Restaurant Order Agent

Agente de WhatsApp (Google Gemini) para um restaurante: monta pedidos a
partir do cardápio, responde dúvidas frequentes e informa o status de
pedidos já feitos.

MVP feito para prototipar rápido: pode ser testado inteiramente pelo
terminal (`scripts/chat_cli.py`) ou por testes automatizados (`pytest`) sem
nenhuma credencial da Meta — o WhatsApp entra só quando você quiser ligar de
verdade.

## Arquitetura

```
app/
  domain/
    menu.py         # cardápio (carregado de data/menu.json)
    restaurant.py    # dados do restaurante + FAQ (data/faq.json)
    orders.py         # pedidos, status, persistência em SQLite
  agent/
    llm_types.py      # tipos internos (ModelTurn, TextBlock, ToolUseBlock, Message)
    gemini_client.py  # wrapper do SDK do Gemini
    tools.py           # ferramentas que o modelo pode chamar (carrinho, pedido, status)
    prompts.py          # prompt de sistema (cardápio + FAQ + regras)
    chat_agent.py         # laço de tool-use: recebe msg -> chama o Gemini -> executa tools -> responde
  whatsapp/
    client.py        # envia mensagens via WhatsApp Cloud API
    webhook.py         # valida o webhook e extrai mensagens recebidas
  session_store.py   # carrinho + histórico de conversa por cliente (em memória)
  main.py               # app FastAPI (rotas /webhook e /health)
scripts/chat_cli.py     # chat local pelo terminal, sem precisar de WhatsApp
data/menu.json, data/faq.json   # dados de exemplo — troque pelos do seu restaurante
tests/                            # testes offline, com um cliente LLM falso/scriptado
```

O modelo decide quando chamar cada ferramenta (`add_item_to_cart`,
`remove_item_from_cart`, `view_cart`, `confirm_order`,
`check_order_status`); o código Python só executa o que foi pedido e nunca
deixa o modelo inventar preço, item ou pedido.

A camada `app/agent/llm_types.py` (`LLMClient`, `ModelTurn`, `Message`) é
independente do provedor — hoje ela é implementada por `gemini_client.py`,
mas o resto do agente (tools, prompts, loop de conversa, testes) não sabe
nem se importa qual provedor está por trás. Trocar de LLM no futuro é só
escrever um novo `*_client.py`.

## Configuração

1. Crie o ambiente virtual e instale as dependências:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Copie `.env.example` para `.env` e preencha:

   ```bash
   cp .env.example .env
   ```

   - `GEMINI_API_KEY`: gere de graça em https://aistudio.google.com/apikey
   - `RESTAURANT_NAME` / `RESTAURANT_ADDRESS` / `RESTAURANT_PHONE`: dados do seu restaurante
   - Edite `data/menu.json` e `data/faq.json` com o cardápio e as perguntas frequentes reais
   - As variáveis `WHATSAPP_*` só são necessárias quando for ligar o WhatsApp de verdade (passo mais abaixo)

## Testar sem WhatsApp

**Testes automatizados** (não precisam de nenhuma chave, usam um cliente LLM falso/scriptado):

```bash
pytest
```

**Conversa manual pelo terminal** (precisa de `GEMINI_API_KEY` real — de graça em https://aistudio.google.com/apikey):

```bash
python scripts/chat_cli.py
```

Isso já exercita o fluxo completo: montar carrinho, confirmar pedido
(gravado em SQLite, por padrão em `data/orders.db`) e consultar status.

## Ligando ao WhatsApp de verdade (WhatsApp Cloud API)

1. Crie um app em https://developers.facebook.com/apps e adicione o produto
   **WhatsApp**. A Meta fornece um número de teste grátis.
2. Em **WhatsApp > Configuração da API**, copie o **Temporary access token**
   e o **Phone number ID** para `WHATSAPP_ACCESS_TOKEN` e
   `WHATSAPP_PHONE_NUMBER_ID` no `.env`. (Para produção, gere um token
   permanente com um usuário de sistema.)
3. Escolha um valor qualquer para `WHATSAPP_VERIFY_TOKEN` no `.env` — ele só
   precisa bater com o que você configurar no passo 5.
4. Rode o servidor localmente e exponha com um túnel (ex: `ngrok`), já que a
   Meta precisa de uma URL pública HTTPS para o webhook:

   ```bash
   uvicorn app.main:app --reload --port 8000
   ngrok http 8000
   ```

5. Em **WhatsApp > Configuração > Webhook**, cadastre:
   - Callback URL: `https://<sua-url-ngrok>/webhook`
   - Verify token: o mesmo valor de `WHATSAPP_VERIFY_TOKEN`
   - Inscreva-se no campo `messages`
6. Envie uma mensagem do número de teste (cadastrado como destinatário
   autorizado no painel da Meta) para o número do WhatsApp Cloud API. A
   mensagem chega em `POST /webhook`, o agente processa e a resposta volta
   pelo `WhatsAppClient`.

## Limitações conhecidas do MVP (próximos passos naturais)

- Estado de conversa (carrinho + histórico) fica em memória por processo —
  ótimo para um único worker; para múltiplos workers/produção, trocar por
  um store compartilhado (ex: Redis).
- Só mensagens de texto são tratadas; imagens/áudio são ignorados.
- Não há painel para a cozinha atualizar o status do pedido — hoje isso
  seria feito chamando `OrderStore.update_status` diretamente; um próximo
  passo natural é uma tela simples (ou endpoint) para a equipe do
  restaurante.
- Token de acesso "temporário" do WhatsApp expira em 24h — para produção,
  gerar um token permanente de usuário de sistema no Meta Business Manager.
- O tier gratuito do Gemini tem limite de requisições por minuto/dia; para
  um restaurante com volume real de pedidos, sua conta do Google AI Studio
  precisará ser migrada para o tier pago (ainda bem mais barato que a maioria
  das alternativas).
