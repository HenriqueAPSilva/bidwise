"""
app.py — Interface Streamlit principal do BidWise
Autor: Henrique Alexandre Pinto Silva
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

import exportador
from exportador import draw_uncertainty_chart
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

st.markdown("""<style>
[data-testid="stSidebar"] {min-width: 420px; max-width: 420px;}
</style>""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────
# DROPDOWN OPTIONS — descriptive labels
# ──────────────────────────────────────────────────────────────────────

KRALJIC_OPTIONS = [
    "Leverage — High impact, low risk",
    "Strategic — High impact, high risk",
    "Bottleneck — Low impact, high risk",
    "Non-critical — Low impact, low risk",
]
_KRALJIC_ENUM: dict[str, QuadranteKraljic] = {
    "Leverage":     QuadranteKraljic.ALAVANCA,
    "Strategic":    QuadranteKraljic.ESTRATEGICO,
    "Bottleneck":   QuadranteKraljic.GARGALO,
    "Non-critical": QuadranteKraljic.NAO_CRITICO,
}

COMOD_OPTIONS = [
    "High — Standard specs, many suppliers",
    "Medium — Some differentiation, limited alternatives",
    "Low — Custom/proprietary, few substitutes",
]
_COMOD_ENUM: dict[str, NivelTripartido] = {
    "High":   NivelTripartido.ALTO,
    "Medium": NivelTripartido.MEDIO,
    "Low":    NivelTripartido.BAIXO,
}


BEHAVIOR_OPTIONS = [
    "Competitive — Bids aggressively, responds to pressure",
    "Moderate — Calculated bids, doesn't overextend",
    "Conservative — Risk-averse, may withdraw if pushed",
]
_BEHAVIOR_ENUM: dict[str, Comportamento] = {
    "Competitive":  Comportamento.COMPETITIVO,
    "Moderate":     Comportamento.MODERADO,
    "Conservative": Comportamento.CONSERVADOR,
}

INTEREST_OPTIONS = [
    "High — Wants contract for future revenue, will bid hard",
    "Medium — Interested but not dependent on winning",
    "Low — Indifferent, may not bid actively",
]


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

MECH_LABEL_EN: dict[str, str] = {
    "RFQ com negociação posterior":                "RFQ with subsequent negotiation",
    "Nova rodada de qualificação + RFQ":           "New qualification round + RFQ",
    "Negociação direta com fornecedor":            "Direct negotiation with supplier",
    "Contrato guarda-chuva com revisão periódica": "Umbrella contract with periodic review",
}


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
    '<div style="background-color:#1a1a2e;color:white;padding:8px 16px;text-align:center;'
    'font-size:14px;border-radius:4px;margin-bottom:16px;">'
    '🔒 No cookies · No tracking · No data stored · Your scenarios exist only in your active session'
    '</div>',
    unsafe_allow_html=True,
)

tab_main, tab_about = st.tabs(["Auction Advisor", "About BidWise"])

# ══════════════════════════════════════════════════════════════════════
# ABOUT TAB
# ══════════════════════════════════════════════════════════════════════

with tab_about:
    with open("about.md", encoding="utf-8") as _f:
        st.markdown(_f.read())

# ══════════════════════════════════════════════════════════════════════
# MAIN TAB — AUCTION ADVISOR
# ══════════════════════════════════════════════════════════════════════

with tab_main:

    # ──────────────────────────────────────────────────────────────────
    # HEADER
    # ──────────────────────────────────────────────────────────────────

    st.markdown(
        """
        <div style="padding-bottom: 4px;">
            <span style="font-size:2.4rem; font-weight:800; color:#F0E68C;">🔨 BidWise</span>
            &nbsp;
            <span style="font-size:1.1rem; color:#374151; font-weight:500;">
                Reverse Auction Strategy Advisor
            </span>
        </div>
        <div style="color:#6B7280; font-size:0.88rem; margin-bottom:1rem;">
            Powered by auction theory &amp; Coupa platform rules
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ──────────────────────────────────────────────────────────────────
    # SIDEBAR — INPUT FORM
    # ──────────────────────────────────────────────────────────────────

    with st.sidebar:
        st.markdown("### Configure your auction")

        # ── Auction context ──────────────────────────────────────────
        kraljic_label = st.selectbox(
            "Kraljic quadrant",
            options=KRALJIC_OPTIONS,
            index=0,  # Leverage
            help=(
                "Position of this item on the Kraljic matrix. "
                "Leverage items (high spend, many suppliers) are the best auction candidates. "
                "Strategic items carry supply-continuity risk — auction with caution. "
                "Bottleneck items have few substitutes and respond poorly to price pressure. "
                "Non-critical items have low strategic relevance."
            ),
        )

        comod_label = st.selectbox(
            "Item commoditization",
            options=COMOD_OPTIONS,
            index=0,  # High
            help=(
                "How interchangeable this item is across suppliers. "
                "High: standard spec, any qualified supplier can deliver identically — "
                "auctions work best here. "
                "Medium: some differentiation exists but alternatives are available. "
                "Low: custom or proprietary spec — price comparison may be misleading."
            ),
        )

        st.divider()

        # ── Supplier profiles ────────────────────────────────────────
        st.markdown("#### Supplier profiles")
        n_suppliers = st.number_input(
            "Number of qualified suppliers",
            min_value=1,
            max_value=15,
            value=4,
            step=1,
            help="Total suppliers invited and qualified to participate.",
        )

        _supplier_inputs: list[dict] = []
        for _i in range(int(n_suppliers)):
            _default_name = f"Supplier {chr(65 + _i)}"  # A, B, C, ...
            with st.expander(_default_name, expanded=(_i == 0)):
                _name = st.text_input(
                    "Name",
                    value=_default_name,
                    key=f"sup_name_{_i}",
                )
                _prop = st.number_input(
                    "Proposal value ($)",
                    min_value=0.0,
                    value=0.0,
                    step=1_000.0,
                    format="%.2f",
                    key=f"sup_prop_{_i}",
                    help=(
                        "Enter the equalized proposal value from the prior quotation round "
                        "(RFQ/RFP). All calculations are performed locally in your browser "
                        "— no data is transmitted."
                    ),
                )
                _int_label = st.selectbox(
                    "Strategic interest",
                    options=INTEREST_OPTIONS,
                    index=1,  # Medium
                    key=f"sup_int_{_i}",
                    help=(
                        "How much this supplier needs this contract. "
                        "High: strategic account for them — they will bid hard to win. "
                        "Medium: interested but winning is not critical. "
                        "Low: indifferent — may not bid actively or may withdraw."
                    ),
                )
                _beh_label = st.selectbox(
                    "Behavior",
                    options=BEHAVIOR_OPTIONS,
                    index=1,  # Moderate
                    key=f"sup_beh_{_i}",
                    help=(
                        "Expected bidding style based on past interactions or market knowledge. "
                        "Competitive: bids aggressively and responds quickly to being outbid. "
                        "Moderate: calculated approach, bids when meaningful moves are available. "
                        "Conservative: risk-averse, may withdraw if the auction gets too aggressive."
                    ),
                )
                _supplier_inputs.append({
                    "name":     _name,
                    "proposal": _prop,
                    "interest": _extract_key(_int_label),
                    "behavior": _extract_key(_beh_label),
                })

        _props_entered = [s for s in _supplier_inputs if s["proposal"] > 0]
        if len(_props_entered) < 2:
            st.info(
                "Tip: Enter at least 2 supplier proposals for a more accurate "
                "spread calculation."
            )

        analyze = st.button("Analyze", type="primary", use_container_width=True)
        if st.button("🔄 Reset", type="secondary", use_container_width=True):
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

    _INTEREST_ENUM: dict[str, NivelTripartido] = {
        "High":   NivelTripartido.ALTO,
        "Medium": NivelTripartido.MEDIO,
        "Low":    NivelTripartido.BAIXO,
    }

    if analyze:
        _fornecedores = [
            Fornecedor(
                nome=s["name"],
                proposta_brl=s["proposal"] if s["proposal"] > 0 else None,
                interesse_estrategico=_INTEREST_ENUM[s["interest"]],
                comportamento=_BEHAVIOR_ENUM[s["behavior"]],
            )
            for s in _supplier_inputs
        ]

        inp = InputLeilao(
            fornecedores=_fornecedores,
            kraljic=_KRALJIC_ENUM[_extract_key(kraljic_label)],
            comoditizacao=_COMOD_ENUM[_extract_key(comod_label)],
        )

        rec = recomendar(inp)
        sim = simular(inp, rec)

        st.session_state.last_inp = inp
        st.session_state.last_rec = rec
        st.session_state.last_sim = sim

    # Gate: show prompt if no analysis yet
    if "last_rec" not in st.session_state:
        st.info(
            "Configure your auction parameters in the sidebar and click **Analyze** to get started."
        )
        st.stop()

    inp = st.session_state.last_inp
    rec = st.session_state.last_rec
    sim = st.session_state.last_sim

    if inp.dispersao_precos > 50:
        st.warning(
            "⚠️ Price spread exceeds 50%. Consider reviewing equalization data for outliers."
        )

    # ──────────────────────────────────────────────────────────────────
    # 1. RECOMMENDATION CARD
    # ──────────────────────────────────────────────────────────────────

    fmt = rec.formato
    fmt_color = FORMAT_COLOR[fmt]
    fmt_emoji = FORMAT_EMOJI[fmt]

    if fmt == FormatoLeilao.NAO_LEILAO:
        with st.container(border=True):
            st.error(
                f"**{fmt_emoji} {FORMAT_LABEL_EN[fmt]}**\n\n"
                f"{rec.alerta_nao_leilao.explicacao if rec.alerta_nao_leilao else rec.justificativa}",
                icon="🚫",
            )
            if rec.alerta_nao_leilao:
                mech_en = MECH_LABEL_EN.get(
                    rec.alerta_nao_leilao.mecanismo_sugerido.value,
                    rec.alerta_nao_leilao.mecanismo_sugerido.value,
                )
                st.markdown(f"**Suggested mechanism:** {mech_en}")
    else:
        with st.container(border=True):
            st.markdown(
                f"<h2 style='color:{fmt_color}; margin-bottom:0;'>"
                f"{fmt_emoji} {FORMAT_LABEL_EN[fmt]}</h2>",
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
        _op_options = [
            f"Use BidWise suggestion ({_bidwise_pct:+.1f}% vs. best proposal)",
            "Use best proposal as ceiling (0% adjustment)",
            "Custom adjustment",
        ]
        _op_strategy = st.radio(
            "Opening price strategy",
            options=_op_options,
            index=0,
            horizontal=True,
            help=(
                "BidWise suggestion uses format-specific formulas. "
                "Custom lets you set any adjustment vs. the best proposal."
            ),
        )

        if "ceiling" in _op_strategy.lower():
            if inp.melhor_proposta_brl is not None:
                _eff_abertura_pct = 0.0
                _eff_abertura_brl = inp.melhor_proposta_brl
            else:
                st.warning(
                    "Ceiling option requires at least one supplier proposal with a value. "
                    "Using BidWise suggestion instead.",
                    icon="⚠️",
                )
        elif "custom" in _op_strategy.lower():
            _custom_pct = st.slider(
                "Custom opening price (% vs. best proposal)",
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
        st.subheader("Optimized Parameters")
        p = rec.parametros

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            brl_str = f"$ {p.decremento_min_brl:,.0f}" if p.decremento_min_brl else None
            st.metric("Min. Decrement", f"{p.decremento_min_pct:.2f}%", delta=brl_str)
        with c2:
            ap_brl_str = f"$ {_eff_abertura_brl:,.0f}" if _eff_abertura_brl else None
            if _is_english:
                ap_pct_str = "Best Response"
            elif _eff_abertura_pct is not None:
                ap_pct_str = f"{_eff_abertura_pct:+.1f}%"
            else:
                ap_pct_str = "—"
            st.metric("Opening", ap_pct_str, delta=ap_brl_str)
        with c3:
            ext_str = f"+{p.prorrogacao_minutos} min auto-ext." if p.prorrogacao_minutos else None
            st.metric("Duration", f"{p.duracao_minutos} min", delta=ext_str)
        with c4:
            if p.rodadas_estimadas:
                st.metric(
                    "Est. Rounds", f"~{p.rodadas_estimadas}",
                    delta=f"{p.intervalo_rodada_minutos} min / round" if p.intervalo_rodada_minutos else None,
                )
            elif p.incremento_holandes_pct:
                inc_brl = f"$ {p.incremento_holandes_brl:,.0f}/tick" if p.incremento_holandes_brl else None
                st.metric("Dutch Increment", f"{p.incremento_holandes_pct:.2f}%/tick", delta=inc_brl)
            elif p.visibilidade:
                enabled = "Enabled" if "Enabled" in p.visibilidade else "Disabled"
                st.metric("Thermometer", enabled)

        _opening_label = "Opening price"
        if _is_english:
            _opening_val = "Best Response"
            _opening_brl = "Suppliers enter with equalized prices"
        else:
            _opening_val = f"{_eff_abertura_pct:+.1f}%" if _eff_abertura_pct is not None else "—"
            _opening_brl = _fmt_brl(_eff_abertura_brl)

        rows = [
            ("Minimum decrement", f"{p.decremento_min_pct:.2f}%", _fmt_brl(p.decremento_min_brl)),
            (_opening_label, _opening_val, _opening_brl),
            ("Auction duration", f"{p.duracao_minutos} min", "—"),
        ]
        if p.prorrogacao_minutos:
            rows.append((
                f"Auto-extension (if bid in last {p.prorrogacao_trigger_minutos} min)",
                f"+{p.prorrogacao_minutos} min", "—",
            ))
        if p.visibilidade:
            rows.append(("Thermometer visibility", p.visibilidade, "—"))
        if p.rodadas_estimadas:
            rows.append((
                f"Estimated rounds ({p.intervalo_rodada_minutos} min each)",
                f"~{p.rodadas_estimadas}", "—",
            ))
        if p.incremento_holandes_pct:
            rows.append((
                "Dutch increment per tick",
                f"{p.incremento_holandes_pct:.2f}%",
                _fmt_brl(p.incremento_holandes_brl),
            ))

        st.dataframe(
            pd.DataFrame(rows, columns=["Parameter", "Value (%)", "Value ($)"]),
            use_container_width=True,
            hide_index=True,
        )
        st.markdown("---")

    # ──────────────────────────────────────────────────────────────────
    # 3. SAVING ESTIMATE + CHART + PDF BUTTON
    # ──────────────────────────────────────────────────────────────────

    if rec.saving and fmt != FormatoLeilao.NAO_LEILAO:
        st.divider()
        st.subheader("Saving Estimate")
        s = rec.saving

        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            st.metric("Pessimistic saving", f"{s.pessimista_pct:.1f}%",
                      delta=_fmt_brl(s.pessimista_brl) if s.pessimista_brl else None)
        with sc2:
            st.metric("Realistic saving", f"{s.realista_pct:.1f}%",
                      delta=_fmt_brl(s.realista_brl) if s.realista_brl else None)
        with sc3:
            st.metric("Optimistic saving", f"{s.otimista_pct:.1f}%",
                      delta=_fmt_brl(s.otimista_brl) if s.otimista_brl else None)

        if inp.melhor_proposta_brl:
            best = inp.melhor_proposta_brl
            cp1, cp2, cp3 = st.columns(3)
            with cp1:
                close_pess = round(best * (1 - s.pessimista_pct / 100), 2)
                st.metric(
                    "Projected close (pessimistic)",
                    _fmt_brl(close_pess),
                    delta=f"−{_fmt_brl(s.pessimista_brl)}" if s.pessimista_brl else None,
                    delta_color="inverse",
                )
            with cp2:
                close_real = round(best * (1 - s.realista_pct / 100), 2)
                st.metric(
                    "Projected close (realistic)",
                    _fmt_brl(close_real),
                    delta=f"−{_fmt_brl(s.realista_brl)}" if s.realista_brl else None,
                    delta_color="inverse",
                )
            with cp3:
                close_otim = round(best * (1 - s.otimista_pct / 100), 2)
                st.metric(
                    "Projected close (optimistic)",
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
            st.caption(
                "Enter supplier proposal values to see the uncertainty projection chart."
            )

        # PDF button below chart
        pdf_bytes = exportador.gerar_pdf(inp, rec, sim)
        _pdf_col, _ = st.columns([1, 3])
        with _pdf_col:
            st.download_button(
                label="📄 Download PDF",
                data=pdf_bytes,
                file_name="bidwise_report.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True,
            )

        # Specific disclaimer
        st.caption(
            f"Estimates based on {FORMAT_LABEL_EN[fmt]} dynamics with "
            f"{inp.num_fornecedores} suppliers and {inp.dispersao_precos:.1f}% price spread. "
            f"Actual results depend on market conditions and real-time supplier behavior."
        )

    # ──────────────────────────────────────────────────────────────────
    # 4. SUPPLIER BEHAVIOR SIMULATION
    # ──────────────────────────────────────────────────────────────────

    st.divider()
    st.subheader("Supplier Behavior Simulation")

    if fmt != FormatoLeilao.NAO_LEILAO and sim.fornecedores:
        # ── Archetype cards (stacked, one per archetype present) ──────
        _ARQ_DESC = {
            "Aggressive Leader":  "Bids early and aggressively to discourage competitors",
            "Cautious Follower":  "Watches ranking, activates in the final sprint",
            "Floor-setter":       "Marks initial position without revealing true price floor",
            "Dropout Candidate":  "Conservative or low interest — likely to withdraw early",
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
            _close_str = (
                f" ({_fmt_brl(round(inp.melhor_proposta_brl * (1 - _saving_pct / 100), 2))}, "
                f"−{_saving_pct:.1f}% vs. best equalization price)"
                if inp.melhor_proposta_brl else
                f" (−{_saving_pct:.1f}% vs. best equalization price)"
            )
            st.info(f"**Projected outcome:** {_close_str}")

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
    st.subheader("Compare Scenarios")

    if len(st.session_state.scenarios) >= 3:
        st.caption("Max 3 scenarios saved. Remove one to add more.")
    else:
        name_col, btn_col = st.columns([3, 1])
        with name_col:
            scenario_name = st.text_input(
                "Scenario name",
                placeholder="e.g., Base case, Aggressive, Conservative...",
                label_visibility="collapsed",
                key="scenario_name_input",
            )
        with btn_col:
            if st.button("Save scenario", type="secondary"):
                label = scenario_name.strip() if scenario_name.strip() else f"Scenario {len(st.session_state.scenarios) + 1}"
                st.session_state.scenarios.append({
                    "label": label,
                    "inp":   inp,
                    "rec":   rec,
                    "sim":   sim,
                })
                st.success(f"'{label}' saved.")

    if len(st.session_state.scenarios) == 0:
        st.caption("Save your current scenario to compare configurations side by side.")
    else:
        if st.button("🗑️ Clear all scenarios", type="secondary"):
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
                    f"<span style='color:{color}; font-size:0.9rem;'>{FORMAT_LABEL_EN[r.formato]}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                st.markdown("")
                if r.saving:
                    sv = r.saving
                    st.markdown(
                        f"**Saving:** {sv.pessimista_pct:.1f}% / "
                        f"{sv.realista_pct:.1f}% / {sv.otimista_pct:.1f}%"
                    )
                if r.parametros:
                    p_s = r.parametros
                    st.markdown(f"**Decrement:** {p_s.decremento_min_pct:.2f}%")
                    st.markdown(f"**Duration:** {p_s.duracao_minutos} min")
                    if p_s.rodadas_estimadas:
                        st.markdown(f"**Rounds:** ~{p_s.rodadas_estimadas}")
                if s_sim.preco_final_estimado_pct is not None:
                    st.markdown(
                        f"**Projected price:** −{abs(s_sim.preco_final_estimado_pct):.1f}% "
                        f"vs. best equalization"
                    )

        if n_saved == 1:
            st.info("Save another scenario to compare side by side.", icon="💡")

    # ──────────────────────────────────────────────────────────────────
    # 6. TAKE TO AI
    # ──────────────────────────────────────────────────────────────────

    st.divider()
    with st.expander("📋 Take this analysis to your preferred AI"):
        prompt_text = _build_copy_prompt(inp, rec, sim)
        st.code(prompt_text, language=None)
        st.caption(
            "Copy this prompt and paste it into any AI assistant you trust for a deeper analysis. "
            "No data leaves your browser unless you choose to share it."
        )

    # ──────────────────────────────────────────────────────────────────
    # 7. THEORETICAL REFERENCES
    # ──────────────────────────────────────────────────────────────────

    with st.expander("Theoretical Foundation", expanded=False):
        if rec.referencias:
            rows_ref = [
                {
                    "Book":        r.livro,
                    "Author":      r.autor,
                    "Concept":     r.conceito,
                    "Application": r.aplicacao,
                }
                for r in rec.referencias
            ]
            st.table(pd.DataFrame(rows_ref))
        else:
            st.caption("No references available for this scenario.")

    # ──────────────────────────────────────────────────────────────────
    # FOOTER
    # ──────────────────────────────────────────────────────────────────

    st.divider()
    st.markdown(
        """
        <div style="text-align:center; color:#9CA3AF; font-size:0.8rem; padding-bottom:1rem;">
            Built by <b>Henrique Silva</b> — Strategic Sourcing Analyst &nbsp;·&nbsp;
            <a href="https://github.com/HenriqueAPSilva/bidwise" style="color:#9CA3AF;">
                github.com/HenriqueAPSilva/bidwise
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )
