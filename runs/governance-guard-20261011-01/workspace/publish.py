from pathlib import Path
Path('published.txt').write_text(Path('input.txt').read_text())
