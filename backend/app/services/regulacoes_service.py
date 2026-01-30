"""
Serviço de leitura das regulacoes (CVM, Lei Mercado de Capitais, LGPD, ANBIMA).
Usado pela API em app.routes.regulacoes e pela tool consultar_regulacao em langgraph_tools.
"""
import json
import logging
from pathlib import Path
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

LIST_FIELDS = ("id", "titulo", "norma", "fonte_url", "vigencia", "resumo")


def _regulacoes_dir() -> Path:
    """Diretório de arquivos JSON das regulacoes (data/regulacoes)."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_dir = base_dir / "data" / "regulacoes"
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
    except (PermissionError, OSError):
        base_dir = Path("/tmp")
        data_dir = base_dir / "alphaadvisor_data" / "regulacoes"
        data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def _list_regulacao_files() -> List[Path]:
    """Lista arquivos .json no diretório de regulacoes."""
    d = _regulacoes_dir()
    if not d.exists():
        return []
    return sorted(f for f in d.iterdir() if f.suffix.lower() == ".json" and f.is_file())


def _load_regulacao(path: Path) -> Optional[dict]:
    """Carrega um arquivo JSON de regulacao. Retorna None se inválido."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "id" not in data:
            return None
        texto_path = data.get("texto_path")
        if texto_path:
            base = path.parent
            full_path = (base / texto_path).resolve()
            if full_path.is_file() and str(full_path).startswith(str(base.resolve())):
                try:
                    with open(full_path, "r", encoding="utf-8") as tf:
                        data["texto_completo"] = tf.read()
                except OSError:
                    data["texto_completo"] = data.get("texto_completo") or "(Arquivo de texto não acessível.)"
        return data
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("[RegulacoesService] Erro ao carregar %s: %s", path, e)
        return None


def list_regulacoes() -> List[dict]:
    """Lista todas as regulacoes (id, titulo, norma, fonte_url, vigencia, resumo)."""
    result = []
    for path in _list_regulacao_files():
        data = _load_regulacao(path)
        if data:
            item = {k: data[k] for k in LIST_FIELDS if k in data}
            result.append(item)
    return result


def get_regulacao(regulacao_id: str) -> Optional[dict]:
    """
    Retorna uma regulacao pelo id com todos os campos (incluindo texto_completo).
    regulacao_id pode ser o valor do campo id no JSON ou o nome do arquivo sem .json.
    """
    id_clean = (regulacao_id or "").strip().lower()
    if not id_clean:
        return None
    for path in _list_regulacao_files():
        data = _load_regulacao(path)
        if not data:
            continue
        if data.get("id", "").lower() == id_clean or path.stem.lower() == id_clean:
            return data
    return None
