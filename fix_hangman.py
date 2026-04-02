path = r'C:\Users\aziza\OneDrive\Desktop\KingBot\cogs\hangman\hangman.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("f'```{self.man[fails]}\\\\n{p}```You guessed the King\\\\'s password and spared the peasant!\\\\nThe word was {word}.'", "f\\\"```\\n{self.man[fails]}\\n{p}```You guessed the King's password and spared the peasant!\\nThe word was {word}.\\\"")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
