from pathlib import Path
import sys
value = int(Path('input.txt').read_text())
print('positive input verified' if value > 0 else 'negative input rejected')
sys.exit(0 if value > 0 else 1)
