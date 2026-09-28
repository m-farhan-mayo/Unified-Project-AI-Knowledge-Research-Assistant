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
        with patch.object(main, "load_history", return_value=[]), patch.object(main, "save_history"), patch.object(main, "ask_llm_with_tools", return_value={"answer": "Hello", "sources": []}), patch.object(main, "send_email") as email:
            response = self.client.post("/api/chat", json={"session_id": "test", "message": "Hello"})
        self.assertEqual(response.status_code, 200)
        email.assert_not_called()

    def test_rag_diagnostic_requires_document(self):
        self.assertEqual(self.client.get("/api/rag-test").status_code, 422)
        with patch.object(main, "answer_with_rag", return_value={"answer": "Found", "sources": []}) as rag:
            self.assertEqual(self.client.get("/api/rag-test?document_id=7").status_code, 200)
        self.assertEqual(rag.call_args.kwargs["document_id"], 7)

    def test_vector_insert_uses_current_schema(self):
        with patch.object(main, "get_embedding", return_value=[0.1]), patch.object(main, "create_document", return_value=7), patch.object(main, "insert_document_chunks") as insert:
            response = self.client.get("/api/vector-insert-test")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(insert.call_args.args[0], 7)

    def test_invalid_pdf_returns_client_error(self):
        response = self.client.post("/api/upload-pdf", files={"file": ("invalid.pdf", b"not a PDF", "application/pdf")})
        self.assertEqual(response.status_code, 400)

    def test_missing_sample_is_not_server_error(self):
        with patch.object(main.os.path, "isfile", return_value=False):
            for route in ("/api/chunk-test", "/api/chunk-embedding-test"):
                self.assertEqual(self.client.get(route).status_code, 404)


if __name__ == "__main__":
    unittest.main()
