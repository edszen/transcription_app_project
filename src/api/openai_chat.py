from openai import OpenAI
from src import config
from PyQt5.QtCore import QSettings
import logging

class ChatGPTIntegration:
    def __init__(self):
        self.settings = QSettings("SZ Apps", "GatherScribe")
        self.client = None
        self.model = None
        self.logger = logging.getLogger(__name__)
        self.load_settings()

    def load_settings(self):
        api_key = self.settings.value("openai_api_key", "")
        if api_key:
            self.client = OpenAI(api_key=api_key)
            self.model = self.settings.value("openai_model", config.CHATGPT_MODEL)
            self.logger.info(f"ChatGPT settings loaded. Using model: {self.model}")
        else:
            self.logger.warning("No OpenAI API key found in settings.")

    def generate_response(self, prompt, model=None):
        if not self.client:
            self.logger.error("OpenAI API key not set. Please check your settings.")
            return "Error: OpenAI API key not set. Please check your settings."

        selected_model = model or self.model
        try:
            response = self.client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant analyzing meeting transcriptions."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return f"An error occurred: {str(e)}"

    def summarize_transcript(self, transcript, model=None):
        prompt = f"Summarize the following transcript:\n\n{transcript}"
        return self.generate_response(prompt, model)

    def analyze_topics(self, transcript, model=None):
        prompt = f"Identify the main topics discussed in this transcript:\n\n{transcript}"
        return self.generate_response(prompt, model)

    def answer_question(self, transcript, question, model=None):
        prompt = f"Based on the following transcript, answer this question: {question}\n\nTranscript:\n{transcript}"
        return self.generate_response(prompt, model)