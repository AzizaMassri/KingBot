path = r'C:\Users\aziza\OneDrive\Desktop\KingBot\cogs\hangman\hangman.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'spared the peasant!' in line:
        lines[i] = "\t\t\t\tp = f\"```\\n{self.man[fails]}\\n{p}```You guessed the King's password and spared the peasant!\\nThe word was {word}.\"\n"

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(lines)
