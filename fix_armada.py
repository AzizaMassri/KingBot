path = r'C:\Users\aziza\OneDrive\Desktop\KingBot\refactor_battleship.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("King\\\\'s Armada", "King's Armada")
text = text.replace("King\\\\'s", "King's")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
