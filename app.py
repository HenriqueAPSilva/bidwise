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
    page_icon="🔨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────
# SIDEBAR VISIBILITY — inject before any rendering
# ──────────────────────────────────────────────────────────────────────

if st.session_state.get("sidebar_hidden", False):
    st.markdown(
        '<style>[data-testid="stSidebar"] {display: none;}</style>',
        unsafe_allow_html=True,
    )

# ──────────────────────────────────────────────────────────────────────
# LANGUAGE SELECTION — must happen before any t() calls
# ──────────────────────────────────────────────────────────────────────

_lang_raw = st.sidebar.radio(
    "🌐",
    ["EN", "PT-BR"],
    horizontal=True,
    label_visibility="collapsed",
    key="lang_selector",
)
lang: str = "pt" if _lang_raw == "PT-BR" else "en"

st.markdown("""<style>
[data-testid="stSidebar"] {min-width: 420px; max-width: 420px;}
@media (max-width: 1080px) {
    [data-testid="stSidebar"] {
        min-width: 100vw !important;
        max-width: 100vw !important;
        width: 100vw !important;
        z-index: 999;
        position: fixed;
        left: 0;
        top: 0;
    }
    [data-testid="stSidebar"][aria-expanded="false"] {
        display: none !important;
    }
    section[data-testid="stMain"] {
        margin-left: 0 !important;
        width: 100vw !important;
    }
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
    "Alavanca":     QuadranteKraljic.ALAVANCA,
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
    FormatoLeilao.INGLES_COMPLETO: "#1A56A0",
    FormatoLeilao.INGLES_REDUZIDO: "#0E7C7B",
    FormatoLeilao.HOLANDES:        "#6B21A8",
    FormatoLeilao.JAPONES:         "#B45309",
    FormatoLeilao.NAO_LEILAO:      "#B91C1C",
}

FORMAT_LABEL_EN: dict[FormatoLeilao, str] = {
    FormatoLeilao.INGLES_COMPLETO: "English Reverse — Ranking + Thermometer",
    FormatoLeilao.INGLES_REDUZIDO: "English Reverse — Ranking Only",
    FormatoLeilao.HOLANDES:        "Dutch Reverse",
    FormatoLeilao.JAPONES:         "Japanese Reverse",
    FormatoLeilao.NAO_LEILAO:      "Do Not Auction",
}

FORMAT_LABEL_PT: dict[FormatoLeilao, str] = {
    FormatoLeilao.INGLES_COMPLETO: "English Reverse — Ranking + Termômetro",
    FormatoLeilao.INGLES_REDUZIDO: "English Reverse — Apenas Ranking",
    FormatoLeilao.HOLANDES:        "Dutch Reverse",
    FormatoLeilao.JAPONES:         "Japanese Reverse",
    FormatoLeilao.NAO_LEILAO:      "Não Fazer Leilão",
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


def _build_copy_prompt(inp: InputLeilao, rec, sim) -> str:
    """Generate a structured prompt the user can paste into any AI assistant."""
    _KRALJIC_EN = {
        "Alavanca": "Leverage", "Estratégico": "Strategic",
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
    f'<div style="background-color:#1a1a2e;color:white;padding:8px 16px;text-align:center;'
    f'font-size:14px;border-radius:4px;margin-bottom:16px;">'
    f'{t("privacy_bar", lang)}'
    f'</div>',
    unsafe_allow_html=True,
)

tab_main, tab_about = st.tabs([t("tab_advisor", lang), t("tab_about", lang)])

if st.session_state.pop("show_about", False):
    st.markdown(
        """<script>
        (function() {
            const tabs = window.parent.document.querySelectorAll('button[role="tab"]');
            if (tabs.length >= 2) tabs[1].click();
        })();
        </script>""",
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════════
# ABOUT TAB
# ══════════════════════════════════════════════════════════════════════

with tab_about:
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

with tab_main:

    # ── Return button — always visible when sidebar is hidden ─────────
    if st.session_state.get("sidebar_hidden", False) or st.session_state.get("sidebar_collapsed", False):
        if st.button(t("configure_scenario", lang), use_container_width=True, key="show_sidebar_again"):
            st.session_state["sidebar_hidden"] = False
            st.session_state["sidebar_collapsed"] = False
            st.session_state["show_about"] = False
            st.rerun()

    # ──────────────────────────────────────────────────────────────────
    # HEADER
    # ──────────────────────────────────────────────────────────────────

    st.markdown(
        f"""
        <div style="padding-bottom: 4px;">
            <span style="font-size:2.4rem; font-weight:800; color:#F0E68C;">🔨 BidWise</span>
            &nbsp;
            <span style="font-size:1.1rem; color:#374151; font-weight:500;">
                {"Consultor de Estratégia de Leilão Reverso" if lang == "pt" else "Reverse Auction Strategy Advisor"}
            </span>
        </div>
        <div style="color:#6B7280; font-size:0.88rem; margin-bottom:1rem;">
            {t("tagline", lang)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ──────────────────────────────────────────────────────────────────
    # SIDEBAR — INPUT FORM
    # ──────────────────────────────────────────────────────────────────

    with st.sidebar:
        if "last_rec" in st.session_state:
            if st.button(t("view_report", lang), use_container_width=True, key="view_report_top"):
                st.session_state["sidebar_hidden"] = True
                st.rerun()
        else:
            st.info(t("sidebar_no_analysis_tip", lang))
            if st.button(t("about_from_sidebar", lang), use_container_width=True, key="about_from_sidebar"):
                st.session_state["sidebar_hidden"] = True
                st.session_state["show_about"] = True
                st.rerun()

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

        analyze = st.button(t("analyze", lang), type="primary", use_container_width=True)
        if st.button(t("reset", lang), type="secondary", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        if "last_rec" in st.session_state:
            if st.button(t("view_report", lang), use_container_width=True, key="view_report_bottom"):
                st.session_state["sidebar_hidden"] = True
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

    # Gate: show prompt if no analysis yet
    if "last_rec" not in st.session_state:
        st.info(t("get_started", lang))
        st.stop()

    inp = st.session_state.last_inp
    rec = st.session_state.last_rec
    sim = st.session_state.last_sim

    if inp.dispersao_precos > 50:
        st.warning(t("spread_warning", lang))

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
                f"<h2 style='color:{fmt_color}; margin-bottom:0;'>"
                f"{fmt_emoji} {_format_label(fmt, lang)}</h2>",
                unsafe_allow_html=True,
            )
            st.markdown(rec.justificativa)

    st.markdown("---")

    # ──────────────────────────────────────────────────────────────────
    # 1b. OPENING PRICE OVERRIDE
    # ──────────────────────────────────────────────────────────────────

    # Compute effective opening price (read-only override, rec is not mutated)
    _eff_abertura_pct: float | None = rec.parametros.preco_abertura_pct if rec.parametros else None
    _eff_abertura_brl: float | None = rec.parametros.preco_abertura_brl if rec.parametros else None

    _is_english = fmt in (FormatoLeilao.INGLES_COMPLETO, FormatoLeilao.INGLES_REDUZIDO)

    if rec.parametros and fmt != FormatoLeilao.NAO_LEILAO and not _is_english:
        _bidwise_pct = rec.parametros.preco_abertura_pct
        _op_suggestion = t("opening_suggestion", lang).format(pct=_bidwise_pct)
        _op_options = [
            _op_suggestion,
            t("opening_equalization", lang),
            t("opening_custom", lang),
        ]
        _op_strategy = st.radio(
            t("opening_strategy", lang),
            options=_op_options,
            index=0,
            horizontal=True,
        )

        _is_ceiling = _op_strategy == t("opening_equalization", lang)
        _is_custom = _op_strategy == t("opening_custom", lang)

        if _is_ceiling:
            if inp.melhor_proposta_brl is not None:
                _eff_abertura_pct = 0.0
                _eff_abertura_brl = inp.melhor_proposta_brl
            else:
                st.warning(t("opening_ceiling_warning", lang), icon="⚠️")
        elif _is_custom:
            _custom_pct = st.slider(
                t("opening_custom_label", lang),
                min_value=-20,
                max_value=10,
                value=int(_bidwise_pct) if _bidwise_pct else -5,
                step=1,
            )
            _eff_abertura_pct = float(_custom_pct)
            if inp.melhor_proposta_brl is not None:
                _eff_abertura_brl = round(
                    inp.melhor_proposta_brl * (1 + _custom_pct / 100), 2
                )

        st.markdown("---")

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
            if _is_english:
                ap_pct_str = t("best_response", lang)
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

        if _is_english:
            _opening_val = t("best_response", lang)
            _opening_brl = t("best_response_note", lang)
        else:
            _opening_val = f"{_eff_abertura_pct:+.1f}%" if _eff_abertura_pct is not None else "—"
            _opening_brl = _fmt_brl(_eff_abertura_brl)

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
        _fig, _has_chart = draw_uncertainty_chart(sim.alvos_por_fornecedor)
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
                use_container_width=True,
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
        # ── Archetype cards (stacked, one per archetype present) ──────
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
                        f"<div style='text-align:center;'>"
                        f"<span style='font-size:48px;font-weight:bold;line-height:1.1;'>{len(_nomes)}</span><br>"
                        f"<b>{_arq_name}</b><br>"
                        f"{_sup_lines}<br>"
                        f"<i style='color:gray;font-size:13px;'>{_desc}</i>"
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
            if alerta.severidade == "Alta":
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
                    f"<div style='border-left: 4px solid {color}; padding-left: 8px;'>"
                    f"<b>{FORMAT_EMOJI[r.formato]} {scenario['label']}</b><br>"
                    f"<span style='color:{color}; font-size:0.9rem;'>{_format_label(r.formato, lang)}</span>"
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
        prompt_text = _build_copy_prompt(inp, rec, sim)
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
        <div style="text-align:center; color:#9CA3AF; font-size:0.8rem; padding-bottom:1rem;">
            {t("footer_text", lang)} &nbsp;·&nbsp;
            <a href="https://github.com/HenriqueAPSilva/bidwise" style="color:#9CA3AF;">
                {t("github_link", lang)}
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )
