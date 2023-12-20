# Simple script to encrypt test data with which the padding oracle can be tested
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

key = "1234567890abcdef".encode()
iv = "0987654321qwer\x33\30".encode()

cipher = Cipher(algorithms.AES128(key), modes.CBC(iv))
encryptor = cipher.encryptor()
ciphertext = encryptor.update("secret_message12".encode()) + encryptor.finalize()
print(base64.b64encode(ciphertext).decode())