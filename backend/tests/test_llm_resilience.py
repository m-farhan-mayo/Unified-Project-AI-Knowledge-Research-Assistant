import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import httpx
from openai import InternalServerError, AuthenticationError
from fastapi.testclient import TestClient
import main
from app.services import llm_service


def provider_error(error_class=InternalServerError, status=503):
    return error_class("provider error", response=httpx.Response(status, request=httpx.Request("POST", "https://example.test")), body=None)


class ResilienceTests(unittest.TestCase):
    def test_chat_and_rag_outages_return_503_without_saving_history(self):
        client = TestClient(main.app)
        for document_id, target in ((None, "ask_llm_with_tools"), (7, "answer_with_rag")):
            with self.subTest(document_id=document_id), patch.object(main, "load_history", return_value=[]), patch.object(main, "save_history") as save, patch.object(main, target, side_effect=provider_error()):
                response = client.post("/api/chat", json={"session_id": "test", "message": "Hello", "document_id": document_id})
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.headers["retry-after"], "30")
                self.assertIn("high demand", response.json()["detail"])
                save.assert_not_called()

    @patch.dict(os.environ, {"GEMINI_MODEL": "primary", "GEMINI_FALLBACK_MODEL": "fallback"})
    def test_both_generation_paths_use_fallback(self):
        for generate, prompt in ((llm_service.ask_llm, "Hello"), (llm_service.ask_llm_with_tools, "Hello")):
            with self.subTest(generate=generate.__name__):
                client = Mock()
                result = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Recovered", tool_calls=None))])
                client.chat.completions.create.side_effect = [provider_error(), result]
                with patch.object(llm_service, "get_client", return_value=client):
                    answer = generate(prompt)
                self.assertEqual(answer if isinstance(answer, str) else answer["answer"], "Recovered")
                calls = client.chat.completions.create.call_args_list
                self.assertEqual([call.kwargs["model"] for call in calls], ["primary", "fallback"])
                self.assertEqual(calls[0].kwargs["messages"], calls[1].kwargs["messages"])

    @patch.dict(os.environ, {"GEMINI_MODEL": "primary", "GEMINI_FALLBACK_MODEL": "fallback"})
    def test_auth_errors_do_not_trigger_fallback(self):
        client = Mock()
        client.chat.completions.create.side_effect = provider_error(AuthenticationError, 401)
        with self.assertRaises(AuthenticationError):
            llm_service.create_completion(client, messages=[])
        self.assertEqual(client.chat.completions.create.call_count, 1)

    @patch.dict(os.environ, {"GEMINI_FALLBACK_MODEL": ""})
    def test_no_fallback_preserves_provider_error(self):
        client = Mock()
        client.chat.completions.create.side_effect = provider_error()
        with self.assertRaises(InternalServerError):
            llm_service.create_completion(client, messages=[])
        self.assertEqual(client.chat.completions.create.call_count, 1)
