import asyncio
import threading
from types import SimpleNamespace

import bot
from pdf_generator import _sanitize_filename


def test_sanitize_filename_removes_path_separators():
    assert _sanitize_filename("Vesterbro / Kongens Enghave") == (
        "Vesterbro_Kongens_Enghave"
    )


def test_generate_executive_pdf_runs_outside_event_loop_thread(monkeypatch, tmp_path):
    event_loop_thread = threading.get_ident()
    worker_thread = None

    def fake_generate(zone_data, filename):
        nonlocal worker_thread
        worker_thread = threading.get_ident()
        output = tmp_path / "report.pdf"
        output.write_bytes(b"%PDF-1.4")
        return str(output)

    monkeypatch.setattr(bot, "generate_executive_pdf", fake_generate)

    result = asyncio.run(
        bot._generate_executive_pdf({"name": "Nørrebro"}, str(tmp_path / "report.pdf"))
    )

    assert result.endswith("report.pdf")
    assert worker_thread is not None
    assert worker_thread != event_loop_thread


def test_receive_email_refuses_to_store_without_consent(monkeypatch):
    messages = []

    class FakeMessage:
        text = "user@example.com"

        async def reply_text(self, text, **_kwargs):
            messages.append(text)

    rpc_called = False

    class FakeSupabase:
        def rpc(self, *_args, **_kwargs):
            nonlocal rpc_called
            rpc_called = True
            raise AssertionError("RPC must not be called without consent")

    update = SimpleNamespace(
        message=FakeMessage(),
        effective_user=SimpleNamespace(id=123, username="test_user"),
    )
    context = SimpleNamespace(
        user_data={
            "district": "Nørrebro",
            "b_type": "curated_vintage",
            "full_name": "Test User",
        }
    )

    monkeypatch.setattr(bot, "supabase", FakeSupabase())
    result = asyncio.run(bot.receive_email(update, context))

    assert result == bot.ConversationHandler.END
    assert not rpc_called
    assert "consenso" in messages[0].lower()
