from cryptography.fernet import Fernet
import os

class EncryptionUtils:
    def __init__(self, key=None):
        if key is None:
            self.key_file = os.path.join(os.path.dirname(__file__), 'encryption.key')
            self.key = self.load_or_generate_key()
        else:
            self.key = key
        self.cipher_suite = Fernet(self.key)

    def load_or_generate_key(self):
        """Load the encryption key from a file, or generate a new one if it doesn't exist."""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.key_file), exist_ok=True)
        
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as key_file:
                return key_file.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as key_file:
                key_file.write(key)
            return key

    def encrypt(self, data):
        """Encrypt the provided data."""
        return self.cipher_suite.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data):
        """Decrypt the provided data."""
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
