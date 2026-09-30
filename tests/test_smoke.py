import asyncio
import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

os.environ.setdefault("BOT_TOKEN", "123456789:SMOKE_TEST_TOKEN_123456789")
os.environ.setdefault("APP_ENV", "development")
os.environ.pop("RENDER_EXTERNAL_URL", None)

import bot
import handlers.start as start


class StructuralBotSmokeTests(unittest.TestCase):
    def test_all_core_modules_import_and_application_builds(self):
        app = bot.create_application()
        self.assertIsNotNone(app)
        self.assertGreaterEqual(len(app.handlers), 1)

    def test_start_new_user_flow(self):
        message = SimpleNamespace(reply_text=AsyncMock())
        user = SimpleNamespace(id=987654321, username="smoke", first_name="Smoke", last_name="Test")
        update = SimpleNamespace(effective_message=message, effective_user=user)
        context = SimpleNamespace(user_data={})

        with patch.object(start, "_is_existing_user", return_value=False),              patch.object(start, "_create_user_safely"):
            asyncio.run(start.start_command(update, context))

        self.assertTrue(context.user_data["is_new_user"])
        self.assertTrue(context.user_data["onboarding_required"])
        message.reply_text.assert_awaited_once()
        kwargs = message.reply_text.await_args.kwargs
        self.assertIsNotNone(kwargs["reply_markup"])

    def test_language_selection_flow(self):
        query = SimpleNamespace(
            data="language:fa",
            answer=AsyncMock(),
            message=SimpleNamespace(edit_text=AsyncMock()),
        )
        update = SimpleNamespace(callback_query=query, effective_user=SimpleNamespace(id=1))
        context = SimpleNamespace(user_data={})

        asyncio.run(start.language_callback(update, context))

        self.assertEqual(context.user_data["language"], "fa")
        query.answer.assert_awaited_once()
        query.message.edit_text.assert_awaited_once()

    def test_unit_selection_flow(self):
        query = SimpleNamespace(
            data="unit:SI",
            answer=AsyncMock(),
            message=SimpleNamespace(edit_text=AsyncMock()),
        )
        update = SimpleNamespace(
            callback_query=query,
            effective_user=SimpleNamespace(id=1),
        )
        context = SimpleNamespace(user_data={"language": "fa"})

        with patch.object(start, "update_user_preferences"):
            asyncio.run(start.unit_system_callback(update, context))

        self.assertEqual(context.user_data["unit_system"], "SI")
        self.assertFalse(context.user_data["onboarding_required"])
        query.answer.assert_awaited_once()
        self.assertGreaterEqual(query.message.edit_text.await_count, 1)


if __name__ == "__main__":
    unittest.main()
