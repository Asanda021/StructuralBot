# StructuralBot

Telegram-based structural engineering assistant for calculations, reinforcement/BBS and cut-list workflows, quantities, reports, billing infrastructure, and a future AI assistant.

## Architecture

- **Telegram layer:** `bot.py` and `handlers/`
- **Engineering engine:** `core/` and `codes/`
- **AI layer:** `ai/`
- **Billing layer:** `billing/`
- **Persistence:** SQLite via `database.py`
- **Tests:** `tests/`
- **CI:** GitHub Actions under `.github/workflows/`

## Security model

- The Telegram **bot token is loaded from environment variables** and is not intended to be committed.
- Telegram's authenticated user identity is represented internally by the Telegram user ID stored in the `users` table.
- Project records are linked to users through foreign keys.
- AI/payment credentials belong in environment variables, not handlers or source files.
- Production startup requires `SECRET_KEY` to be configured.
- SQLite foreign-key enforcement and a busy timeout are enabled for every connection.
- Webhook payload hashes are used only for idempotency/deduplication; they are **not** a replacement for provider signature verification.

## Configuration

Copy `.env.example` to `.env` and set the required values. Never commit `.env`.

For production, set:

- `APP_ENV=production`
- `BOT_TOKEN`
- `SECRET_KEY`
- credentials for any enabled AI/payment provider

## Development

Install dependencies:

```bash
pip install -r requirements.txt
pip install pytest pytest-asyncio
```

Run tests:

```bash
pytest -ra
```

Compile-check the project:

```bash
python -m compileall -q .
```

## Engineering boundary

Deterministic structural calculations and code compliance remain the responsibility of the calculation engine and configured design-code layer. The AI layer is an assistant and should not silently replace engineering calculations or code checks.
