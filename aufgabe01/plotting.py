import matplotlib.pyplot as plt
import bytenigma
import random

TEST_INPUTS = 1000
TEST_ROTORS = 10
INPUT_LENGTH = 256

# This is quite inefficient
def gen_rand_rotor():
    rotor = []
    while len(rotor) < 256:
        rand = random.randint(0, 255)
        if rand not in rotor:
            rotor.append(rand)

    return rotor

def gen_rand_input(length):
    input = []

    for i in range(length):
        input.append(random.randint(0, 255))

    return bytes(input)



def testBias():
    result = [0] * 256
    for _ in range(TEST_ROTORS):
        rotors = [gen_rand_rotor()]
        for __ in range(TEST_INPUTS):
            for byte in bytenigma.run_bytenigma(rotors, gen_rand_input(INPUT_LENGTH)):
                result[byte] = result[byte] + 1

    return result

result = testBias()
#result = [0] * 256
#input = b"Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."

#for byte in bytenigma.run_bytenigma([range(256)], input):
 #   result[byte] = result[byte] + 1

#for i, val in enumerate(result):
#    result[i] = val / 5

xaxis = range(256)
ypoints = result

plt.bar(xaxis, ypoints)
#plt.ylim(0.8, 1.2)
plt.title("10 zufällige Rotoren, pro Rotor 1000 zufällige Eingaben")
plt.xlabel("Outputbytes")
plt.ylabel("Count")
plt.show()