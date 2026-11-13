"""Baixa uma versão fixa da única tabela-fonte do projeto (biblioteca padrão)."""

import argparse
import hashlib
from pathlib import Path
from urllib.request import Request, urlopen

RAIZ = Path(__file__).resolve().parent
COMMIT = "6e8780b23a6453a9a18c60304b681aeec5b48da0"
URL = (
    f"https://raw.githubusercontent.com/andyweaves/worldcup22/{COMMIT}/"
    "resources/international_matches.csv"
)
SHA256 = "1a7f6df7751eb39edb80b5c41afedbb27892762581c0755e52431a102386658b"
DESTINO = RAIZ / "data" / "international_matches.csv"


def baixar(destino=DESTINO):
    """Confere os bytes antes de gravar; não substitui arquivos diferentes."""
    destino = Path(destino)
    if destino.exists():
        if hashlib.sha256(destino.read_bytes()).hexdigest() != SHA256:
            raise ValueError(f"O arquivo {destino} já existe com conteúdo diferente.")
        return destino
    requisicao = Request(URL, headers={"User-Agent": "Projeto-Zebras-Copas"})
    with urlopen(requisicao, timeout=60) as resposta:
        conteudo = resposta.read()
    if hashlib.sha256(conteudo).hexdigest() != SHA256:
        raise ValueError("O download não corresponde ao SHA-256 da versão estudada.")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(conteudo)
    return destino


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", type=Path, default=DESTINO)
    args = parser.parse_args()
    try:
        caminho = baixar(args.destino)
    except (ValueError, OSError) as erro:
        parser.exit(1, f"Erro ao baixar dados: {erro}\n")
    print(f"CSV disponível em {caminho}\nSHA-256: {SHA256}")


if __name__ == "__main__":
    main()
