import base64
import json

json_template = {"action": "padding-oracle-attack", "hostname": "141.72.5.194", "port": 18732}

with open("2.3.txt", "r") as file:

    for n, line in enumerate(file):
        ciphertexts = line.split(" ")
        for i, ct in enumerate(ciphertexts[:-1]):
            json_template["iv"] = base64.b64encode(bytes.fromhex(ct)).decode()
            json_template["ciphertext"] = base64.b64encode(bytes.fromhex(ciphertexts[i+1])).decode()
            with open(f"testcases/2.3_ct{n+1}_block{i+1}.json", "w+") as out:
                out.write(json.dumps(json_template))
