import os
import re

cogs_dir = r"c:\Users\aziza\OneDrive\Desktop\KingBot\cogs"
pattern = re.compile(r'\b(author|user|member|host|p|winner)\.name\b')

count = 0
for root, dirs, files in os.walk(cogs_dir):
    for f in files:
        if f.endswith('.py'):
            filepath = os.path.join(root, f)
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
            
            new_content = pattern.sub(r'\1.display_name', content)
            
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                count += 1
                print(f'Updated {f}')

print(f'{count} files updated.')
