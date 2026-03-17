"""
config.py — Configurações globais do BidWise
Carrega credenciais e define constantes de modelo.
"""

from __future__ import annotations

import os


def _load_api_key() -> str | None:
    """
    Tenta carregar ANTHROPIC_API_KEY de st.secrets (Streamlit Cloud)
    com fallback para os.environ (dev local).
    Retorna None se nenhuma das duas fontes tiver a chave.
    """
    # Tentativa 1: Streamlit secrets (só disponível quando rodando no Streamlit)
    try:
        import streamlit as st
        key = st.secrets.get("ANTHROPIC_API_KEY")
        if key:
            return key
    except Exception:
        pass  # Não está rodando no Streamlit — normal em dev local

    # Tentativa 2: variável de ambiente
    return os.environ.get("ANTHROPIC_API_KEY")


ANTHROPIC_API_KEY: str | None = _load_api_key()

MODEL_DEFAULT = "claude-sonnet-4-20250514"
MODEL_PREMIUM = "claude-opus-4-6-20250219"

MAX_API_CALLS_PER_SESSION = 5
