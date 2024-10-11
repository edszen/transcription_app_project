import unittest
from unittest.mock import patch, MagicMock
from src.api.openai_chat import ChatGPTIntegration

class TestChatGPTIntegration(unittest.TestCase):
    def setUp(self):
        self.chatgpt = ChatGPTIntegration()

    def test_initialization(self):
        self.assertIsNotNone(self.chatgpt)
        self.assertIsNone(self.chatgpt.client)

    @patch('src.api.openai_chat.OpenAI')
    def test_load_settings(self, mock_openai):
        mock_settings = MagicMock()
        mock_settings.value.return_value = "dummy_api_key"
        self.chatgpt.settings = mock_settings

        self.chatgpt.load_settings()

        self.assertIsNotNone(self.chatgpt.client)
        mock_openai.assert_called_once_with(api_key="dummy_api_key")

    @patch('src.api.openai_chat.ChatGPTIntegration.generate_response')
    def test_summarize_transcript(self, mock_generate):
        mock_generate.return_value = "Summary"
        result = self.chatgpt.summarize_transcript("Test transcript")
        self.assertEqual(result, "Summary")

    @patch('src.api.openai_chat.ChatGPTIntegration.generate_response')
    def test_analyze_topics(self, mock_generate):
        mock_generate.return_value = "Topics"
        result = self.chatgpt.analyze_topics("Test transcript")
        self.assertEqual(result, "Topics")

    @patch('src.api.openai_chat.ChatGPTIntegration.generate_response')
    def test_answer_question(self, mock_generate):
        mock_generate.return_value = "Answer"
        result = self.chatgpt.answer_question("Test transcript", "Test question")
        self.assertEqual(result, "Answer")

if __name__ == '__main__':
    unittest.main()