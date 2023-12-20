from collections import deque

def run_bytenigma(rotors, input):
    
    output = bytearray()

    # Initialize rotors
    rotors_list = [Rotor(rotor) for rotor in rotors]

    for byte in input:

        for rotor in rotors_list:
            byte = rotor.encode(byte)

        byte = ~byte & 0xFF

        for rotor in reversed(rotors_list):
            byte = rotor.decode(byte)
        
        output.append(byte)  # Theoretisch könnte man das hier sicherlich optimieren, indem man es zu nem list lookup macht, weil man weiß, dass es immer nur zwischen 0 und 255 ist

        overflow = rotors_list[0].rotate()
        for rotor in rotors_list[1:]:
            if overflow == 0:
                overflow = rotor.rotate()
            else:
                break


    return output

class Rotor:
    
    def __init__(self, rotor: list):
        self._rotor = deque(rotor)

    def encode(self, byte: int):
        return self._rotor[byte]
        

    def decode(self, byte: int):
        return self._rotor.index(byte)
    
    def rotate(self):
        self._rotor.rotate(-1)
        return self._rotor[255]
            