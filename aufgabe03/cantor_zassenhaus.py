from .galois_arithmetics import CZPolynomial, Polynomial, gen_empty_poly_list
from . import gcm
import random
import sys

Q_THIRD = (2**128 - 1) // 3

def gcm_recover(nonce: bytes, msg1: dict, msg2: dict, msg3: dict, msg4: dict) -> bytes:

    BLOCK_LEN = 16

    # Setup all variables that will be needed for Cantor-Zassenhaus and forging the auth tag
    Tu = Polynomial.from_bytes(msg1["auth_tag"])
    Tv = Polynomial.from_bytes(msg2["auth_tag"])
    
    associated_datas = [msg1["associated_data"], msg2["associated_data"], msg3["associated_data"], msg4["associated_data"]]
    ciphertexts = [msg1["ciphertext"], msg2["ciphertext"], msg3["ciphertext"], msg4["ciphertext"]]

    L_list = [gcm.gen_L(ad, ct) for ad, ct in zip(associated_datas, ciphertexts)]
    
    # Split into blocks and then pad the last block
    ciphertext_blocks_list = [gcm.split_bytes(ct, BLOCK_LEN) for ct in ciphertexts]
    ciphertext_blocks_list = [gcm.pad_blocks(ct_blocks, BLOCK_LEN) for ct_blocks in ciphertext_blocks_list]

    ad_blocks_list = [gcm.split_bytes(ad, BLOCK_LEN) for ad in associated_datas]
    ad_blocks_list = [gcm.pad_blocks(ad_blocks, BLOCK_LEN) for ad_blocks in ad_blocks_list]

    msg1_equation = [Tu, Polynomial.from_bytes(L_list[0])]
    msg1_equation.extend([Polynomial.from_bytes(ct) for ct in ciphertext_blocks_list[0][::-1]])
    msg1_equation.extend([Polynomial.from_bytes(ad) for ad in ad_blocks_list[0][::-1]])

    msg2_equation = [Tv, Polynomial.from_bytes(L_list[1])]
    msg2_equation.extend([Polynomial.from_bytes(ct) for ct in ciphertext_blocks_list[1][::-1]])
    msg2_equation.extend([Polynomial.from_bytes(ad) for ad in ad_blocks_list[1][::-1]])

    equation = CZPolynomial.from_poly_list(msg1_equation) + CZPolynomial.from_poly_list(msg2_equation)

    f = equation.make_monisch()

    key_polys = factorize_poly(f, f)    # Liste an CZPolynomials
    zeros = [poly.coefficients[0] for poly in key_polys]

    for h in zeros:

        # GHASH von msg1 XOR auth_tag von msg1 = E_Y0 von msg1
        E_Y0 = Polynomial.from_bytes(gcm.GHASH(h.to_bytes(), ad_blocks_list[0], ciphertext_blocks_list[0], L_list[0])) ^ Polynomial.from_bytes(msg1["auth_tag"])
        
        # Now calculate the auth_tag of msg3 with the h and E_Y0 and check if it is correct on the supplied auth_tag of msg3
        msg3_auth_tag = Polynomial.from_bytes(gcm.GHASH(h.to_bytes(), ad_blocks_list[2], ciphertext_blocks_list[2], L_list[2])) ^ E_Y0

        if msg3_auth_tag.to_bytes() == msg3["auth_tag"]:
            # Forge the auth_tag for msg4 if E_Y0 and h have been verified
            msg4_auth_tag = Polynomial.from_bytes(gcm.GHASH(h.to_bytes(), ad_blocks_list[3], ciphertext_blocks_list[3], L_list[3])) ^ E_Y0
            
            return msg4_auth_tag.to_bytes()

    
    return b""

def factorize_poly(f: CZPolynomial, p: CZPolynomial) -> list:
    
    result = []

    factors = can_zass(f, p)
    while factors == None:
        factors = can_zass(f, p)

    k1, k2 = factors

    if len(k1.coefficients) > 2:
        result.extend(factorize_poly(f, k1))
    else:
        result.append(k1.make_monisch())

    if len(k2.coefficients) > 2:
        result.extend(factorize_poly(f, k2))
    else:
        result.append(k2.make_monisch())

    return result


def can_zass(f: CZPolynomial, p: CZPolynomial) -> tuple:
    
    d = len(f.coefficients)-1   # Grad 1 bei einer länge von 2, deshalb -1
    h = rand_cz_poly(d - 1) # zufälliges Polynom vom Grad d − 1

    g = pow(h, Q_THIRD, f)

    g = (g + CZPolynomial.from_poly_list([Polynomial.from_list([0])])) % f # Add the "1"-polynomial

    q = p.gcd(g)
    
    if int(q) != 1 and q != p:
        k1 = q
        k2 = p // q
        return k1, k2
    else:
        return None

def rand_cz_poly(degree: int):
    """Generiert Metapolynom von garantiert Grad degree"""
    
    # 128 is the bit-count of the GCM polynomials
    BIT_COUNT = 128
    random_poly = CZPolynomial.from_bytes_list([get_rand_bits_as_bytes(BIT_COUNT) for i in range(degree+1)])    # Für Grad=degree braucht man degree+1 Koeffizienten

    # Maybe the random polynomial-coefficient of the highest exponent was 0, regenerate it until it is not zero
    while random_poly.coefficients[-1].to_list() == []:
        random_poly.coefficients[-1] = rand_poly(BIT_COUNT)

    return random_poly

def rand_poly(bit_count: int):
    return Polynomial.from_bytes(get_rand_bits_as_bytes(bit_count))

def get_rand_bits_as_bytes(amount: int):

    if amount % 8 != 0:
        raise ValueError("Amount must be a multiple of 8")

    return random.getrandbits(amount).to_bytes(amount//8, "big")