"""
exportador.py — Geração de relatório PDF com ReportLab
Autor: Henrique Alexandre Pinto Silva
Descrição: Gera relatório PDF completo da estratégia de leilão reverso.
           Retorna bytes — não salva em disco (uso com st.download_button).
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable,
    Image as RLImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from motor import FormatoLeilao, InputLeilao, Recomendacao
from simulador import SimulacaoResult, TipoAlerta
from i18n import t as _t

_FORMAT_LABEL_EN: dict[FormatoLeilao, str] = {
    FormatoLeilao.INGLES_COMPLETO: "English Reverse — Ranking + Thermometer",
    FormatoLeilao.INGLES_REDUZIDO: "English Reverse — Ranking Only",
    FormatoLeilao.HOLANDES:        "Dutch Reverse",
    FormatoLeilao.JAPONES:         "Japanese Reverse",
    FormatoLeilao.NAO_LEILAO:      "Do Not Auction",
}


# ──────────────────────────────────────────────────────────────────────
# PALETA DE CORES
# ──────────────────────────────────────────────────────────────────────

NAVY       = colors.HexColor("#0D2137")
BLUE       = colors.HexColor("#1A56A0")
LIGHT_BLUE = colors.HexColor("#EBF3FB")
TEAL       = colors.HexColor("#0E7C7B")
GREEN      = colors.HexColor("#1A7A4A")
GREEN_BG   = colors.HexColor("#E8F5EE")
AMBER      = colors.HexColor("#B45309")
AMBER_BG   = colors.HexColor("#FEF3C7")
RED        = colors.HexColor("#B91C1C")
RED_BG     = colors.HexColor("#FEE2E2")
GRAY_LIGHT = colors.HexColor("#F3F4F6")
GRAY_MID   = colors.HexColor("#9CA3AF")
GRAY_DARK  = colors.HexColor("#374151")
WHITE      = colors.white
BLACK      = colors.black

# Cor de destaque por formato
_FORMAT_COLORS: dict[FormatoLeilao, tuple] = {
    FormatoLeilao.INGLES_COMPLETO:  (BLUE,  LIGHT_BLUE),
    FormatoLeilao.INGLES_REDUZIDO:  (TEAL,  colors.HexColor("#E6F5F5")),
    FormatoLeilao.HOLANDES:         (colors.HexColor("#6B21A8"), colors.HexColor("#F3E8FF")),
    FormatoLeilao.JAPONES:          (colors.HexColor("#B45309"), colors.HexColor("#FEF9EE")),
    FormatoLeilao.NAO_LEILAO:       (RED,   RED_BG),
}


# ──────────────────────────────────────────────────────────────────────
# ESTILOS DE PARÁGRAFO
# ──────────────────────────────────────────────────────────────────────

def _build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()

    return {
        "logo": ParagraphStyle(
            "logo",
            fontName="Helvetica-Bold",
            fontSize=28,
            textColor=NAVY,
            leading=34,
            alignment=TA_LEFT,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            fontName="Helvetica",
            fontSize=11,
            textColor=GRAY_DARK,
            leading=14,
            alignment=TA_LEFT,
        ),
        "meta": ParagraphStyle(
            "meta",
            fontName="Helvetica",
            fontSize=9,
            textColor=GRAY_MID,
            leading=12,
            alignment=TA_RIGHT,
        ),
        "section_title": ParagraphStyle(
            "section_title",
            fontName="Helvetica-Bold",
            fontSize=12,
            textColor=NAVY,
            leading=16,
            spaceBefore=14,
            spaceAfter=4,
        ),
        "format_label": ParagraphStyle(
            "format_label",
            fontName="Helvetica-Bold",
            fontSize=15,
            textColor=WHITE,
            leading=20,
            alignment=TA_LEFT,
        ),
        "format_sublabel": ParagraphStyle(
            "format_sublabel",
            fontName="Helvetica",
            fontSize=9,
            textColor=WHITE,
            leading=12,
            alignment=TA_LEFT,
        ),
        "confidence": ParagraphStyle(
            "confidence",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=WHITE,
            leading=14,
            alignment=TA_RIGHT,
        ),
        "body": ParagraphStyle(
            "body",
            fontName="Helvetica",
            fontSize=9,
            textColor=GRAY_DARK,
            leading=13,
            spaceAfter=4,
        ),
        "body_card": ParagraphStyle(
            "body_card",
            fontName="Helvetica",
            fontSize=9,
            textColor=GRAY_DARK,
            leading=13,
        ),
        "table_header": ParagraphStyle(
            "table_header",
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=WHITE,
            leading=12,
            alignment=TA_CENTER,
        ),
        "table_cell": ParagraphStyle(
            "table_cell",
            fontName="Helvetica",
            fontSize=9,
            textColor=GRAY_DARK,
            leading=12,
        ),
        "table_cell_bold": ParagraphStyle(
            "table_cell_bold",
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=GRAY_DARK,
            leading=12,
        ),
        "saving_label": ParagraphStyle(
            "saving_label",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=GRAY_DARK,
            leading=14,
            alignment=TA_CENTER,
        ),
        "saving_pct": ParagraphStyle(
            "saving_pct",
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            alignment=TA_CENTER,
        ),
        "saving_brl": ParagraphStyle(
            "saving_brl",
            fontName="Helvetica",
            fontSize=9,
            textColor=GRAY_MID,
            leading=12,
            alignment=TA_CENTER,
        ),
        "alert_high": ParagraphStyle(
            "alert_high",
            fontName="Helvetica",
            fontSize=9,
            textColor=RED,
            leading=12,
            leftIndent=12,
        ),
        "alert_mid": ParagraphStyle(
            "alert_mid",
            fontName="Helvetica",
            fontSize=9,
            textColor=AMBER,
            leading=12,
            leftIndent=12,
        ),
        "alert_low": ParagraphStyle(
            "alert_low",
            fontName="Helvetica",
            fontSize=9,
            textColor=TEAL,
            leading=12,
            leftIndent=12,
        ),
        "ai_body": ParagraphStyle(
            "ai_body",
            fontName="Helvetica-Oblique",
            fontSize=9,
            textColor=GRAY_DARK,
            leading=13,
            leftIndent=8,
            rightIndent=8,
        ),
        "footer": ParagraphStyle(
            "footer",
            fontName="Helvetica",
            fontSize=7.5,
            textColor=GRAY_MID,
            leading=11,
            alignment=TA_CENTER,
        ),
        "disclaimer": ParagraphStyle(
            "disclaimer",
            fontName="Helvetica-Oblique",
            fontSize=7.5,
            textColor=GRAY_MID,
            leading=11,
            alignment=TA_CENTER,
        ),
    }


# ──────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────

def _hr(styles: dict) -> HRFlowable:
    return HRFlowable(
        width="100%", thickness=0.5, color=GRAY_LIGHT, spaceAfter=6, spaceBefore=6
    )


def _sp(h: float = 0.3) -> Spacer:
    return Spacer(1, h * cm)


def _fmt_brl(value: Optional[float]) -> str:
    if value is None:
        return "—"
    return f"$ {value:,.2f}"


def _fmt_pct(value: Optional[float], suffix: str = "%") -> str:
    if value is None:
        return "—"
    return f"{value:.1f}{suffix}"


def _confidence_label(score: float, lang: str = "en") -> str:
    if score >= 0.30:
        return _t("pdf_confidence_high", lang).format(score=score)
    elif score >= 0.15:
        return _t("pdf_confidence_mid", lang).format(score=score)
    else:
        return _t("pdf_confidence_low", lang).format(score=score)


# ──────────────────────────────────────────────────────────────────────
# SEÇÕES DO DOCUMENTO
# ──────────────────────────────────────────────────────────────────────

def _section_header(styles: dict, page_w: float, lang: str = "en") -> list:
    now = datetime.now().strftime("%Y-%m-%d  %H:%M")
    elements = []

    # Linha do logo + meta lado a lado via tabela
    logo_p   = Paragraph("BidWise", styles["logo"])
    sub_p    = Paragraph(_t("pdf_report_title", lang), styles["subtitle"])
    meta_p   = Paragraph(_t("pdf_generated_on", lang).format(now=now), styles["meta"])

    header_table = Table(
        [[logo_p, meta_p]],
        colWidths=[page_w * 0.65, page_w * 0.35],
    )
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
    ]))

    elements.append(header_table)
    elements.append(_sp(0.15))
    elements.append(sub_p)
    elements.append(_sp(0.2))
    elements.append(HRFlowable(width="100%", thickness=2, color=NAVY,
                                spaceAfter=8, spaceBefore=0))
    return elements


def _section_scenario_summary(
    styles: dict, inp: InputLeilao, page_w: float, lang: str = "en"
) -> list:
    """Scenario inputs snapshot — printed before the recommendation card."""
    elements: list = []
    elements.append(Paragraph(_t("pdf_scenario_summary", lang), styles["section_title"]))

    _is_pt = lang == "pt"

    _KRALJIC_LABEL = {
        "Alavanca":    "Alavanca"    if _is_pt else "Leverage",
        "Estratégico": "Estratégico" if _is_pt else "Strategic",
        "Gargalo":     "Gargalo"     if _is_pt else "Bottleneck",
        "Não crítico": "Não crítico" if _is_pt else "Non-critical",
    }
    _NIVEL_LABEL = {
        "Alto":  "Alto"  if _is_pt else "High",
        "Médio": "Médio" if _is_pt else "Medium",
        "Baixo": "Baixo" if _is_pt else "Low",
    }
    _BEHAV_LABEL = {
        "Competitivo": "Competitivo" if _is_pt else "Competitive",
        "Moderado":    "Moderado"    if _is_pt else "Moderate",
        "Conservador": "Conservador" if _is_pt else "Conservative",
    }

    # ── Auction context ──────────────────────────────────────────────
    ctx_rows = [
        [Paragraph(_t("pdf_param_header", lang), styles["table_header"]),
         Paragraph(_t("pdf_value_header", lang), styles["table_header"])],
        [Paragraph(_t("kraljic", lang), styles["table_cell_bold"]),
         Paragraph(_KRALJIC_LABEL.get(inp.kraljic.value, inp.kraljic.value), styles["table_cell"])],
        [Paragraph(_t("commoditization", lang), styles["table_cell_bold"]),
         Paragraph(_NIVEL_LABEL.get(inp.comoditizacao.value, inp.comoditizacao.value), styles["table_cell"])],
        [Paragraph(_t("pdf_num_suppliers", lang), styles["table_cell_bold"]),
         Paragraph(str(inp.num_fornecedores), styles["table_cell"])],
        [Paragraph(_t("pdf_price_spread", lang), styles["table_cell_bold"]),
         Paragraph(f"{inp.dispersao_precos:.1f}%", styles["table_cell"])],
    ]
    ctx_table = Table(ctx_rows, colWidths=[page_w * 0.50, page_w * 0.50])
    ctx_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, GRAY_LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D1D5DB")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(ctx_table)
    elements.append(_sp(0.25))

    # ── Supplier profiles ────────────────────────────────────────────
    sup_rows: list[list] = [[
        Paragraph(_t("pdf_supplier_header", lang), styles["table_header"]),
        Paragraph(_t("pdf_proposal_header", lang), styles["table_header"]),
        Paragraph(_t("pdf_behavior_header", lang), styles["table_header"]),
        Paragraph(_t("pdf_interest_header", lang), styles["table_header"]),
    ]]
    for forn in inp.fornecedores:
        proposta = f"$ {forn.proposta_brl:,.2f}" if forn.proposta_brl is not None else "—"
        sup_rows.append([
            Paragraph(forn.nome, styles["table_cell_bold"]),
            Paragraph(proposta, styles["table_cell"]),
            Paragraph(_BEHAV_LABEL.get(forn.comportamento.value, forn.comportamento.value), styles["table_cell"]),
            Paragraph(_NIVEL_LABEL.get(forn.interesse_estrategico.value, forn.interesse_estrategico.value), styles["table_cell"]),
        ])

    sup_col_w = [page_w * 0.28, page_w * 0.25, page_w * 0.24, page_w * 0.23]
    sup_table = Table(sup_rows, colWidths=sup_col_w)
    sup_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BLUE]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D1D5DB")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("ALIGN", (2, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(sup_table)
    return elements


def _section_recommendation_card(
    styles: dict, rec: Recomendacao, page_w: float, lang: str = "en"
) -> list:
    elements = []
    elements.append(Paragraph(_t("pdf_section_rec", lang), styles["section_title"]))

    fg_color, bg_color = _FORMAT_COLORS.get(
        rec.formato, (BLUE, LIGHT_BLUE)
    )

    # Colored card header
    format_p = Paragraph(_FORMAT_LABEL_EN.get(rec.formato, rec.formato.value), styles["format_label"])
    card_header = Table(
        [[format_p]],
        colWidths=[page_w],
    )
    card_header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), fg_color),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("ROUNDEDCORNERS", [4, 4, 0, 0]),
    ]))

    # Corpo do card: justificativa
    just_p = Paragraph(rec.justificativa, styles["body_card"])
    card_body = Table(
        [[just_p]],
        colWidths=[page_w],
    )
    card_body.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg_color),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("ROUNDEDCORNERS", [0, 0, 4, 4]),
    ]))

    elements.append(card_header)
    elements.append(card_body)
    return elements


def _section_parameters(styles: dict, rec: Recomendacao, page_w: float, lang: str = "en") -> list:
    elements = []
    elements.append(Paragraph(_t("pdf_section_params", lang), styles["section_title"]))

    if not rec.parametros:
        elements.append(Paragraph(_t("pdf_no_params", lang), styles["body"]))
        return elements

    p = rec.parametros

    rows: list[list] = [
        [
            Paragraph(_t("pdf_param_header", lang), styles["table_header"]),
            Paragraph(_t("param_col_value_pct", lang), styles["table_header"]),
            Paragraph(_t("param_col_value_brl", lang), styles["table_header"]),
        ]
    ]

    def row(label: str, pct: Optional[str], brl: Optional[str]) -> list:
        return [
            Paragraph(label, styles["table_cell_bold"]),
            Paragraph(pct or "—", styles["table_cell"]),
            Paragraph(brl or "—", styles["table_cell"]),
        ]

    rows.append(row(
        _t("min_decrement_param", lang),
        _fmt_pct(p.decremento_min_pct),
        _fmt_brl(p.decremento_min_brl),
    ))
    rows.append(row(
        _t("opening_price_param", lang),
        getattr(p, "preco_abertura_descricao", None) or _fmt_pct(p.preco_abertura_pct),
        _fmt_brl(p.preco_abertura_brl),
    ))
    rows.append(row(
        _t("duration_param", lang),
        f"{p.duracao_minutos} min",
        "—",
    ))

    if p.prorrogacao_minutos:
        rows.append(row(
            _t("auto_ext_param", lang).format(trigger=p.prorrogacao_trigger_minutos),
            f"+{p.prorrogacao_minutos} min",
            "—",
        ))

    if p.visibilidade:
        rows.append([
            Paragraph(_t("thermometer_param", lang), styles["table_cell_bold"]),
            Paragraph(p.visibilidade, styles["table_cell"]),
            Paragraph("—", styles["table_cell"]),
        ])

    if p.rodadas_estimadas:
        _rounds_label = _t("rounds_param", lang).format(interval=p.intervalo_rodada_minutos)
        rows.append(row(
            _rounds_label,
            f"~{p.rodadas_estimadas}",
            "—",
        ))

    if p.incremento_holandes_pct:
        rows.append(row(
            _t("dutch_increment_param", lang),
            _fmt_pct(p.incremento_holandes_pct),
            _fmt_brl(p.incremento_holandes_brl),
        ))

    col_w = [page_w * 0.48, page_w * 0.26, page_w * 0.26]
    table = Table(rows, colWidths=col_w, repeatRows=1)
    table.setStyle(TableStyle([
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TOPPADDING", (0, 0), (-1, 0), 7),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
        # Data rows
        ("BACKGROUND", (0, 1), (-1, -1), WHITE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, GRAY_LIGHT]),
        ("TOPPADDING", (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        # Borders
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D1D5DB")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    elements.append(table)
    return elements


def _section_saving(styles: dict, rec: Recomendacao, page_w: float, lang: str = "en") -> list:
    elements = []
    elements.append(Paragraph(_t("pdf_section_saving", lang), styles["section_title"]))

    if not rec.saving:
        elements.append(Paragraph(_t("pdf_no_saving", lang), styles["body"]))
        return elements

    s = rec.saving
    col_w = page_w / 3

    # Cores das colunas
    pct_colors = [
        (RED, RED_BG),
        (TEAL, colors.HexColor("#E6F5F5")),
        (GREEN, GREEN_BG),
    ]
    labels    = [
        _t("pdf_saving_pessimistic", lang),
        _t("pdf_saving_realistic", lang),
        _t("pdf_saving_optimistic", lang),
    ]
    pct_vals  = [s.pessimista_pct, s.realista_pct, s.otimista_pct]
    brl_vals  = [s.pessimista_brl, s.realista_brl, s.otimista_brl]

    # Cabeçalho
    header_row = [
        [Paragraph(label, styles["saving_label"])]
        for label in labels
    ]

    # Linha de %
    pct_row = []
    for pct, (fg, _) in zip(pct_vals, pct_colors):
        style = ParagraphStyle(
            "sp_pct", parent=styles["saving_pct"], textColor=fg
        )
        pct_row.append([Paragraph(f"{pct:.1f}%", style)])

    # Linha de R$
    brl_row = [
        [Paragraph(_fmt_brl(brl), styles["saving_brl"])]
        for brl in brl_vals
    ]

    # Montar como 3 sub-tabelas lado a lado
    cells = []
    for i, (label, pct, brl, (fg, bg)) in enumerate(
        zip(labels, pct_vals, brl_vals, pct_colors)
    ):
        label_p = Paragraph(label, styles["saving_label"])
        pct_style = ParagraphStyle("spp", parent=styles["saving_pct"], textColor=fg)
        pct_p  = Paragraph(f"{pct:.1f}%", pct_style)
        brl_p  = Paragraph(_fmt_brl(brl), styles["saving_brl"])
        inner = Table(
            [[label_p], [pct_p], [brl_p]],
            colWidths=[col_w - 8],
        )
        inner.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]))
        cells.append(inner)

    saving_table = Table(
        [cells],
        colWidths=[col_w, col_w, col_w],
    )
    saving_table.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    note_p = Paragraph(_t("pdf_saving_note", lang), styles["body"])

    elements.append(saving_table)
    elements.append(_sp(0.2))
    elements.append(note_p)
    return elements


def _section_simulation(
    styles: dict,
    sim: SimulacaoResult,
    page_w: float,
    lang: str = "en",
) -> list:
    elements = []
    elements.append(Paragraph(_t("pdf_section_simulation", lang), styles["section_title"]))

    if sim.formato == FormatoLeilao.NAO_LEILAO:
        elements.append(Paragraph(sim.narrativa, styles["body"]))
        return elements

    # Distribuição de arquétipos
    contagem: dict[str, int] = {}
    for f in sim.fornecedores:
        contagem[f.arquetipo.value] = contagem.get(f.arquetipo.value, 0) + 1
    dist_str = "  |  ".join(f"{v}× {k}" for k, v in contagem.items())
    elements.append(Paragraph(_t("pdf_supplier_field", lang).format(dist=dist_str), styles["body"]))
    elements.append(_sp(0.15))

    # Narrativa determinística
    for line in sim.narrativa.split("\n\n"):
        if line.strip():
            elements.append(Paragraph(line.strip(), styles["body"]))

    # Vencedor e preço final
    if sim.vencedor_provavel and sim.preco_final_estimado_pct is not None:
        result_p = Paragraph(
            _t("pdf_projected_outcome", lang).format(
                winner=sim.vencedor_provavel.nome,
                pct=sim.preco_final_estimado_pct,
                saving=abs(sim.preco_final_estimado_pct),
            ),
            styles["body"],
        )
        elements.append(result_p)

    return elements


def _section_alerts(styles: dict, sim: SimulacaoResult, page_w: float, lang: str = "en") -> list:
    elements = []

    if not sim.alertas:
        return elements

    elements.append(Paragraph(_t("pdf_section_alerts", lang), styles["section_title"]))

    sev_style = {
        "Alta":  ("alert_high", "[HIGH]  "),
        "Média": ("alert_mid",  "[MED]   "),
        "Baixa": ("alert_low",  "[LOW]   "),
    }
    sev_bg = {
        "Alta":  RED_BG,
        "Média": AMBER_BG,
        "Baixa": colors.HexColor("#F0FDF4"),
    }
    sev_border = {
        "Alta":  RED,
        "Média": AMBER,
        "Baixa": GREEN,
    }

    for alerta in sorted(sim.alertas, key=lambda a: {"Alta": 0, "Média": 1, "Baixa": 2}[a.severidade]):
        style_key, prefix = sev_style.get(alerta.severidade, ("body", ""))
        text = f"<b>{alerta.tipo.value}</b> — {alerta.descricao}"
        alert_cell = Table(
            [[Paragraph(text, styles[style_key])]],
            colWidths=[page_w - 4],
        )
        alert_cell.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), sev_bg[alerta.severidade]),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LINEAFTER", (0, 0), (0, -1), 3, sev_border[alerta.severidade]),
        ]))
        elements.append(alert_cell)
        elements.append(_sp(0.1))

    return elements


def _section_references(styles: dict, rec: Recomendacao, page_w: float, lang: str = "en") -> list:
    elements = []
    elements.append(Paragraph(_t("pdf_section_references", lang), styles["section_title"]))

    if not rec.referencias:
        return elements

    rows: list[list] = [[
        Paragraph(_t("pdf_book_header", lang), styles["table_header"]),
        Paragraph(_t("pdf_author_header", lang), styles["table_header"]),
        Paragraph(_t("pdf_concept_header", lang), styles["table_header"]),
    ]]

    for ref in rec.referencias:
        rows.append([
            Paragraph(f"<i>{ref.livro}</i>", styles["table_cell"]),
            Paragraph(ref.autor, styles["table_cell"]),
            Paragraph(ref.aplicacao, styles["table_cell"]),
        ])

    col_w = [page_w * 0.28, page_w * 0.22, page_w * 0.50]
    table = Table(rows, colWidths=col_w, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TOPPADDING", (0, 0), (-1, 0), 7),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, GRAY_LIGHT]),
        ("TOPPADDING", (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D1D5DB")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    elements.append(table)
    return elements


def _section_suppliers(styles: dict, inp: InputLeilao, page_w: float) -> list:
    """Tabela de fornecedores com proposta, interesse e comportamento."""
    elements: list = []
    elements.append(Paragraph("7. Supplier Profiles", styles["section_title"]))
    elements.append(_sp(0.2))

    _BEHAV_EN = {
        "Competitivo": "Competitive",
        "Moderado":    "Moderate",
        "Conservador": "Conservative",
    }
    _INT_EN = {
        "Alto":  "High",
        "Médio": "Medium",
        "Baixo": "Low",
    }

    header = ["Supplier", "Proposal ($)", "Strategic Interest", "Behavior"]
    rows = [header]
    for forn in inp.fornecedores:
        proposta = f"$ {forn.proposta_brl:,.2f}" if forn.proposta_brl is not None else "—"
        rows.append([
            forn.nome,
            proposta,
            _INT_EN.get(forn.interesse_estrategico.value, forn.interesse_estrategico.value),
            _BEHAV_EN.get(forn.comportamento.value, forn.comportamento.value),
        ])

    col_w = [page_w * 0.30, page_w * 0.25, page_w * 0.23, page_w * 0.22]
    tbl = Table(rows, colWidths=col_w)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0), 8),
        ("FONTSIZE",     (0, 1), (-1, -1), 8),
        ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BLUE]),
        ("GRID",         (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
        ("ALIGN",        (1, 0), (1, -1), "RIGHT"),
        ("ALIGN",        (2, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(tbl)
    elements.append(_sp(0.3))
    return elements


def draw_uncertainty_chart(alvos: list[dict], dark: bool = True):
    """
    Generates the per-supplier uncertainty projection chart.
    Returns (fig, has_data). has_data=False when no supplier has a proposal value.

    dark=True  → dark-mode palette (transparent bg, white text) for Streamlit.
    dark=False → light palette (white bg, dark text) for PDF export.

    Each entry in alvos: {nome, proposta_inicial, alvo_realista, range_min, range_max, arquetipo}
    """
    with_data = [a for a in alvos if a.get("proposta_inicial")]
    if not with_data:
        return None, False

    _INITIAL = {
        "Aggressive Leader": "A",
        "Cautious Follower": "C",
        "Floor-setter":      "F",
        "Dropout Candidate": "D",
    }

    # Colour palette — dark mode vs PDF light mode
    _C_CIRCLE  = "#5DADE2"
    _C_DIAMOND = "#2ECC71"
    _C_BOX     = "#5DADE2"
    _C_ANNOT   = "#333333"
    _C_TITLE   = "#333333"
    _C_LABELS  = "#333333"
    _C_GRID    = "#4A4A6A" if dark else "#F3F4F6"
    _C_SPINE   = "#555577" if dark else "#E5E7EB"
    _C_LEG     = "#333333"

    n = len(with_data)
    fig, ax = plt.subplots(figsize=(max(7, n * 1.6), 5))
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")

    for i, a in enumerate(with_data):
        prop        = a["proposta_inicial"]
        alvo_pct    = a["alvo_realista"]
        rmin_pct    = a["range_min"]   # lower saving → higher price
        rmax_pct    = a["range_max"]   # higher saving → lower price

        target      = prop * (1 - alvo_pct / 100)
        price_upper = prop * (1 - rmin_pct / 100)
        price_lower = prop * (1 - rmax_pct / 100)

        # Uncertainty box
        ax.add_patch(mpatches.Rectangle(
            (i - 0.25, price_lower), 0.5, price_upper - price_lower,
            facecolor=_C_BOX, alpha=0.30,
            edgecolor=_C_CIRCLE, linewidth=0.8, zorder=2,
        ))

        # Initial proposal — open circle
        ax.plot(i, prop, marker='o', color=_C_CIRCLE, markersize=11,
                markerfacecolor='none', markeredgewidth=2.2, zorder=5, linestyle='None')

        # Realistic target — filled diamond
        ax.plot(i, target, marker='D', color=_C_DIAMOND, markersize=8,
                markerfacecolor=_C_DIAMOND, zorder=5, linestyle='None')

        # Alternate annotation offsets to prevent overlap when proposals are close
        _above = i % 2 == 0
        ax.annotate(
            f"${prop:,.0f}", xy=(i, prop),
            xytext=(8, 6 if _above else -14),
            textcoords="offset points", fontsize=7.5,
            color=_C_ANNOT, fontweight='bold',
            va='bottom' if _above else 'top',
        )
        ax.annotate(
            f"${target:,.0f}", xy=(i, target),
            xytext=(8, -6 if _above else 8),
            textcoords="offset points", fontsize=7.5,
            color=_C_ANNOT, fontweight='bold',
            va='top' if _above else 'bottom',
        )

    xlabels = [a['nome'] for a in with_data]
    rotate = n > 4
    ax.set_xticks(range(n))
    ax.set_xticklabels(
        xlabels, fontsize=8.5, color=_C_LABELS,
        rotation=20 if rotate else 0,
        ha='right' if rotate else 'center',
    )

    all_props = [a["proposta_inicial"] for a in with_data]
    min_price = min(a["proposta_inicial"] * (1 - a["range_max"] / 100) for a in with_data)
    ax.set_ylim(min_price * 0.93, max(all_props) * 1.10)
    ax.set_xlim(-0.6, n - 0.4)

    ax.set_ylabel("Price ($)", fontsize=9, color=_C_LABELS)
    ax.set_title(
        "Reverse Auction Planning — Uncertainty Projection",
        fontsize=11, fontweight='bold', color=_C_TITLE, pad=12,
    )
    ax.tick_params(colors=_C_LABELS, labelsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(_C_SPINE)
    ax.spines["bottom"].set_color(_C_SPINE)
    ax.yaxis.grid(True, color=_C_GRID, zorder=0, linewidth=0.7)

    leg_handles = [
        plt.Line2D([0], [0], marker='o', color=_C_CIRCLE, markerfacecolor='none',
                   markeredgewidth=2, markersize=9, linestyle='None', label='○  Initial Proposal'),
        plt.Line2D([0], [0], marker='D', color=_C_DIAMOND, markerfacecolor=_C_DIAMOND,
                   markersize=7, linestyle='None', label='◆  Realistic Target'),
        mpatches.Patch(facecolor=_C_BOX, alpha=0.6, edgecolor=_C_CIRCLE,
                       label='█  Uncertainty Range'),
    ]
    ax.legend(
        handles=leg_handles,
        loc='lower right',
        ncol=1, fontsize=8.5, framealpha=0.5, labelcolor=_C_LEG,
    )
    fig.text(0.98, 0.02, "BidWise", ha='right', va='bottom',
             fontsize=7, color='#9CA3AF', style='italic')

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.22 if not rotate else 0.30)
    return fig, True


def _section_uncertainty_chart(
    styles: dict,
    sim: SimulacaoResult,
    page_w: float,
    lang: str = "en",
) -> list:
    elements = []
    elements.append(Paragraph(_t("pdf_section_chart", lang), styles["section_title"]))

    fig, has_data = draw_uncertainty_chart(sim.alvos_por_fornecedor, dark=False)
    if not has_data:
        elements.append(Paragraph(_t("pdf_no_chart", lang), styles["body"]))
        return elements

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor='white', transparent=False)
    plt.close(fig)
    buf.seek(0)

    img = RLImage(buf, width=page_w, height=page_w * 0.56)
    elements.append(img)
    return elements


def _section_footer(styles: dict, lang: str = "en") -> list:
    elements = [
        _sp(0.4),
        HRFlowable(width="100%", thickness=0.5, color=GRAY_MID,
                   spaceAfter=6, spaceBefore=0),
        Paragraph(_t("pdf_footer_gen", lang), styles["footer"]),
        _sp(0.1),
        Paragraph(_t("pdf_footer_disclaimer", lang), styles["disclaimer"]),
    ]
    return elements


# ──────────────────────────────────────────────────────────────────────
# FUNÇÃO PRINCIPAL
# ──────────────────────────────────────────────────────────────────────

def gerar_pdf(
    inp: InputLeilao,
    rec: Recomendacao,
    sim: SimulacaoResult,
    lang: str = "en",
) -> bytes:
    """
    Gera o relatório PDF completo e retorna os bytes.
    Não salva em disco — usar com st.download_button.
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title=_t("pdf_report_title", lang),
        author="BidWise",
    )

    page_w = A4[0] - 3.6 * cm  # largura útil
    styles = _build_styles()

    story: list = []

    story.extend(_section_header(styles, page_w, lang=lang))
    story.append(_sp(0.3))

    story.extend(_section_scenario_summary(styles, inp, page_w, lang=lang))
    story.append(_sp(0.4))

    story.extend(_section_recommendation_card(styles, rec, page_w, lang=lang))
    story.append(_sp(0.4))

    story.extend(_section_parameters(styles, rec, page_w, lang=lang))
    story.append(_sp(0.4))

    story.extend(_section_saving(styles, rec, page_w, lang=lang))
    story.append(_sp(0.4))

    story.extend(_section_simulation(styles, sim, page_w, lang=lang))
    story.append(_sp(0.3))

    story.extend(_section_alerts(styles, sim, page_w, lang=lang))

    story.extend(_section_uncertainty_chart(styles, sim, page_w, lang=lang))

    story.extend(_section_references(styles, rec, page_w, lang=lang))

    story.extend(_section_footer(styles, lang=lang))

    doc.build(story)
    return buffer.getvalue()


# ──────────────────────────────────────────────────────────────────────
# TESTE
# ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from motor import (
        Comportamento,
        Fornecedor,
        NivelTripartido,
        QuadranteKraljic,
        recomendar,
    )
    from simulador import simular

    inp = InputLeilao(
        fornecedores=[
            Fornecedor("Alpha",   500_000.00, NivelTripartido.ALTO,  Comportamento.COMPETITIVO),
            Fornecedor("Beta",    520_000.00, NivelTripartido.ALTO,  Comportamento.COMPETITIVO),
            Fornecedor("Gamma",   555_000.00, NivelTripartido.ALTO,  Comportamento.COMPETITIVO),
            Fornecedor("Delta",   580_000.00, NivelTripartido.MEDIO, Comportamento.COMPETITIVO),
            Fornecedor("Epsilon", 610_000.00, NivelTripartido.ALTO,  Comportamento.MODERADO),
            Fornecedor("Zeta",    625_000.00, NivelTripartido.ALTO,  Comportamento.COMPETITIVO),
        ],
        kraljic=QuadranteKraljic.ALAVANCA,
        comoditizacao=NivelTripartido.ALTO,
    )

    rec = recomendar(inp)
    sim = simular(inp, rec)

    pdf_bytes = gerar_pdf(inp, rec, sim)

    output_path = "bidwise_test_report.pdf"
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)

    print(f"PDF generated: {output_path}  ({len(pdf_bytes):,} bytes)")
