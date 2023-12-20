# Entschlüsselte Texte

    $ ./query_blocks.sh
    Emerson Brady Von Terra nach Sol Emerson Brady Von Terra nach Sol Der erste Mensch auf der Sonne.
    Ein Programmierer aus Mannheim, recht schlau, verzweifelte, denn sein Code war im Bau. Mit einer Tasse Kaffee in der Hand, sah er den Code, der nicht stand, und rief: "Oh Code, sei mir gnädig, genau!"
    https://web.archive.org/web/20140207013940/http://www.kryptochef.net/

Also:
1. Emerson Brady Von Terra nach Sol Emerson Brady Von Terra nach Sol Der erste Mensch auf der Sonne.
2. Ein Programmierer aus Mannheim, recht schlau, verzweifelte, denn sein Code war im Bau. Mit einer Tasse Kaffee in der Hand, sah er den Code, der nicht stand, und rief: "Oh Code, sei mir gnädig, genau!"
3. https://web.archive.org/web/20140207013940/http://www.kryptochef.net/

Ich habe außerdem mal das Padding entfernt. Das hat zufällig die ascii vertical tabs getroffen, die Formatierung war damit nicht so schön.
query_blocks.sh wird nicht funktionieren, falls Sie es testen wollen, weil dafür kauma statt dem Base64-Output den ascii-plaintext printen muss, was ich wieder entfernen musste damit die Rückgabe richtig ist.