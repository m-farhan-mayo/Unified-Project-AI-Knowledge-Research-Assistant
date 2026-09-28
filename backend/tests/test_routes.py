import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
import main


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app)

    def test_document_chat_uses_rag_and_saves_history(self):
        result = {"answer": "Document answer", "sources": []}
        with patch.object(main, "load_history", return_value=[]), patch.object(main, "save_history") as save, patch.object(main, "answer_with_rag", return_value=result) as rag, patch.object(main, "ask_llm_with_tools") as normal:
            response = self.client.post("/api/chat", json={"session_id": "test", "message": "Question", "document_id": 7})
        self.assertEqual(response.status_code, 200)
        rag.assert_called_once_with(question="Question", document_id=7, history=[])
        normal.assert_not_called()
        self.assertEqual(save.call_args.args[1][-1]["content"], "Document answer")

    def test_normal_chat_does_not_automatically_email(self):
        with patch.object(main, "load_history", return_value=[]), patch.object(main, "save_history"), patch.object(main, "ask_llm_with_tools", return_value={"answer": "Hello", "sources": []}), patch("app.services.llm_service.send_email") as email:
            response = self.client.post("/api/chat", json={"session_id": "test", "message": "Hello"})
        self.assertEqual(response.status_code, 200)
        email.assert_not_called()

    def test_invalid_pdf_returns_client_error(self):
        response = self.client.post("/api/upload-pdf", files={"file": ("invalid.pdf", b"not a PDF", "application/pdf")})
        self.assertEqual(response.status_code, 400)

    def test_health_and_public_routes(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        self.assertEqual(set(main.app.openapi()["paths"]), {
            "/", "/api/health", "/api/chat", "/api/upload-pdf",
        })

    def test_development_routes_are_removed(self):
        for route in (
            "test", "config-test", "llm-test", "embedding-test", "db-test",
            "vector-insert-test", "chunks-test", "vector-search-test",
            "chunk-test", "chunk-embedding-test", "rag-test", "history-test",
            "tool-test", "search-test", "research-test",
        ):
            with self.subTest(route=route):
                self.assertEqual(self.client.get(f"/api/{route}").status_code, 404)


if __name__ == "__main__":
    unittest.main()
