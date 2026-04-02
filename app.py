"""
app.py — Interface Streamlit principal do BidWise
Autor: Henrique Alexandre Pinto Silva
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

import exportador
from exportador import draw_uncertainty_chart
from i18n import (
    BEHAVIOR_OPTIONS,
    COMMODITIZATION_OPTIONS,
    INTEREST_OPTIONS,
    KRALJIC_OPTIONS,
    t,
)
from motor import (
    Comportamento,
    Fornecedor,
    FormatoLeilao,
    InputLeilao,
    NivelTripartido,
    QuadranteKraljic,
    recomendar,
)
from simulador import simular

# ──────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="BidWise",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

for _legacy_key in ("sidebar_hidden", "sidebar_collapsed", "show_about"):
    st.session_state.pop(_legacy_key, None)

# ──────────────────────────────────────────────────────────────────────
# LANGUAGE SELECTION — must happen before any t() calls
# ──────────────────────────────────────────────────────────────────────

_lang_raw = st.sidebar.radio(
    "🌐",
    ["PT-BR", "EN"],
    horizontal=True,
    label_visibility="collapsed",
    key="lang_selector",
)
lang: str = "pt" if _lang_raw == "PT-BR" else "en"

st.markdown("""<style>
html, body { overflow-x: hidden !important; }

/* ── BidWise Design Tokens — MarketWise family, azul-petróleo ──────── */
:root {
    --primary-color: #6F8797;
    /* Texto */
    --bw-text-primary: var(--text-color, #1C2D3A);
    --bw-text-secondary: #3F4F5F;
    --bw-text-muted: #6B7E8A;

    /* Superfícies */
    --bw-surface-subtle: rgba(74, 144, 164, 0.08);
    --bw-surface-card: rgba(74, 144, 164, 0.05);
    --bw-sidebar-bg: #F3F6FA;

    /* Bordas */
    --bw-border-subtle: rgba(196, 213, 223, 0.90);

    /* Barra de privacidade */
    --bw-privacy-bg: #EBF1F6;
    --bw-privacy-text: #1C2D3A;

    /* Marca — azul-petróleo BidWise */
    --bw-brand: #4A90A4;
    --bw-brand-subtitle: #3F4F5F;
    --bw-accent: #6F8797;
    --bw-accent-hover: #5F7686;
    --bw-accent-soft: rgba(111, 135, 151, 0.16);
    --bw-accent-border: rgba(111, 135, 151, 0.40);
}

/* ── Tema escuro ────────────────────────────────────────────────────── */
@media (prefers-color-scheme: dark) {
    :root {
        --primary-color: #6F91A3;
        --bw-text-secondary: #A8BFCC;
        --bw-text-muted: #6B8A9A;
        --bw-surface-subtle: rgba(91, 174, 196, 0.10);
        --bw-surface-card: rgba(91, 174, 196, 0.05);
        --bw-sidebar-bg: #262730;
        --bw-border-subtle: rgba(91, 174, 196, 0.22);
        --bw-privacy-bg: #0E1A24;
        --bw-privacy-text: #E8F2F8;
        --bw-brand: #5BAEC4;
        --bw-brand-subtitle: #A8BFCC;
        --bw-accent: #6F91A3;
        --bw-accent-hover: #82A5B8;
        --bw-accent-soft: rgba(111, 145, 163, 0.22);
        --bw-accent-border: rgba(130, 165, 184, 0.46);
    }
}

.bw-privacy-bar {
    background-color: var(--bw-privacy-bg);
    color: var(--bw-privacy-text);
    padding: 8px 16px;
    text-align: center;
    font-size: 14px;
    border-bottom: 1px solid var(--bw-border-subtle);
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    z-index: 1000;
}

.bw-market-bar {
    background: #E8EFF6;
    color: #24425A;
    border: 1px solid #C7D6E2;
    border-radius: 10px;
    padding: 6px 14px;
    text-align: center;
    font-size: 0.9rem;
    font-weight: 500;
    margin: 10px auto 14px auto;
    max-width: min(980px, 100%);
}

@media (prefers-color-scheme: dark) {
    .bw-market-bar {
        color: #EAF4FA;
        background: #183243;
        border-color: #2A566B;
    }
}

.stAppViewContainer,
[data-testid="stSidebar"] {
    padding-top: 44px;
}

.bw-header {
    padding-bottom: 4px;
}

.bw-header__brand {
    font-size: 2.4rem;
    font-weight: 800;
    color: var(--bw-brand);
}

.bw-header__title {
    font-size: 1.1rem;
    color: var(--bw-brand-subtitle);
    font-weight: 500;
}

.bw-header__tagline {
    color: var(--bw-text-secondary);
    font-size: 0.88rem;
    margin-bottom: 1rem;
}

.bw-format-title {
    color: var(--bw-format-accent, var(--bw-text-primary));
    margin-bottom: 0;
}

.bw-archetype-card {
    text-align: center;
    background: var(--bw-surface-card);
    border: 1px solid var(--bw-border-subtle);
    border-radius: 12px;
    padding: 16px 12px;
    height: 100%;
}

.bw-archetype-card__count {
    font-size: 48px;
    font-weight: bold;
    line-height: 1.1;
    color: var(--bw-text-primary);
}

.bw-archetype-card__desc {
    color: var(--bw-text-secondary);
    font-size: 13px;
}

.bw-scenario-card {
    border-left: 4px solid var(--bw-format-accent, var(--bw-text-primary));
    background: var(--bw-surface-card);
    border-radius: 8px;
    padding: 10px 12px;
}

.bw-scenario-card__format {
    color: var(--bw-format-accent, var(--bw-text-primary));
    font-size: 0.9rem;
}

.bw-footer {
    text-align: center;
    color: var(--bw-text-muted);
    font-size: 0.8rem;
    padding-bottom: 1rem;
}

.bw-footer a {
    color: var(--bw-text-muted);
}

button[kind="primary"] {
    background-color: var(--bw-accent) !important;
    border-color: var(--bw-accent) !important;
    color: #F8FAFC !important;
}

button[kind="primary"]:hover {
    background-color: var(--bw-accent-hover) !important;
    border-color: var(--bw-accent-hover) !important;
}

button[kind="secondary"] {
    border-color: var(--bw-accent-border) !important;
}

[data-testid="stSidebar"] [data-baseweb="radio"] label,
[data-testid="stSidebar"] [data-baseweb="radio"] label *,
[data-testid="stSidebar"] [data-baseweb="radio"] label[data-checked="true"],
[data-testid="stSidebar"] [data-baseweb="radio"] label[data-checked="true"] * {
    background: transparent !important;
    background-color: transparent !important;
    border-color: transparent !important;
    box-shadow: none !important;
}

[data-testid="stSidebar"] input[type="radio"] {
    accent-color: var(--bw-accent) !important;
}

[data-testid="stSidebar"] [role="radio"],
[data-testid="stSidebar"] [role="radiogroup"] [role="radio"] {
    background: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
}

[data-testid="stSidebar"] [role="radio"][aria-checked="true"],
[data-testid="stSidebar"] [role="radiogroup"] [aria-checked="true"] {
    color: inherit !important;
    background: transparent !important;
    background-color: transparent !important;
}

[data-testid="stSidebar"] [role="radio"][aria-checked="true"] *,
[data-testid="stSidebar"] [role="radiogroup"] [aria-checked="true"] * {
    border-color: var(--bw-accent) !important;
    background: transparent !important;
    background-color: transparent !important;
}

[data-testid="stSidebar"] [data-baseweb="radio"] input:checked + div,
[data-testid="stSidebar"] [data-baseweb="radio"] input:checked + div::before,
[data-testid="stSidebar"] [data-baseweb="radio"] div[aria-checked="true"],
[data-testid="stSidebar"] [data-baseweb="radio"] div[aria-checked="true"]::before {
    background-color: var(--bw-accent) !important;
    border-color: var(--bw-accent) !important;
}

[data-testid="stSidebar"] [data-baseweb="radio"] label > div:last-child {
    background: transparent !important;
    background-color: transparent !important;
}

.st-key-lang_selector,
.st-key-lang_selector * {
    --st-radio-selected-bg: transparent !important;
}

.st-key-lang_selector [data-baseweb="radio"] label > div:last-child,
.st-key-lang_selector [data-baseweb="radio"] label > div:last-child span,
.st-key-lang_selector [data-baseweb="radio"] label > div:last-child,
.st-key-lang_selector [data-baseweb="radio"] label > div:last-child *,
.st-key-lang_selector [role="radio"] > div:last-child,
.st-key-lang_selector [role="radio"] > div:last-child * {
    background: transparent !important;
    background-color: transparent !important;
    background-image: none !important;
    box-shadow: none !important;
}

.st-key-lang_selector [data-baseweb="radio"] label > *:not(:first-child),
.st-key-lang_selector [data-baseweb="radio"] label > *:not(:first-child) *,
.st-key-lang_selector [role="radio"] > *:not(:first-child),
.st-key-lang_selector [role="radio"] > *:not(:first-child) * {
    background: transparent !important;
    background-color: transparent !important;
    background-image: none !important;
    box-shadow: none !important;
}

.st-key-lang_selector [data-baseweb="radio"] input:checked + div + div,
.st-key-lang_selector [data-baseweb="radio"] input:checked + div + div *,
.st-key-lang_selector [data-baseweb="radio"] input + div + div,
.st-key-lang_selector [data-baseweb="radio"] input + div + div * {
    background: transparent !important;
    background-color: transparent !important;
    background-image: none !important;
    box-shadow: none !important;
}

.st-key-lang_selector [data-baseweb="radio"] [data-testid="stMarkdownContainer"],
.st-key-lang_selector [data-baseweb="radio"] [data-testid="stMarkdownContainer"] *,
.st-key-lang_selector [data-baseweb="radio"] p,
.st-key-lang_selector [data-baseweb="radio"] span,
.st-key-lang_selector [data-baseweb="radio"] div {
    background: transparent !important;
    background-color: transparent !important;
    background-image: none !important;
    box-shadow: none !important;
}

.st-key-lang_selector [data-baseweb="radio"] label {
    padding: 0 !important;
    gap: 0.35rem !important;
}

button[data-testid="stNumberInputStepUp"],
button[data-testid="stNumberInputStepDown"] {
    border-color: var(--bw-accent-border) !important;
}

button[data-testid="stNumberInputStepUp"]:hover,
button[data-testid="stNumberInputStepDown"]:hover,
button[data-testid="stNumberInputStepUp"]:focus,
button[data-testid="stNumberInputStepDown"]:focus {
    background-color: var(--bw-accent-soft) !important;
    border-color: var(--bw-accent) !important;
    color: var(--bw-accent) !important;
}

[data-baseweb="input"]:focus-within,
[data-baseweb="base-input"]:focus-within,
[data-baseweb="select"]:focus-within,
[data-baseweb="select"] > div:focus-within,
[data-baseweb="select"] > div[data-focus="true"],
[data-baseweb="base-input"] > div:focus-within,
[data-baseweb="base-input"] > div[data-focus="true"],
[data-testid="stTextInput"] [data-baseweb="input"]:focus-within,
[data-testid="stTextInput"] [data-baseweb="base-input"]:focus-within,
[data-testid="stNumberInput"] [data-baseweb="input"]:focus-within,
[data-testid="stNumberInput"] [data-baseweb="base-input"]:focus-within,
[data-testid="stNumberInput"] input:focus-visible,
[data-testid="stNumberInput"] input:focus,
[data-testid="stSelectbox"] [data-baseweb="select"]:focus-within,
[data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within,
[data-testid="stSelectbox"] [data-baseweb="select"] > div[data-focus="true"],
textarea:focus,
input:focus,
select:focus {
    border-color: var(--bw-accent) !important;
    box-shadow: 0 0 0 1px var(--bw-accent) !important;
    outline: none !important;
}

/* Streamlit/BaseWeb fallback states that still used the default accent */
a,
a:visited,
[data-testid="stTooltipIcon"] button,
[data-testid="stTooltipIcon"] svg,
[data-testid="stExpander"] summary:hover,
[data-testid="stExpander"] summary:focus-visible,
[data-testid="stExpander"] [data-testid="stIconMaterial"],
[data-testid="stMetricDelta"] {
    color: var(--bw-accent) !important;
}

[data-testid="stTooltipIcon"] button:hover,
[data-testid="stTooltipIcon"] button:focus-visible {
    color: var(--bw-accent-hover) !important;
    border-color: var(--bw-accent-border) !important;
    box-shadow: 0 0 0 1px var(--bw-accent-soft) !important;
}

[data-testid="stAlert"] [data-baseweb="notification"],
[data-testid="stInfo"] [data-baseweb="notification"] {
    border-color: var(--bw-accent-border) !important;
    background: var(--bw-accent-soft) !important;
}

[data-testid="stAlert"] [data-testid="stAlertContentInfo"],
[data-testid="stInfo"] [data-testid="stAlertContentInfo"],
[data-testid="stAlert"] [data-testid="stAlertDynamicIcon"],
[data-testid="stInfo"] [data-testid="stAlertDynamicIcon"] {
    color: var(--bw-accent) !important;
}

[data-baseweb="select"] *[aria-selected="true"],
[role="listbox"] [aria-selected="true"] {
    background-color: var(--bw-accent-soft) !important;
    color: var(--bw-text-primary) !important;
}

button:focus-visible,
[role="button"]:focus-visible,
summary:focus-visible {
    box-shadow: 0 0 0 2px var(--bw-accent-soft) !important;
}
</style>""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────
# ENUM MAPPINGS — handles both EN and PT-BR keys
# ──────────────────────────────────────────────────────────────────────

_KRALJIC_ENUM: dict[str, QuadranteKraljic] = {
    # EN keys
    "Leverage":     QuadranteKraljic.ALAVANCA,
    "Strategic":    QuadranteKraljic.ESTRATEGICO,
    "Bottleneck":   QuadranteKraljic.GARGALO,
    "Non-critical": QuadranteKraljic.NAO_CRITICO,
    # PT-BR keys
    "Alavancagem":  QuadranteKraljic.ALAVANCA,
    "Estratégico":  QuadranteKraljic.ESTRATEGICO,
    "Gargalo":      QuadranteKraljic.GARGALO,
    "Não crítico":  QuadranteKraljic.NAO_CRITICO,
}

_COMOD_ENUM: dict[str, NivelTripartido] = {
    "High": NivelTripartido.ALTO,   "Medium": NivelTripartido.MEDIO,  "Low": NivelTripartido.BAIXO,
    "Alto": NivelTripartido.ALTO,   "Médio":  NivelTripartido.MEDIO,  "Baixo": NivelTripartido.BAIXO,
}

_BEHAVIOR_ENUM: dict[str, Comportamento] = {
    "Competitive":  Comportamento.COMPETITIVO,
    "Moderate":     Comportamento.MODERADO,
    "Conservative": Comportamento.CONSERVADOR,
    "Competitivo":  Comportamento.COMPETITIVO,
    "Moderado":     Comportamento.MODERADO,
    "Conservador":  Comportamento.CONSERVADOR,
}

_INTEREST_ENUM_FULL: dict[str, NivelTripartido] = {
    "High": NivelTripartido.ALTO,   "Medium": NivelTripartido.MEDIO,  "Low": NivelTripartido.BAIXO,
    "Alto": NivelTripartido.ALTO,   "Médio":  NivelTripartido.MEDIO,  "Baixo": NivelTripartido.BAIXO,
}


def _extract_key(label: str) -> str:
    """Extract the keyword before ' —' from a descriptive dropdown label."""
    return label.split(" —")[0].strip()


# ──────────────────────────────────────────────────────────────────────
# FORMAT MAPS
# ──────────────────────────────────────────────────────────────────────

FORMAT_EMOJI: dict[FormatoLeilao, str] = {
    FormatoLeilao.INGLES_COMPLETO: "📊",
    FormatoLeilao.INGLES_REDUZIDO: "📋",
    FormatoLeilao.HOLANDES:        "🔒",
    FormatoLeilao.JAPONES:         "⏬",
    FormatoLeilao.NAO_LEILAO:      "⚠️",
}

FORMAT_COLOR: dict[FormatoLeilao, str] = {
    # Mid-tone para funcionar em tema claro e escuro
    FormatoLeilao.INGLES_COMPLETO: "#2D7DD2",  # azul-médio  — visibilidade + pressão
    FormatoLeilao.INGLES_REDUZIDO: "#17A2A2",  # teal        — visibilidade reduzida
    FormatoLeilao.HOLANDES:        "#7C3AED",  # violeta     — opacidade / clock
    FormatoLeilao.JAPONES:         "#D97706",  # âmbar       — eliminação progressiva
    FormatoLeilao.NAO_LEILAO:      "#DC2626",  # vermelho    — alerta
}

FORMAT_LABEL_EN: dict[FormatoLeilao, str] = {
    FormatoLeilao.INGLES_COMPLETO: "English Reverse — Ranking + Thermometer",
    FormatoLeilao.INGLES_REDUZIDO: "English Reverse — Ranking Only",
    FormatoLeilao.HOLANDES:        "Dutch Reverse",
    FormatoLeilao.JAPONES:         "Japanese Reverse",
    FormatoLeilao.NAO_LEILAO:      "Do Not Auction",
}

FORMAT_LABEL_PT: dict[FormatoLeilao, str] = {
    FormatoLeilao.INGLES_COMPLETO: "Leilão Reverso Inglês — Ranking + Termômetro",
    FormatoLeilao.INGLES_REDUZIDO: "Leilão Reverso Inglês — Apenas Ranking",
    FormatoLeilao.HOLANDES:        "Leilão Reverso Holandês",
    FormatoLeilao.JAPONES:         "Leilão Reverso Japonês",
    FormatoLeilao.NAO_LEILAO:      "Não Realizar Leilão",
}

MECH_LABEL_EN: dict[str, str] = {
    "RFQ com negociação posterior":                "RFQ with subsequent negotiation",
    "Nova rodada de qualificação + RFQ":           "New qualification round + RFQ",
    "Negociação direta com fornecedor":            "Direct negotiation with supplier",
    "Contrato guarda-chuva com revisão periódica": "Umbrella contract with periodic review",
}


def _format_label(fmt: FormatoLeilao, lang: str) -> str:
    if lang == "pt":
        return FORMAT_LABEL_PT[fmt]
    return FORMAT_LABEL_EN[fmt]


def _mech_label(mec_value: str, lang: str) -> str:
    if lang == "pt":
        return mec_value  # already in PT
    return MECH_LABEL_EN.get(mec_value, mec_value)


# ──────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────

def _fmt_brl(value: float | None) -> str:
    if value is None:
        return "—"
    return f"$ {value:,.2f}"


def _is_dark_theme() -> bool:
    """Best-effort detection of the active Streamlit theme."""
    def _hex_to_rgb(value: str) -> tuple[int, int, int] | None:
        value = value.strip()
        if not value.startswith("#"):
            return None
        value = value.lstrip("#")
        if len(value) == 3:
            value = "".join(ch * 2 for ch in value)
        if len(value) != 6:
            return None
        try:
            return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
        except ValueError:
            return None

    try:
        base = str(st.get_option("theme.base") or "").lower()
        if base in {"dark", "light"}:
            return base == "dark"

        bg = st.get_option("theme.backgroundColor")
        text = st.get_option("theme.textColor")
        bg_rgb = _hex_to_rgb(str(bg)) if bg else None
        text_rgb = _hex_to_rgb(str(text)) if text else None

        if bg_rgb:
            luminance = (0.2126 * bg_rgb[0] + 0.7152 * bg_rgb[1] + 0.0722 * bg_rgb[2]) / 255
            return luminance < 0.5

        if text_rgb:
            luminance = (0.2126 * text_rgb[0] + 0.7152 * text_rgb[1] + 0.0722 * text_rgb[2]) / 255
            return luminance > 0.7
    except Exception:
        pass
    return False


def _build_copy_prompt(inp: InputLeilao, rec, sim, lang: str = "en") -> str:
    """Generate a structured prompt the user can paste into any AI assistant."""
    _KRALJIC_EN = {
        "Alavancagem": "Leverage", "Estratégico": "Strategic",
        "Gargalo": "Bottleneck", "Não crítico": "Non-critical",
    }
    _NIVEL_EN = {"Alto": "High", "Médio": "Medium", "Baixo": "Low"}
    _BEHAV_EN = {
        "Competitivo": "Competitive", "Moderado": "Moderate", "Conservador": "Conservative",
    }

    lines = [
        "# BidWise Auction Analysis — Take to Your Preferred AI",
        "",
        "## Scenario Inputs",
        f"- Number of suppliers: {inp.num_fornecedores}",
        f"- Kraljic quadrant: {_KRALJIC_EN.get(inp.kraljic.value, inp.kraljic.value)}",
        f"- Item commoditization: {_NIVEL_EN.get(inp.comoditizacao.value, inp.comoditizacao.value)}",
        f"- Price spread (auto-calculated): {inp.dispersao_precos:.1f}%",
        "",
        "## Supplier Profiles (anonymized)",
    ]
    for i, forn in enumerate(inp.fornecedores):
        _prop_str = f"${forn.proposta_brl:,.0f}" if forn.proposta_brl else "not provided"
        lines.append(
            f"- Supplier {i + 1}: "
            f"proposal={_prop_str}"
            f", strategic interest={_NIVEL_EN.get(forn.interesse_estrategico.value, forn.interesse_estrategico.value)}"
            f", behavior={_BEHAV_EN.get(forn.comportamento.value, forn.comportamento.value)}"
        )
    lines += [
        "",
        "## BidWise Recommendation",
        f"- Recommended format: {FORMAT_LABEL_EN[rec.formato]}",
        f"- Justification: {rec.justificativa}",
    ]
    if rec.parametros:
        p = rec.parametros
        lines += [
            "",
            "## Optimized Parameters",
            f"- Minimum decrement: {p.decremento_min_pct:.2f}%"
            + (f" ($ {p.decremento_min_brl:,.0f})" if p.decremento_min_brl else ""),
            f"- Opening price: {p.preco_abertura_pct:+.1f}% vs. best proposal",
            f"- Auction duration: {p.duracao_minutos} min",
        ]
        if p.prorrogacao_minutos:
            lines.append(f"- Auto-extension: +{p.prorrogacao_minutos} min")
        if p.visibilidade:
            lines.append(f"- Thermometer visibility: {p.visibilidade}")
        if p.rodadas_estimadas:
            lines.append(f"- Estimated rounds: ~{p.rodadas_estimadas}")
    if rec.saving:
        s = rec.saving
        lines += [
            "",
            "## Saving Estimate",
            f"- Pessimistic: {s.pessimista_pct:.1f}%",
            f"- Realistic: {s.realista_pct:.1f}%",
            f"- Optimistic: {s.otimista_pct:.1f}%",
        ]
    lines += [
        "",
        "## Simulation Summary",
        sim.narrativa,
        "",
        "---",
        "## Request to AI",
        "Based on the above auction scenario and BidWise's recommendation, please provide:",
        "1) A deeper analysis of the recommended format choice and why it fits this scenario.",
        "2) Predicted supplier behavior during the auction — who will lead, who may drop out, when.",
        "3) Key risk factors and mitigation strategies the buyer should prepare for.",
        "4) Suggestions for post-auction negotiation to lock in the saving.",
    ]
    if lang == "pt":
        lines += ["", "Por favor, responda em português."]
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────
# ANALYTICS
# ──────────────────────────────────────────────────────────────────────

st.markdown(
    """
    <script defer data-domain="bidwise.streamlit.app"
            src="https://plausible.io/js/script.js"></script>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────
# TABS
# ──────────────────────────────────────────────────────────────────────

st.markdown(
    f'<div class="bw-privacy-bar">'
    f'{t("privacy_bar", lang)}'
    f'</div>',
    unsafe_allow_html=True,
)

st.markdown(
    f'<div class="bw-market-bar">{t("market_report_bar", lang)}</div>',
    unsafe_allow_html=True,
)

if "active_tab" not in st.session_state:
    st.session_state.active_tab = 0

_tab_labels = [t("tab_advisor", lang), t("tab_guide", lang), t("tab_about", lang)]
_tc1, _tc2, _tc3 = st.columns(3)
for _ti, (_tcol, _tlabel) in enumerate(zip([_tc1, _tc2, _tc3], _tab_labels)):
    with _tcol:
        if st.button(_tlabel, key=f"_tabbtn_{_ti}", use_container_width=True,
                     type="primary" if st.session_state.active_tab == _ti else "secondary"):
            st.session_state.active_tab = _ti
            st.rerun()

_active_tab = st.session_state.active_tab

# ══════════════════════════════════════════════════════════════════════
# GUIDE TAB
# ══════════════════════════════════════════════════════════════════════

if _active_tab == 1:
    _guide_file = "supplier_guide_pt.md" if lang == "pt" else "supplier_guide.md"
    try:
        with open(_guide_file, encoding="utf-8") as _f:
            st.markdown(_f.read())
    except FileNotFoundError:
        with open("supplier_guide.md", encoding="utf-8") as _f:
            st.markdown(_f.read())

# ══════════════════════════════════════════════════════════════════════
# ABOUT TAB
# ══════════════════════════════════════════════════════════════════════

if _active_tab == 2:
    _about_file = "about_pt.md" if lang == "pt" else "about.md"
    try:
        with open(_about_file, encoding="utf-8") as _f:
            st.markdown(_f.read())
    except FileNotFoundError:
        with open("about.md", encoding="utf-8") as _f:
            st.markdown(_f.read())

# ══════════════════════════════════════════════════════════════════════
# MAIN TAB — AUCTION ADVISOR
# ══════════════════════════════════════════════════════════════════════

if _active_tab == 0:

    # ──────────────────────────────────────────────────────────────────
    # HEADER
    # ──────────────────────────────────────────────────────────────────

    st.markdown(
        f"""
        <div class="bw-header">
            <span class="bw-header__brand">⚖️ BidWise</span>
            &nbsp;
            <span class="bw-header__title">
                {"Consultor de Estratégia de Leilão Reverso" if lang == "pt" else "Reverse Auction Strategy Advisor"}
            </span>
        </div>
        <div class="bw-header__tagline">
            {t("tagline", lang)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ──────────────────────────────────────────────────────────────────
    # SIDEBAR — INPUT FORM
    # ──────────────────────────────────────────────────────────────────

    with st.sidebar:
        if "last_rec" not in st.session_state:
            st.info(t("sidebar_no_analysis_tip", lang))

        st.markdown(f"### {t('sidebar_title', lang)}")

        # ── Auction context ──────────────────────────────────────────
        kraljic_label = st.selectbox(
            t("kraljic", lang),
            options=KRALJIC_OPTIONS[lang],
            index=st.session_state.get("_kq_idx", 0),
            help=t("kraljic_help", lang),
        )
        st.session_state["_kq_idx"] = KRALJIC_OPTIONS[lang].index(kraljic_label)

        comod_label = st.selectbox(
            t("commoditization", lang),
            options=COMMODITIZATION_OPTIONS[lang],
            index=st.session_state.get("_cm_idx", 0),
            help=t("commoditization_help", lang),
        )
        st.session_state["_cm_idx"] = COMMODITIZATION_OPTIONS[lang].index(comod_label)

        st.divider()

        # ── Supplier profiles ────────────────────────────────────────
        st.markdown(f"#### {t('supplier_profiles', lang)}")
        n_suppliers = st.number_input(
            t("num_suppliers", lang),
            min_value=1,
            max_value=15,
            value=4,
            step=1,
            key="num_suppliers",
            help=t("num_suppliers_help", lang),
        )

        _sup_default_prefix = "Fornecedor" if lang == "pt" else "Supplier"
        _supplier_inputs: list[dict] = []
        for _i in range(int(n_suppliers)):
            _default_name = f"{_sup_default_prefix} {chr(65 + _i)}"  # A, B, C, ...
            with st.expander(_default_name, expanded=(_i == 0)):
                _name = st.text_input(
                    t("name", lang),
                    value=_default_name,
                    key=f"sup_name_{_i}",
                )
                _prop = st.number_input(
                    t("proposal", lang),
                    min_value=0.0,
                    value=0.0,
                    step=1_000.0,
                    format="%.2f",
                    key=f"sup_prop_{_i}",
                    help=t("proposal_help", lang),
                )
                # Correct stored option string when language changes
                _int_opts = INTEREST_OPTIONS[lang]
                if st.session_state.get(f"sup_int_{_i}") not in _int_opts:
                    st.session_state[f"sup_int_{_i}"] = _int_opts[st.session_state.get(f"_si_idx_{_i}", 1)]
                _int_label = st.selectbox(
                    t("interest", lang),
                    options=_int_opts,
                    key=f"sup_int_{_i}",
                    help=t("interest_help", lang),
                )
                st.session_state[f"_si_idx_{_i}"] = _int_opts.index(_int_label)

                _beh_opts = BEHAVIOR_OPTIONS[lang]
                if st.session_state.get(f"sup_beh_{_i}") not in _beh_opts:
                    st.session_state[f"sup_beh_{_i}"] = _beh_opts[st.session_state.get(f"_sb_idx_{_i}", 1)]
                _beh_label = st.selectbox(
                    t("behavior", lang),
                    options=_beh_opts,
                    key=f"sup_beh_{_i}",
                    help=t("behavior_help", lang),
                )
                st.session_state[f"_sb_idx_{_i}"] = _beh_opts.index(_beh_label)
                _supplier_inputs.append({
                    "name":     _name,
                    "proposal": _prop,
                    "interest": _extract_key(_int_label),
                    "behavior": _extract_key(_beh_label),
                })

        _props_entered = [s for s in _supplier_inputs if s["proposal"] > 0]
        if len(_props_entered) < 2:
            st.info(t("tip_min_proposals", lang))

        analyze = st.button(t("analyze", lang), type="primary", width="stretch")
        if st.button(t("reset", lang), type="secondary", width="stretch"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # ──────────────────────────────────────────────────────────────────
    # SESSION STATE INIT
    # ──────────────────────────────────────────────────────────────────

    if "scenarios" not in st.session_state:
        st.session_state.scenarios = []
    if "last_inp" not in st.session_state:
        st.session_state.last_inp = None

    # ──────────────────────────────────────────────────────────────────
    # MAIN LOGIC — run when Analyze clicked
    # ──────────────────────────────────────────────────────────────────

    if analyze:
        _fornecedores = [
            Fornecedor(
                nome=s["name"],
                proposta_brl=s["proposal"] if s["proposal"] > 0 else None,
                interesse_estrategico=_INTEREST_ENUM_FULL[s["interest"]],
                comportamento=_BEHAVIOR_ENUM[s["behavior"]],
            )
            for s in _supplier_inputs
        ]

        inp = InputLeilao(
            fornecedores=_fornecedores,
            kraljic=_KRALJIC_ENUM[_extract_key(kraljic_label)],
            comoditizacao=_COMOD_ENUM[_extract_key(comod_label)],
        )

        rec = recomendar(inp, lang=lang)
        sim = simular(inp, rec, lang=lang)

        st.session_state.last_inp = inp
        st.session_state.last_rec = rec
        st.session_state.last_sim = sim
        st.session_state.last_lang = lang

    # Gate: show prompt if no analysis yet
    if "last_rec" not in st.session_state:
        st.info(t("get_started", lang))
        st.stop()

    inp = st.session_state.last_inp
    rec = st.session_state.last_rec
    sim = st.session_state.last_sim

    if inp.dispersao_precos > 100:
        st.warning(t("spread_warning_extreme", lang))
    elif inp.dispersao_precos > 50:
        st.warning(t("spread_warning", lang))

    if inp.kraljic == QuadranteKraljic.GARGALO and inp.num_fornecedores >= 6:
        st.info(t("bottleneck_large_field", lang))

    # ──────────────────────────────────────────────────────────────────
    # 1. RECOMMENDATION CARD
    # ──────────────────────────────────────────────────────────────────

    fmt = rec.formato
    fmt_color = FORMAT_COLOR[fmt]
    fmt_emoji = FORMAT_EMOJI[fmt]

    if fmt == FormatoLeilao.NAO_LEILAO:
        with st.container(border=True):
            st.error(
                f"**{fmt_emoji} {_format_label(fmt, lang)}**\n\n"
                f"{rec.alerta_nao_leilao.explicacao if rec.alerta_nao_leilao else rec.justificativa}",
                icon="🚫",
            )
            if rec.alerta_nao_leilao:
                mec_display = _mech_label(rec.alerta_nao_leilao.mecanismo_sugerido.value, lang)
                st.markdown(f"**{t('suggested_mechanism', lang)}** {mec_display}")
    else:
        with st.container(border=True):
            st.markdown(
                f"<h2 class='bw-format-title' style='--bw-format-accent:{fmt_color};'>"
                f"{fmt_emoji} {_format_label(fmt, lang)}</h2>",
                unsafe_allow_html=True,
            )
            st.markdown(rec.justificativa)

    st.markdown("---")

    _eff_abertura_pct: float | None = rec.parametros.preco_abertura_pct if rec.parametros else None
    _eff_abertura_brl: float | None = rec.parametros.preco_abertura_brl if rec.parametros else None
    _is_english = fmt in (FormatoLeilao.INGLES_COMPLETO, FormatoLeilao.INGLES_REDUZIDO)

    # ──────────────────────────────────────────────────────────────────
    # 2. OPTIMIZED PARAMETERS
    # ──────────────────────────────────────────────────────────────────

    if rec.parametros and fmt != FormatoLeilao.NAO_LEILAO:
        st.subheader(t("optimized_params", lang))
        p = rec.parametros

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            brl_str = f"$ {p.decremento_min_brl:,.0f}" if p.decremento_min_brl else None
            st.metric(t("min_decrement", lang), f"{p.decremento_min_pct:.2f}%", delta=brl_str)
        with c2:
            ap_brl_str = f"$ {_eff_abertura_brl:,.0f}" if _eff_abertura_brl else None
            _abertura_desc = getattr(p, "preco_abertura_descricao", None)
            if _abertura_desc:
                ap_pct_str = _abertura_desc
            elif _eff_abertura_pct is not None:
                ap_pct_str = f"{_eff_abertura_pct:+.1f}%"
            else:
                ap_pct_str = "—"
            st.metric(t("opening_price", lang), ap_pct_str, delta=ap_brl_str)
        with c3:
            ext_str = t("auto_ext_delta", lang).format(mins=p.prorrogacao_minutos) if p.prorrogacao_minutos else None
            st.metric(t("duration", lang), f"{p.duracao_minutos} min", delta=ext_str)
        with c4:
            if p.rodadas_estimadas:
                st.metric(
                    t("est_rounds", lang), f"~{p.rodadas_estimadas}",
                    delta=f"{p.intervalo_rodada_minutos} min / round" if p.intervalo_rodada_minutos else None,
                )
            elif p.incremento_holandes_pct:
                inc_brl = f"$ {p.incremento_holandes_brl:,.0f}/tick" if p.incremento_holandes_brl else None
                st.metric(t("dutch_increment", lang), f"{p.incremento_holandes_pct:.2f}%/tick", delta=inc_brl)
            elif p.visibilidade:
                _is_enabled = "Enabled" in p.visibilidade or "Ativado" in p.visibilidade
                enabled_str = ("Ativado" if lang == "pt" else "Enabled") if _is_enabled else ("Desativado" if lang == "pt" else "Disabled")
                st.metric(t("thermometer", lang), enabled_str)

        if getattr(p, "preco_abertura_descricao", None):
            _opening_val = p.preco_abertura_descricao
            _opening_brl = t("best_response_note", lang) if _is_english else _fmt_brl(_eff_abertura_brl)
        elif _eff_abertura_pct is not None:
            _opening_val = f"{_eff_abertura_pct:+.1f}%"
            _opening_brl = _fmt_brl(_eff_abertura_brl)
        else:
            _opening_val = "—"
            _opening_brl = "—"

        rows = [
            (t("min_decrement_param", lang), f"{p.decremento_min_pct:.2f}%", _fmt_brl(p.decremento_min_brl)),
            (t("opening_label", lang), _opening_val, _opening_brl),
            (t("duration_param", lang), f"{p.duracao_minutos} min", "—"),
        ]
        if p.prorrogacao_minutos:
            rows.append((
                t("auto_ext_param", lang).format(trigger=p.prorrogacao_trigger_minutos),
                f"+{p.prorrogacao_minutos} min", "—",
            ))
        if p.visibilidade:
            rows.append((t("thermometer_param", lang), p.visibilidade, "—"))
        if p.rodadas_estimadas:
            rows.append((
                t("rounds_param", lang).format(interval=p.intervalo_rodada_minutos),
                f"~{p.rodadas_estimadas}", "—",
            ))
        if p.incremento_holandes_pct:
            rows.append((
                t("dutch_increment_param", lang),
                f"{p.incremento_holandes_pct:.2f}%",
                _fmt_brl(p.incremento_holandes_brl),
            ))

        st.dataframe(
            pd.DataFrame(rows, columns=[
                t("param_col_parameter", lang),
                t("param_col_value_pct", lang),
                t("param_col_value_brl", lang),
            ]),
            use_container_width=True,
            hide_index=True,
        )
        st.markdown("---")

    # ──────────────────────────────────────────────────────────────────
    # 3. SAVING ESTIMATE + CHART + PDF BUTTON
    # ──────────────────────────────────────────────────────────────────

    if rec.saving and fmt != FormatoLeilao.NAO_LEILAO:
        st.divider()
        st.subheader(t("saving_estimate", lang))
        s = rec.saving

        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            st.metric(t("pessimistic", lang), f"{s.pessimista_pct:.1f}%",
                      delta=_fmt_brl(s.pessimista_brl) if s.pessimista_brl else None)
        with sc2:
            st.metric(t("realistic", lang), f"{s.realista_pct:.1f}%",
                      delta=_fmt_brl(s.realista_brl) if s.realista_brl else None)
        with sc3:
            st.metric(t("optimistic", lang), f"{s.otimista_pct:.1f}%",
                      delta=_fmt_brl(s.otimista_brl) if s.otimista_brl else None)

        if s.pessimista_pct == s.realista_pct == s.otimista_pct and s.pessimista_pct > 0:
            st.caption(t("saving_flat_warning", lang))

        if inp.melhor_proposta_brl:
            best = inp.melhor_proposta_brl
            cp1, cp2, cp3 = st.columns(3)
            with cp1:
                close_pess = round(best * (1 - s.pessimista_pct / 100), 2)
                st.metric(
                    t("projected_close_pessimistic", lang),
                    _fmt_brl(close_pess),
                    delta=f"−{_fmt_brl(s.pessimista_brl)}" if s.pessimista_brl else None,
                    delta_color="inverse",
                )
            with cp2:
                close_real = round(best * (1 - s.realista_pct / 100), 2)
                st.metric(
                    t("projected_close_realistic", lang),
                    _fmt_brl(close_real),
                    delta=f"−{_fmt_brl(s.realista_brl)}" if s.realista_brl else None,
                    delta_color="inverse",
                )
            with cp3:
                close_otim = round(best * (1 - s.otimista_pct / 100), 2)
                st.metric(
                    t("projected_close_optimistic", lang),
                    _fmt_brl(close_otim),
                    delta=f"−{_fmt_brl(s.otimista_brl)}" if s.otimista_brl else None,
                    delta_color="inverse",
                )

        # ── Uncertainty chart ─────────────────────────────────────────
        _fig, _has_chart = draw_uncertainty_chart(
            sim.alvos_por_fornecedor,
            dark=False,
            lang=lang,
        )
        if _has_chart:
            import matplotlib.pyplot as plt
            st.pyplot(_fig, use_container_width=True)
            plt.close(_fig)
        else:
            st.caption(t("chart_no_data", lang))

        # PDF button below chart
        pdf_bytes = exportador.gerar_pdf(inp, rec, sim, lang=lang)
        _pdf_col, _ = st.columns([1, 3])
        with _pdf_col:
            st.download_button(
                label=t("download_pdf", lang),
                data=pdf_bytes,
                file_name="bidwise_report.pdf",
                mime="application/pdf",
                type="primary",
                width="stretch",
            )

        # Specific disclaimer
        st.caption(t("disclaimer_template", lang).format(
            format=_format_label(fmt, lang),
            n=inp.num_fornecedores,
            spread=inp.dispersao_precos,
        ))

    # ──────────────────────────────────────────────────────────────────
    # 4. SUPPLIER BEHAVIOR SIMULATION
    # ──────────────────────────────────────────────────────────────────

    st.divider()
    st.subheader(t("simulation", lang))

    if fmt != FormatoLeilao.NAO_LEILAO and sim.fornecedores:
        # ── Archetype cards ───────────────────────────────────────────
        _ARQ_DESC = {
            "Aggressive Leader":  t("archetype_aggressive", lang),
            "Cautious Follower":  t("archetype_cautious", lang),
            "Floor-setter":       t("archetype_floor", lang),
            "Dropout Candidate":  t("archetype_dropout", lang),
        }
        _ARQ_ORDER = ["Aggressive Leader", "Cautious Follower", "Floor-setter", "Dropout Candidate"]
        _arq_grupos: dict[str, list[str]] = {}
        for _fs in sim.fornecedores:
            _arq_key = _fs.arquetipo.value
            _arq_grupos.setdefault(_arq_key, []).append(_fs.nome_original or f"Supplier {_fs.id}")
        _present = [(n, _arq_grupos[n]) for n in _ARQ_ORDER if n in _arq_grupos]
        if _present:
            _arq_cols = st.columns(len(_present))
            for _col, (_arq_name, _nomes) in zip(_arq_cols, _present):
                with _col:
                    _sup_lines = "<br>".join(_nomes)
                    _desc = _ARQ_DESC.get(_arq_name, "")
                    st.markdown(
                        f"<div class='bw-archetype-card'>"
                        f"<span class='bw-archetype-card__count'>{len(_nomes)}</span><br>"
                        f"<b>{_arq_name}</b><br>"
                        f"<i class='bw-archetype-card__desc'>{_desc}</i><br>"
                        f"{_sup_lines}"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
        st.write("")

        st.markdown(sim.narrativa)

        if sim.vencedor_provavel and sim.preco_final_estimado_pct is not None:
            _saving_pct = abs(sim.preco_final_estimado_pct)
            _vs_label = "vs. melhor preço de equalização" if lang == "pt" else "vs. best equalization price"
            _close_str = (
                f" ({_fmt_brl(round(inp.melhor_proposta_brl * (1 - _saving_pct / 100), 2))}, "
                f"−{_saving_pct:.1f}% {_vs_label})"
                if inp.melhor_proposta_brl else
                f" (−{_saving_pct:.1f}% {_vs_label})"
            )
            st.info(f"{t('projected_outcome', lang)}{_close_str}")

    if sim.alertas:
        for alerta in sorted(
            sim.alertas,
            key=lambda a: {"Alta": 0, "Média": 1, "Baixa": 2}[a.severidade],
        ):
            msg = f"**{alerta.tipo.value}** — {alerta.descricao}"
            if alerta.tipo.value == "Low auction ROI":
                st.info(msg, icon="💡")
            elif alerta.severidade == "Alta":
                st.error(msg, icon="🚨")
            elif alerta.severidade == "Média":
                st.warning(msg, icon="⚠️")
            else:
                st.info(msg, icon="ℹ️")

    # ──────────────────────────────────────────────────────────────────
    # 5. COMPARE SCENARIOS
    # ──────────────────────────────────────────────────────────────────

    st.divider()
    st.subheader(t("compare", lang))

    _scenario_default_prefix = "Cenário" if lang == "pt" else "Scenario"

    if len(st.session_state.scenarios) >= 3:
        st.caption(t("compare_max", lang))
    else:
        name_col, btn_col = st.columns([3, 1])
        with name_col:
            scenario_name = st.text_input(
                "Scenario name",
                placeholder=t("scenario_name_placeholder", lang),
                label_visibility="collapsed",
                key="scenario_name_input",
            )
        with btn_col:
            if st.button(t("save_scenario", lang), type="secondary"):
                label = scenario_name.strip() if scenario_name.strip() else f"{_scenario_default_prefix} {len(st.session_state.scenarios) + 1}"
                st.session_state.scenarios.append({
                    "label": label,
                    "inp":   inp,
                    "rec":   rec,
                    "sim":   sim,
                })
                st.success(t("scenario_saved", lang).format(label=label))

    if len(st.session_state.scenarios) == 0:
        st.caption(t("compare_hint", lang))
    else:
        if st.button(t("clear_all", lang), type="secondary"):
            st.session_state.scenarios = []
            st.rerun()

        n_saved = len(st.session_state.scenarios)
        cols = st.columns(max(n_saved, 2))
        for col, scenario in zip(cols[:n_saved], st.session_state.scenarios):
            with col:
                r = scenario["rec"]
                s_sim = scenario["sim"]
                color = FORMAT_COLOR[r.formato]
                st.markdown(
                    f"<div class='bw-scenario-card' style='--bw-format-accent:{color};'>"
                    f"<b>{FORMAT_EMOJI[r.formato]} {scenario['label']}</b><br>"
                    f"<span class='bw-scenario-card__format'>{_format_label(r.formato, lang)}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                st.markdown("")
                if r.saving:
                    sv = r.saving
                    st.markdown(
                        f"{t('col_saving', lang)} {sv.pessimista_pct:.1f}% / "
                        f"{sv.realista_pct:.1f}% / {sv.otimista_pct:.1f}%"
                    )
                if r.parametros:
                    p_s = r.parametros
                    st.markdown(f"{t('col_decrement', lang)} {p_s.decremento_min_pct:.2f}%")
                    st.markdown(f"{t('col_duration', lang)} {p_s.duracao_minutos} min")
                    if p_s.rodadas_estimadas:
                        st.markdown(f"{t('col_rounds', lang)} ~{p_s.rodadas_estimadas}")
                if s_sim.preco_final_estimado_pct is not None:
                    _vs = "vs. melhor equalização" if lang == "pt" else "vs. best equalization"
                    st.markdown(
                        f"{t('col_projected', lang)} −{abs(s_sim.preco_final_estimado_pct):.1f}% {_vs}"
                    )

        if n_saved == 1:
            st.info(t("compare_one_saved", lang), icon="💡")

    # ──────────────────────────────────────────────────────────────────
    # 6. TAKE TO AI
    # ──────────────────────────────────────────────────────────────────

    st.divider()
    with st.expander(t("take_to_ai", lang)):
        prompt_text = _build_copy_prompt(inp, rec, sim, lang=lang)
        st.code(prompt_text, language=None)
        st.caption(t("copy_prompt_hint", lang))

    # ──────────────────────────────────────────────────────────────────
    # 7. THEORETICAL REFERENCES
    # ──────────────────────────────────────────────────────────────────

    with st.expander(t("theoretical", lang), expanded=False):
        if rec.referencias:
            _ref_book  = "Livro"    if lang == "pt" else "Book"
            _ref_auth  = "Autor"    if lang == "pt" else "Author"
            _ref_conc  = "Conceito" if lang == "pt" else "Concept"
            _ref_appl  = "Aplicação" if lang == "pt" else "Application"
            rows_ref = [
                {
                    _ref_book: r.livro,
                    _ref_auth: r.autor,
                    _ref_conc: r.conceito,
                    _ref_appl: r.aplicacao,
                }
                for r in rec.referencias
            ]
            st.table(pd.DataFrame(rows_ref))
        else:
            st.caption(t("no_references", lang))

    # ──────────────────────────────────────────────────────────────────
    # FOOTER
    # ──────────────────────────────────────────────────────────────────

    st.divider()
    st.markdown(
        f"""
        <div class="bw-footer">
            <a href="https://www.linkedin.com/in/henriquealexandresilva/" target="_blank" rel="noopener noreferrer">
                <b>Henrique Silva</b>
            </a>
            &nbsp;·&nbsp;
            {"Strategic Sourcing Analyst" if lang == "en" else "Strategic Sourcing Analyst"}
            &nbsp;·&nbsp;
            <a href="https://github.com/HenriqueAPSilva/bidwise">
                {t("github_link", lang)}
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )
