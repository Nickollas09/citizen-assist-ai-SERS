"""
Citizen Assist AI - conversa pelo terminal (módulo de energia).

Uso:
    python -m app.cli
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from energia.assistente import AssistenteEnergia  # noqa: E402


def limpar_markdown(texto):
    return re.sub(r"\*\*?(.+?)\*\*?", r"\1", texto)


def main():
    bot = AssistenteEnergia()
    print("=" * 70)
    print(" Citizen Assist AI · Energia consciente (digite 'sair' para encerrar)")
    print("=" * 70)
    print(limpar_markdown(bot.responder("ajuda")))
    while True:
        try:
            msg = input("\nVocê: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if msg.lower() in {"sair", "exit", "quit"}:
            break
        print("\nAssistente:\n" + limpar_markdown(bot.responder(msg)))
    print("Até mais! Economizar energia é bom para o bolso e para o planeta. 🌱")


if __name__ == "__main__":
    main()
