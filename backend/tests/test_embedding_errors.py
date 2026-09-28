import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from google.genai.errors import ClientError, ServerError
import main


class EmbeddingErrorTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app)

    def test_upload_provider_errors_are_readable_and_leave_no_document(self):
        for error_type, code, expected in (
            (ClientError, 429, 429),
            (ServerError, 503, 503),
            (ClientError, 403, 502),
        ):
            with self.subTest(code=code):
                error = error_type(code, {"error": {"message": "private provider details"}})
                with patch.object(main, "extract_pages_from_pdf", return_value=[{"page_number": 1, "text": "Example"}]) as extract, patch.object(main, "get_embeddings_for_chunks", side_effect=error), patch.object(main, "create_document") as create, patch.object(main, "insert_document_chunks") as insert:
                    response = self.client.post("/api/upload-pdf", files={"file": ("example.pdf", b"mock PDF", "application/pdf")})
                self.assertEqual(response.status_code, expected)
                self.assertIn("embedding", response.json()["detail"])
                self.assertNotIn("private provider details", response.text)
                create.assert_not_called()
                insert.assert_not_called()
                self.assertFalse(os.path.exists(extract.call_args.args[0]))

    def test_document_question_quota_error_does_not_save_failed_turn(self):
        error = ClientError(429, {"error": {"message": "Resource exhausted"}})
        with patch.object(main, "load_history", return_value=[]), patch("app.services.rag_service.get_embedding", side_effect=error), patch.object(main, "save_history") as save:
            response = self.client.post("/api/chat", json={"session_id": "test", "message": "Summarize", "document_id": 7})
        self.assertEqual(response.status_code, 429)
        self.assertIn("quota", response.json()["detail"])
        save.assert_not_called()
