import os
import re

def check_files():
    pattern = re.compile(r'(?<!await\s)\b(db|eco|self\.bot\.db|self\.eco|self\.db|bot\.db)\.(get_balance|add_balance|remove_balance|set|get|hget|hset|hdel|sadd|srem|smembers|delete|zscore|zincrby)\(')
    for root, dirs, files in os.walk('c:\\Users\\aziza\\OneDrive\\Desktop\\KingBot'):
        if 'venv' in root or '.git' in root or '__pycache__' in root:
            continue
        for f in files:
            if f.endswith('.py'):
                path = os.path.join(root, f)
                with open(path, 'r', encoding='utf-8') as file:
                    for i, line in enumerate(file):
                        if pattern.search(line) and not line.strip().startswith('#'):
                            print(f"{path}:{i+1}:{line.strip()}")

check_files()
