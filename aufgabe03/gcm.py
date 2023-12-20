from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from .galois_arithmetics import Polynomial

def encrypt(key: bytes, nonce: bytes, associated_data: bytes, plaintext: bytes) -> (bytes, bytearray, bytes, bytes):    # (ciphertext, auth_tag, Y0, H)

    Y0 = nonce + bytes(3) + b"\x01"

    # 12 byte nonce and add 4 byte counter
    cipher = Cipher(algorithms.AES128(key), modes.CTR(nonce + bytes(4)))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(bytes(32) + plaintext) + encryptor.finalize()
    # Remove first padding block
    ciphertext = ciphertext[16:]

    # Don't need to XOR with plaintext as it is null and therefore nothing changes with the XOR operation
    Y0_encrypted = ciphertext[:16]

    # Now get the actual ciphertext
    ciphertext = ciphertext[16:]

    # Split ciphertext blocks
    BLOCK_LEN = 16
    ciphertext_blocks = split_bytes(ciphertext, BLOCK_LEN)

    # Split associated data blocks
    ad_blocks = split_bytes(associated_data, BLOCK_LEN)

    H = gen_auth_key(key)

    L = gen_L(associated_data, ciphertext)

    # Now take care of authentication via GHASH
    # Pad associated data and last ciphertext block

    if len(ciphertext_blocks) != 0:
        ciphertext_blocks[-1] = pad_bytes(ciphertext_blocks[-1], 16)

    if len(ad_blocks) != 0:
        ad_blocks[-1] = pad_bytes(ad_blocks[-1], 16)

    ghash = GHASH(H, ad_blocks, ciphertext_blocks, L)
    auth_tag = (Polynomial.from_bytes(ghash) ^ Polynomial.from_bytes(Y0_encrypted)).to_bytes()

    return ciphertext, auth_tag, Y0, H

def GHASH(key: bytes, ad_blocks: list, ciphertext_blocks: list, L: bytes) -> bytes:
    """This function assumes that associated_data and ciphertext_blocks are already padded"""

    key = Polynomial.from_bytes(key)
    block = Polynomial.zero()

    for ad_block in ad_blocks:
        block ^= Polynomial.from_bytes(ad_block)
        block *= key

    for ct_block in ciphertext_blocks:
        block ^= Polynomial.from_bytes(ct_block)
        block *= key

    block ^= Polynomial.from_bytes(L)
    block *= key
    
    return block.to_bytes()

def pad_bytes(block: bytes, length: int):
    return block + bytes(length - (len(block) % length) if (len(block) % length) > 0 else 0)

def pad_blocks(bytes_block: list, block_size) -> list:
    if len(bytes_block) != 0:
        bytes_block[-1] = pad_bytes(bytes_block[-1], block_size)

    return bytes_block

def gen_auth_key(key: bytes) -> bytes:

    cipher = Cipher(algorithms.AES128(key), modes.ECB())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(bytes(16)) + encryptor.finalize()

    return ciphertext

def gen_L(associated_data: bytes, ciphertext: bytes) -> bytes:
    return int.to_bytes(len(associated_data) * 8, 8, "big") + int.to_bytes(len(ciphertext) * 8, 8, "big") 

def split_bytes(data: bytes, block_size: int) -> list:
    return [data[i: i + block_size] for i in range(0, len(data), block_size)]