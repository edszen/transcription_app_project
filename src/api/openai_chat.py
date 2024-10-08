from openai import OpenAI
from src import config
from PyQt5.QtCore import QSettings
import time


class ChatGPTIntegration:
    def __init__(self):
        self.settings = QSettings("SZ Apps", "AudioTranscriptionApp")
        self.client = OpenAI(api_key=self.settings.value("openai_api_key", ""))
        self.load_settings()
        
    def load_settings(self):
        self.client.api_key = self.settings.value("openai_api_key", "")
        self.model = self.settings.value("openai_model", config.CHATGPT_MODEL)

    def generate_response(self, prompt, model=None):
        selected_model = model or self.model
        try:
            response = self.client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant analyzing meetings transcriptions."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
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