from cryptography.fernet import Fernet
import os

class EncryptionUtils:
       def __init__(self):
           self.key_file = 'encryption.key'
           self.key = self.load_or_generate_key()
           self.cipher_suite = Fernet(self.key)

       def load_or_generate_key(self):
           if os.path.exists(self.key_file):
               with open(self.key_file, 'rb') as key_file:
                   return key_file.read()
           else:
               key = Fernet.generate_key()
               with open(self.key_file, 'wb') as key_file:
                   key_file.write(key)
               return key

       def encrypt(self, data):
           return self.cipher_suite.encrypt(data.encode()).decode()

       def decrypt(self, encrypted_data):
           return self.cipher_suite.decrypt(encrypted_data.encode()).decode()