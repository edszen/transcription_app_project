from openai import OpenAI
from src import config
from PyQt5.QtCore import QSettings, QObject, pyqtSignal
import logging

class ChatGPTIntegration(QObject):
    response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__() # Initialize the QObject
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
            self.error_occurred.emit("No OpenAI API key found in settings.")

    def generate_response(self, prompt, model=None):
        if not self.client:
            error_message = "OpenAI API key not set. Please check your settings."
            self.logger.error(error_message)
            self.error_occurred.emit(error_message)
            return error_message

        selected_model = model or self.model
        try:
            response = self.client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant analyzing meeting transcriptions."},
                    {"role": "user", "content": prompt}
                ]
            )
            response_content = response.choices[0].message.content
            self.response_received.emit(response_content)
            return response_content
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            self.logger.error(f"Error generating response: {str(e)}")
            self.error_occurred.emit(error_message)
            return error_message

    def summarize_transcript(self, transcript, model=None):
        prompt = f"Summarize the following transcript:\n\n{transcript}"
        return self.generate_response(prompt, model)

    def analyze_topics(self, transcript, model=None):
        prompt = f"Identify the main topics discussed in this transcript:\n\n{transcript}"
        return self.generate_response(prompt, model)

    def answer_question(self, transcript, question, model=None):
        prompt = f"Based on the following transcript, answer this question: {question}\n\nTranscript:\n{transcript}"
        return self.generate_response(prompt, model)