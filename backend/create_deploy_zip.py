import zipfile
import os
from pathlib import Path
from datetime import datetime

exclude_dirs = {'data', '.git', 'venv', 'env', '__pycache__', '.elasticbeanstalk'}
exclude_patterns = ['*.zip', 'data', '.git', 'venv', 'env', '.env', '*_DEPLOY*.txt', '*_DEPLOY*.md', 'deploy*.ps1', 'deploy*.bat', '__pycache__', '*.pyc', 'test_*.py', 'start_*.bat', 'RESTART_*.bat', '.elasticbeanstalk']

datetime_str = datetime.now().strftime("%Y%m%d_%H%M%S")
version_label = f"app-{datetime_str}"
zip_path = f"deploy-{version_label}.zip"
base_path = Path('.')

print(f"Criando ZIP: {zip_path}")

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk('.'):
        # Filtrar diretórios
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not any(Path(root, d).match(p) for p in exclude_patterns)]
        
        for file in files:
            file_path = Path(root, file)
            # Verificar se deve excluir
            if any(file_path.match(p) for p in exclude_patterns):
                continue
            
            arcname = str(file_path.relative_to(base_path)).replace('\\', '/')
            zipf.write(str(file_path), arcname)

print(f"ZIP criado: {zip_path}")
print(f"Versão: {version_label}")

