import socket

def attack_poracle(hostname, port, iv, ciphertext):
    
    with socket.create_connection((hostname, port)) as sock:

        plaintext = bytearray([0] * 16)
        D_C = bytearray([0] * 16)

        sock.sendall(ciphertext)

        # Get initial byte by sending q 256 times
        sock.sendall(int.to_bytes(256, 2, "little"))

        # Test all possible values for the last byte of Q since at this steps multiple values can result in correct padding
        q = bytearray([0] * 16)
        for i in range(256):
            q[15] = i
            sock.sendall(q)
        
        # Receive answers regarding the validity of the padding
        validity = bytearray()
        while len(validity) < 256:
            validity += sock.recv(1)
            
        # Check if there were two valid paddings and if so, determine which of the Qs resulted in the correct 01 padding
        correct_q = validity.index(1)
        
        if 1 in validity[correct_q+1:]:

            sock.sendall(int.to_bytes(1, 2, "little"))
            q[15] = correct_q
            q[14] = 0xff
            sock.sendall(q)
            valid = b""
            while len(valid) != 1:
                valid = sock.recv(1)

            # If the padding is invalid now, this q didn't result in 0x01 as padding
            if valid[0] == 0:
                correct_q = validity.rindex(1)


        D_C[15] = 0x01 ^ correct_q  # Assume the plaintext could not have been another valid padding for now, taking care of that later
        plaintext[15] = D_C[15] ^ iv[15]

        for index in reversed(range(15)):
            
            # Announce the following 128 q-blocks
            sock.sendall(int.to_bytes(128, 2, "little"))

            # Set the known bytes of q so that the correct padding value results in xoring it
            for j in range(index + 1, 16):
                q[j] = D_C[j] ^ (16-index)

            # Test the first half of the possible values for the current byte in Q
            for i in range(128):
                q[index] = i
                sock.sendall(q)

            # Receive answers regarding the validity of the padding
            validity = bytearray()
            while len(validity) < 128:
                validity += sock.recv(1)
            
            if not 1 in validity:
                # Announce the following 128 q-blocks
                sock.sendall(int.to_bytes(128, 2, "little"))

                # Test the second half of the possible values for the current byte in Q
                for i in range(128, 256):
                    q[index] = i
                    sock.sendall(q)

                # Receive answers regarding the validity of the padding
                validity = bytearray()
                while len(validity) < 128:
                    validity += sock.recv(1)
                
                correct_q = validity.index(1) + 128

            else:
                correct_q = validity.index(1)
                
            D_C[index] = (16-index) ^ correct_q
            plaintext[index] = D_C[index] ^ iv[index]
        
        sock.sendall(b"\x00\x00")

    return plaintext
