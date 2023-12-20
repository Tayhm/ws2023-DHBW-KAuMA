import socket
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

key = "1234567890abcdef".encode()

HOST = ""
PORT = 1234

def check_padding(block):
    last_byte = block[-1]

    if last_byte == 0:
        return False

    for i in range(1, last_byte+1):
        if block[-i] != last_byte:
            return False
        
    return True


def tcp_listen(sock):
    sock.listen()
    print(f"Listening on port {PORT}")

    # Loop to keep accepting new connection after one closes
    while True:

        conn, addr = sock.accept()
        print(f"Connect from {addr}")
        ciphertext = bytearray()

        # Receive ciphertext
        while len(ciphertext) < 16:
            ciphertext += conn.recv(1)

        # Loop to keep receiving Qs until connection is closed
        while True:

            num_of_q = bytearray()
            received_qs = bytearray()

            # Receive number of Qs
            while len(num_of_q) < 2:
                num_of_q += conn.recv(1)
           
            num_of_q = int.from_bytes(num_of_q, "little")
            
            if num_of_q == 0:
                break

            # Receive Qs
            while len(received_qs) < num_of_q * 16:
                received_qs += conn.recv(1)

            # Split received bytes into ciphertext and Qs
            q_blocks = [bytearray(received_qs[x*16:x*16+16]) for x in range(num_of_q)]

            for q in q_blocks:
                
                cipher = Cipher(algorithms.AES128(key), modes.CBC(q))
                decryptor = cipher.decryptor()
                plaintext = decryptor.update(ciphertext) + decryptor.finalize()

                if check_padding(plaintext):
                    conn.sendall(b"\x01")
                else:
                    conn.sendall(b"\x00")

                
        
        conn.close()

if __name__ == "__main__":

    if socket.has_dualstack_ipv6():
        with socket.create_server((HOST, PORT), family=socket.AF_INET6, dualstack_ipv6=True) as sock:
            tcp_listen(sock)
    else:
        with socket.create_server((HOST, PORT)) as sock:
            tcp_listen(sock)