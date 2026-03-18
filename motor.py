"""
motor.py — Configurador Inteligente de Leilão Reverso
Autor: Henrique Alexandre Pinto Silva
Descrição: Motor de recomendação de formato e cálculo de parâmetros
           de leilão reverso, baseado nas regras oficiais do Coupa
           e em teoria dos leilões.

Referências teóricas:
- Auction Theory (Vijay Krishna)
- Thinking Strategically (Dixit & Nalebuff)
- Negotiation Genius (Malhotra & Bazerman)
- The Psychology of Price (Leigh Caldwell)
- Competitive Procurement Strategy (David Muir)
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ──────────────────────────────────────────────────────────────────────
# ENUMS — Domínios das variáveis de input
# ──────────────────────────────────────────────────────────────────────

class QuadranteKraljic(str, Enum):
    ESTRATEGICO = "Estratégico"
    GARGALO = "Gargalo"
    ALAVANCA = "Alavanca"
    NAO_CRITICO = "Não crítico"


class Comportamento(str, Enum):
    COMPETITIVO = "Competitivo"
    MODERADO = "Moderado"
    CONSERVADOR = "Conservador"


class NivelTripartido(str, Enum):
    """Reutilizado para comoditização, interesse estratégico, urgência e risco de conluio."""
    ALTO = "Alto"
    MEDIO = "Médio"
    BAIXO = "Baixo"


class FormatoLeilao(str, Enum):
    INGLES_COMPLETO = "Inglês Reverso — Ranking + Termômetro"
    INGLES_REDUZIDO = "Inglês Reverso — Apenas Ranking"
    HOLANDES = "Holandês Reverso"
    JAPONES = "Japonês Reverso"
    NAO_LEILAO = "Não fazer leilão"


class MecanismoAlternativo(str, Enum):
    RFQ_NEGOCIACAO = "RFQ com negociação posterior"
    NOVA_QUALIFICACAO = "Nova rodada de qualificação + RFQ"
    NEGOCIACAO_DIRETA = "Negociação direta com fornecedor"
    CONTRATO_GUARDA_CHUVA = "Contrato guarda-chuva com revisão periódica"


# ──────────────────────────────────────────────────────────────────────
# DATACLASSES — Estruturas de input e output
# ──────────────────────────────────────────────────────────────────────

@dataclass
class Fornecedor:
    """Perfil individual de um fornecedor participante."""

    nome: str
    proposta_brl: Optional[float]                # proposta da rodada anterior (opcional)
    interesse_estrategico: NivelTripartido        # interesse individual neste contrato
    comportamento: Comportamento                  # perfil competitivo individual


@dataclass
class InputLeilao:
    """Parâmetros inseridos pelo comprador."""

    fornecedores: list[Fornecedor]
    kraljic: QuadranteKraljic
    comoditizacao: NivelTripartido

    def __post_init__(self) -> None:
        if len(self.fornecedores) < 1:
            raise ValueError("At least 1 supplier is required.")

    # ── Computed from supplier list ────────────────────────────────────

    @property
    def num_fornecedores(self) -> int:
        return len(self.fornecedores)

    @property
    def _propostas(self) -> list[float]:
        return [f.proposta_brl for f in self.fornecedores if f.proposta_brl is not None]

    @property
    def dispersao_precos(self) -> float:
        """% spread: (max - min) / min * 100. Returns 10.0 if < 2 proposals."""
        ps = self._propostas
        if len(ps) < 2:
            return 10.0
        return round((max(ps) - min(ps)) / min(ps) * 100, 1)

    @property
    def melhor_proposta_brl(self) -> Optional[float]:
        ps = self._propostas
        return min(ps) if ps else None

    @property
    def media_propostas_brl(self) -> Optional[float]:
        ps = self._propostas
        return round(sum(ps) / len(ps), 2) if ps else None

    @property
    def pior_proposta_brl(self) -> Optional[float]:
        ps = self._propostas
        return max(ps) if ps else None

    @property
    def comportamento_predominante(self) -> Comportamento:
        """Mode of individual supplier behaviors."""
        counts: Counter = Counter(f.comportamento for f in self.fornecedores)
        return counts.most_common(1)[0][0]

    @property
    def interesse_predominante(self) -> NivelTripartido:
        """Mode of individual supplier strategic interests."""
        counts: Counter = Counter(f.interesse_estrategico for f in self.fornecedores)
        return counts.most_common(1)[0][0]


@dataclass
class ParametrosOtimizados:
    """Parâmetros calculados para configuração do leilão."""

    decremento_min_pct: float
    decremento_min_brl: Optional[float]
    preco_abertura_pct: float  # % relativo à melhor proposta (ou média, conforme formato)
    preco_abertura_brl: Optional[float]
    duracao_minutos: int
    prorrogacao_minutos: Optional[int]
    prorrogacao_trigger_minutos: Optional[int]
    visibilidade: Optional[str]
    rodadas_estimadas: Optional[int]
    intervalo_rodada_minutos: Optional[int]  # Japonês
    incremento_holandes_pct: Optional[float]  # Holandês: quanto o preço sobe por tick
    incremento_holandes_brl: Optional[float]


@dataclass
class EstimativaSaving:
    """Faixa de saving estimado."""

    pessimista_pct: float
    realista_pct: float
    otimista_pct: float
    pessimista_brl: Optional[float]
    realista_brl: Optional[float]
    otimista_brl: Optional[float]


@dataclass
class AlertaNaoLeilao:
    """Alerta quando leilão não é o mecanismo certo."""

    motivos: list[str]
    mecanismo_sugerido: MecanismoAlternativo
    explicacao: str


@dataclass
class ReferenciaTeórica:
    """Embasamento teórico citado na justificativa."""

    livro: str
    autor: str
    conceito: str
    aplicacao: str


@dataclass
class Recomendacao:
    """Output completo do motor de recomendação."""

    formato: FormatoLeilao
    justificativa: str
    parametros: Optional[ParametrosOtimizados]
    saving: Optional[EstimativaSaving]
    referencias: list[ReferenciaTeórica]
    alerta_nao_leilao: Optional[AlertaNaoLeilao]
    score_confianca: float  # 0 a 1 — quão forte é a recomendação


# ──────────────────────────────────────────────────────────────────────
# MOTOR — Funções de detecção, recomendação e cálculo
# ──────────────────────────────────────────────────────────────────────

def detectar_nao_leilao(inp: InputLeilao, lang: str = "en") -> Optional[AlertaNaoLeilao]:
    """
    Detecta cenários onde leilão reverso NÃO é o mecanismo adequado.

    Referência: Competitive Procurement Strategy (David Muir) —
    capítulos sobre seleção de mecanismo de compra e quando a
    competição de preço aberta prejudica a relação com o fornecedor
    ou não gera valor.
    """
    motivos: list[str] = []

    _is_pt = lang == "pt"

    # Fornecedor único — impossível competição
    if inp.num_fornecedores == 1:
        motivos.append(
            "Apenas um fornecedor qualificado — não há possibilidade de competição."
            if _is_pt else
            "Only one qualified supplier — no competition is possible."
        )

    # Strategic or Bottleneck with irreplaceable supplier
    if inp.kraljic in (QuadranteKraljic.ESTRATEGICO, QuadranteKraljic.GARGALO):
        if inp.num_fornecedores <= 2:
            _kraljic_label = {
                "Estratégico": "Estratégico" if _is_pt else "Strategic",
                "Gargalo":     "Gargalo"     if _is_pt else "Bottleneck",
            }.get(inp.kraljic.value, inp.kraljic.value)
            if _is_pt:
                motivos.append(
                    f"Item classificado como {_kraljic_label} com apenas "
                    f"{inp.num_fornecedores} fornecedor(es) — risco de danos ao "
                    f"relacionamento estratégico com um fornecedor crítico."
                )
            else:
                motivos.append(
                    f"Item classified as {_kraljic_label} with only "
                    f"{inp.num_fornecedores} supplier(s) — risk of damaging the "
                    f"strategic relationship with a critical supplier."
                )

    # Triple risk: low interest + conservative + few suppliers
    if (
        inp.interesse_predominante == NivelTripartido.BAIXO
        and inp.comportamento_predominante == Comportamento.CONSERVADOR
        and inp.num_fornecedores <= 3
    ):
        motivos.append(
            "Combinação de baixo interesse estratégico, comportamento conservador "
            "e poucos fornecedores — alto risco de leilão deserto "
            "(nenhum fornecedor faz lance)."
            if _is_pt else
            "Combination of low strategic interest, conservative behavior, "
            "and few suppliers — high risk of a desert auction "
            "(no supplier submits a bid)."
        )

    # Low commoditization + few suppliers = restrictive specification
    if (
        inp.comoditizacao == NivelTripartido.BAIXO
        and inp.num_fornecedores <= 2
    ):
        motivos.append(
            "Baixa comoditização com no máximo 2 fornecedores — indica especificação "
            "técnica restritiva que pode não se beneficiar de competição aberta de preços."
            if _is_pt else
            "Low commoditization with at most 2 suppliers — indicates a "
            "restrictive technical specification that may not benefit "
            "from open price competition."
        )

    if not motivos:
        return None

    # Determinar mecanismo alternativo
    if inp.num_fornecedores == 1:
        if inp.kraljic in (QuadranteKraljic.ESTRATEGICO, QuadranteKraljic.GARGALO):
            mecanismo = MecanismoAlternativo.NEGOCIACAO_DIRETA
        else:
            mecanismo = MecanismoAlternativo.NOVA_QUALIFICACAO
    elif inp.kraljic in (QuadranteKraljic.ESTRATEGICO, QuadranteKraljic.GARGALO):
        mecanismo = MecanismoAlternativo.CONTRATO_GUARDA_CHUVA
    else:
        mecanismo = MecanismoAlternativo.RFQ_NEGOCIACAO

    if _is_pt:
        _mec_display = mecanismo.value  # already in PT
        explicacao = (
            "O cenário apresentado não favorece competição aberta de preços "
            "em formato de leilão reverso. "
            + " ".join(motivos)
            + f" Recomendação: {_mec_display}."
        )
    else:
        _mec_display = {
            "RFQ com negociação posterior": "RFQ with subsequent negotiation",
            "Nova rodada de qualificação + RFQ": "New qualification round + RFQ",
            "Negociação direta com fornecedor": "Direct negotiation with supplier",
            "Contrato guarda-chuva com revisão periódica": "Umbrella contract with periodic review",
        }.get(mecanismo.value, mecanismo.value)
        explicacao = (
            "The presented scenario does not favor open price competition "
            "in a reverse auction format. "
            + " ".join(motivos)
            + f" Recommendation: {_mec_display}."
        )

    return AlertaNaoLeilao(
        motivos=motivos,
        mecanismo_sugerido=mecanismo,
        explicacao=explicacao,
    )


# ─── Scoring de formato ─────────────────────────────────────────────

def _score_ingles_completo(inp: InputLeilao) -> float:
    """
    Inglês Reverso com ranking + termômetro.
    Máxima pressão psicológica. Ideal para campo grande, competitivo,
    commodity e baixo risco de conluio.
    """
    score = 0.0

    # Número de fornecedores
    if inp.num_fornecedores >= 5:
        score += 25
    elif inp.num_fornecedores == 4:
        score += 20
    elif inp.num_fornecedores == 3:
        score += 10
    else:
        score -= 20  # Não funciona bem com poucos

    # Comoditização
    score += {
        NivelTripartido.ALTO: 20,
        NivelTripartido.MEDIO: 10,
        NivelTripartido.BAIXO: -10,
    }[inp.comoditizacao]

    # Comportamento predominante
    score += {
        Comportamento.COMPETITIVO: 20,
        Comportamento.MODERADO: 10,
        Comportamento.CONSERVADOR: -5,
    }[inp.comportamento_predominante]

    # Interesse estratégico predominante
    score += {
        NivelTripartido.ALTO: 15,
        NivelTripartido.MEDIO: 8,
        NivelTripartido.BAIXO: -10,
    }[inp.interesse_predominante]

    # Dispersão alta favorece Inglês (espaço para competição)
    if inp.dispersao_precos > 20:
        score += 10
    elif inp.dispersao_precos > 10:
        score += 5

    return score


def _score_ingles_reduzido(inp: InputLeilao) -> float:
    """
    Inglês Reverso com apenas ranking (sem termômetro).
    Mantém competição mas reduz capacidade de calibração dos fornecedores.
    """
    score = 0.0

    # Número de fornecedores — funciona com 3 a 5
    if 3 <= inp.num_fornecedores <= 5:
        score += 22
    elif inp.num_fornecedores > 5:
        score += 15  # Ok mas Inglês completo ou Japonês melhor
    elif inp.num_fornecedores == 2:
        score += 5
    else:
        score -= 20

    # Comoditização média é o sweet spot
    score += {
        NivelTripartido.ALTO: 12,
        NivelTripartido.MEDIO: 20,
        NivelTripartido.BAIXO: -5,
    }[inp.comoditizacao]

    # Comportamento moderado é o sweet spot
    score += {
        Comportamento.COMPETITIVO: 12,
        Comportamento.MODERADO: 20,
        Comportamento.CONSERVADOR: 0,
    }[inp.comportamento_predominante]

    # Interesse estratégico predominante
    score += {
        NivelTripartido.ALTO: 10,
        NivelTripartido.MEDIO: 12,
        NivelTripartido.BAIXO: -5,
    }[inp.interesse_predominante]

    return score


def _score_holandes(inp: InputLeilao) -> float:
    """
    Holandês Reverso (clock auction ascendente).
    Opacidade total — comportamento tipo sealed bid.
    Encerra no primeiro aceite.
    """
    score = 0.0

    # Poucos fornecedores — é onde o Holandês brilha
    if inp.num_fornecedores == 2:
        score += 25
    elif inp.num_fornecedores == 3:
        score += 20
    elif inp.num_fornecedores == 4:
        score += 8
    else:
        score -= 10  # Com muitos fornecedores, Inglês ou Japonês melhor

    # Comportamento conservador — Holandês não exige competição aberta
    score += {
        Comportamento.COMPETITIVO: 0,
        Comportamento.MODERADO: 10,
        Comportamento.CONSERVADOR: 22,
    }[inp.comportamento_predominante]

    # Dispersão baixa favorece Holandês (custos parecidos)
    if inp.dispersao_precos < 10:
        score += 15
    elif inp.dispersao_precos < 20:
        score += 5
    else:
        score -= 5

    # Comoditização — funciona em qualquer nível mas brilha no médio/baixo
    score += {
        NivelTripartido.ALTO: 5,
        NivelTripartido.MEDIO: 12,
        NivelTripartido.BAIXO: 8,
    }[inp.comoditizacao]

    # Interesse estratégico predominante
    score += {
        NivelTripartido.ALTO: 5,
        NivelTripartido.MEDIO: 8,
        NivelTripartido.BAIXO: 12,
    }[inp.interesse_predominante]

    return score


def _score_japones(inp: InputLeilao) -> float:
    """
    Japonês Reverso (clock auction descendente com eliminação).
    Elimina passividade — omisso sai. Último ativo vence.
    """
    score = 0.0

    # Número de fornecedores — brilha com campo grande
    if inp.num_fornecedores >= 6:
        score += 25
    elif inp.num_fornecedores == 5:
        score += 20
    elif inp.num_fornecedores == 4:
        score += 10
    elif inp.num_fornecedores == 3:
        score += 2
    else:
        score -= 20

    # Alta comoditização com margens bem definidas
    score += {
        NivelTripartido.ALTO: 22,
        NivelTripartido.MEDIO: 10,
        NivelTripartido.BAIXO: -10,
    }[inp.comoditizacao]

    # Comportamento predominante
    score += {
        Comportamento.COMPETITIVO: 12,
        Comportamento.MODERADO: 18,
        Comportamento.CONSERVADOR: -5,
    }[inp.comportamento_predominante]

    # Dispersão alta = espaço para múltiplas rodadas
    if inp.dispersao_precos > 20:
        score += 18
    elif inp.dispersao_precos > 10:
        score += 10
    else:
        score += 2

    # Interesse estratégico predominante
    score += {
        NivelTripartido.ALTO: 12,
        NivelTripartido.MEDIO: 8,
        NivelTripartido.BAIXO: -5,
    }[inp.interesse_predominante]

    return score


def _normalizar_nivel(nivel: NivelTripartido) -> NivelTripartido:
    """Normaliza Alto/Médio/Baixo independente de acentuação/gênero."""
    mapa = {
        "Alto": NivelTripartido.ALTO,
        "Médio": NivelTripartido.MEDIO,
        "Baixo": NivelTripartido.BAIXO,
        "Alta": NivelTripartido.ALTO,
        "Média": NivelTripartido.MEDIO,
        "Baixa": NivelTripartido.BAIXO,
    }
    return mapa.get(nivel.value, nivel)


# ─── Cálculo de parâmetros ───────────────────────────────────────────

def calcular_decremento(
    propostas: list[float],
    comportamento: Comportamento,
    melhor_proposta: Optional[float] = None,
) -> float:
    """
    Calcula o decremento mínimo ideal (%) baseado nos gaps reais entre propostas.

    Lógica:
    a) < 2 propostas → fallback neutro de 1.0%
    b) Ordena propostas; calcula gap % entre cada par adjacente
    c) gap_medio = média dos gaps
    d) decremento_base = gap_medio × 0.4
    e) Cap e floor por valor do leilão (melhor proposta):
       - < $200k:   floor 0.5%, cap 14%
       - $200k–$2M: floor 0.3%, cap 10%
       - $2M–$10M:  floor 0.2%, cap 6%
       - > $10M:    floor 0.1%, cap 3%
    f) decremento = max(floor, min(cap, decremento_base))
    g) Ajuste por comportamento: competitivo ×1.1, moderado ×1.0, conservador ×0.8
    h) Arredondar a 2 casas decimais

    Referência: Negotiation Genius (Malhotra & Bazerman) —
    a calibração do decremento funciona como ancoragem progressiva.
    """
    # e) Floor/cap dinâmicos por valor
    mp = melhor_proposta
    if mp is None or mp <= 0:
        floor_pct, cap_pct = 0.3, 10.0
    elif mp < 200_000:
        floor_pct, cap_pct = 0.5, 14.0
    elif mp < 2_000_000:
        floor_pct, cap_pct = 0.3, 10.0
    elif mp < 10_000_000:
        floor_pct, cap_pct = 0.2, 6.0
    else:
        floor_pct, cap_pct = 0.1, 3.0

    # b-d) Gap-based base
    valid = sorted(p for p in propostas if p and p > 0)
    if len(valid) < 2:
        decremento_base = 1.0  # fallback neutro
    else:
        gaps = [
            (valid[i + 1] - valid[i]) / valid[i] * 100
            for i in range(len(valid) - 1)
        ]
        gap_medio = sum(gaps) / len(gaps)
        decremento_base = gap_medio * 0.4

    # f) Aplicar floor e cap
    decremento = max(floor_pct, min(cap_pct, decremento_base))

    # g) Ajuste por comportamento
    ajuste = {
        Comportamento.COMPETITIVO: 1.1,
        Comportamento.MODERADO:    1.0,
        Comportamento.CONSERVADOR: 0.8,
    }[comportamento]

    return round(decremento * ajuste, 2)


def calcular_preco_abertura(
    formato: FormatoLeilao,
    melhor_proposta: Optional[float],
    media_propostas: Optional[float],
    pior_proposta: Optional[float],
    num_fornecedores: int,
    comoditizacao: NivelTripartido,
    dispersao: float,
) -> tuple[float, Optional[float]]:
    """
    Calcula o preço de abertura sugerido (% relativo à melhor proposta, valor em $).

    Retorna (percentual_relativo, valor_ou_None).

    Regras por formato:
    - Inglês (ambos): Best Response — suppliers enter with equalized prices.
      Motor retorna 0.0 / None (sem opening price definido pelo comprador).
    - Holandês: Buyer-Defined. N >= 4 → 20% abaixo da melhor; N < 4 → 10% abaixo.
    - Japonês: Buyer-Defined. Commoditização Alta → melhor proposta (0%);
      Média/Baixa → pior proposta (espaço máximo para descida).

    Referência: Negotiation Genius (Malhotra & Bazerman) —
    efeito de ancoragem no preço de abertura.
    """
    if formato in (FormatoLeilao.INGLES_COMPLETO, FormatoLeilao.INGLES_REDUZIDO):
        # Best Response: no buyer-defined opening price
        return 0.0, None

    elif formato == FormatoLeilao.JAPONES:
        # Alto: start at best proposal (tight — commodity suppliers will drop fast)
        # Médio/Baixo: start at worst proposal (max room to descend)
        if comoditizacao == NivelTripartido.ALTO:
            return 0.0, melhor_proposta
        else:
            if pior_proposta and melhor_proposta:
                pct = round(((pior_proposta / melhor_proposta) - 1) * 100, 1)
                return pct, pior_proposta
            elif melhor_proposta:
                return 0.0, melhor_proposta
            else:
                return 0.0, None

    elif formato == FormatoLeilao.HOLANDES:
        # Buyer-Defined: start well below best; first supplier to accept wins
        desconto = 0.20 if num_fornecedores >= 4 else 0.10
        pct = round(-desconto * 100, 1)
        valor = (
            round(melhor_proposta * (1 - desconto), 2)
            if melhor_proposta
            else None
        )
        return pct, valor

    return 0.0, None


def calcular_incremento_holandes(
    interesse_estrategico: NivelTripartido,
    dispersao: float,
    melhor_proposta: Optional[float],
) -> tuple[float, Optional[float]]:
    """
    Calcula o incremento por tick do Holandês (% e $).

    Alto interesse → subida mais lenta para maximizar extração.
    Baixo interesse → subida mais rápida para não perder fornecedores.
    """
    base = {
        NivelTripartido.ALTO: 0.5,   # 0.5% por tick (lento)
        NivelTripartido.MEDIO: 1.0,  # 1.0%
        NivelTripartido.BAIXO: 1.5,  # 1.5% (rápido)
    }[interesse_estrategico]

    # Dispersão baixa → incremento menor (mais granulosidade)
    if dispersao < 10:
        base *= 0.7

    pct = round(base, 2)
    valor = round(melhor_proposta * pct / 100, 2) if melhor_proposta else None
    return pct, valor


def calcular_duracao(
    formato: FormatoLeilao,
    num_fornecedores: int,
    dispersao: float,
    decremento: float,
    melhor_proposta: Optional[float] = None,
    preco_abertura_pct: float = -10.0,
    incremento_holandes_pct: Optional[float] = None,
) -> tuple[int, Optional[int]]:
    """
    Calcula a duração recomendada em minutos e o intervalo por rodada (Japonês).

    Retorna (duracao_minutos, intervalo_rodada_minutos_ou_None).

    Inglês:
      Base por Nº fornecedores: 2-3→15 min, 4-6→20 min, 7+→30 min.
      +5 se INGLES_COMPLETO (termômetro), +5 se spread>30%, +5 se melhor>$2M.
      Cap: 45 min.

    Holandês:
      Intervalo por tick: <$200k→0.5 min, $200k–$2M→1 min, >$2M→2 min.
      Ticks estimados = |preco_abertura_pct| / incremento.
      Cap: 30 min.

    Japonês:
      Intervalo por rodada: <$200k→3 min, $200k–$2M→5 min, >$2M→7 min.
      Duração = rodadas × intervalo. Cap total: 90 min (reduzir rodadas se necessário).
    """
    mp = melhor_proposta

    if formato in (FormatoLeilao.INGLES_COMPLETO, FormatoLeilao.INGLES_REDUZIDO):
        if num_fornecedores <= 3:
            base = 15
        elif num_fornecedores <= 6:
            base = 20
        else:
            base = 30
        if formato == FormatoLeilao.INGLES_COMPLETO:
            base += 5
        if dispersao > 30:
            base += 5
        if mp and mp > 2_000_000:
            base += 5
        return min(base, 45), None

    elif formato == FormatoLeilao.HOLANDES:
        if mp is None or mp < 200_000:
            tick_min = 0.5
        elif mp < 2_000_000:
            tick_min = 1.0
        else:
            tick_min = 2.0
        inc = incremento_holandes_pct or 1.0
        ticks_estimados = max(1, round(abs(preco_abertura_pct) / inc))
        duracao = max(5, min(round(ticks_estimados * tick_min), 30))
        return duracao, None

    elif formato == FormatoLeilao.JAPONES:
        if mp is None or mp < 200_000:
            intervalo = 3
        elif mp < 2_000_000:
            intervalo = 5
        else:
            intervalo = 7
        rodadas = calcular_rodadas_japones(dispersao, decremento)
        duracao = rodadas * intervalo
        if duracao > 90:
            rodadas = 90 // intervalo
            duracao = rodadas * intervalo
        return duracao, intervalo

    return 30, None  # fallback


def calcular_prorrogacao(
    formato: FormatoLeilao,
    melhor_proposta: Optional[float] = None,
) -> tuple[Optional[int], Optional[int]]:
    """
    Retorna (minutos_extensao, trigger_minutos) para prorrogação automática.
    Apenas Inglês Reverso. Trigger sempre nos últimos 3 min.

    Extensão por valor:
    - < $200k:   2 min
    - $200k–$2M: 3 min
    - > $2M:     5 min

    Referência: Negotiation Genius — a prorrogação captura lances
    de última hora (sniping) e extrai valor residual.
    """
    if formato not in (FormatoLeilao.INGLES_COMPLETO, FormatoLeilao.INGLES_REDUZIDO):
        return None, None

    mp = melhor_proposta
    if mp is None or mp < 200_000:
        extensao = 2
    elif mp < 2_000_000:
        extensao = 3
    else:
        extensao = 5
    return extensao, 3  # trigger sempre 3 min


def calcular_rodadas_japones(dispersao: float, decremento: float) -> int:
    """
    Estima o número de rodadas para o Japonês Reverso.

    Fórmula: (dispersão% / decremento%) + 2 rodadas de buffer.
    Mínimo 3 rodadas, máximo 20.
    """
    if decremento <= 0:
        return 10  # fallback seguro

    rodadas = int(dispersao / decremento) + 2
    return max(3, min(rodadas, 20))


def determinar_visibilidade(
    comportamento: Comportamento,
    num_fornecedores: int,
    lang: str = "en",
) -> str:
    """
    Determines whether English Reverse should use ranking + thermometer
    or ranking only, based on behavior and field size.

    Referência: The Psychology of Price (Leigh Caldwell) —
    o termômetro amplifica a urgência percebida; com campo pequeno
    pode facilitar calibração tácita entre fornecedores.
    """
    _is_pt = lang == "pt"

    if num_fornecedores <= 2:
        return (
            "Termômetro: Desativado (campo pequeno — não agrega valor)"
            if _is_pt else
            "Thermometer: Disabled (small field — adds no value)"
        )

    if comportamento == Comportamento.COMPETITIVO and num_fornecedores >= 4:
        return (
            "Termômetro: Ativado (máxima pressão competitiva)"
            if _is_pt else
            "Thermometer: Enabled (maximum competitive pressure)"
        )

    if comportamento == Comportamento.CONSERVADOR:
        return (
            "Termômetro: Ativado (ajuda a ativar fornecedores conservadores)"
            if _is_pt else
            "Thermometer: Enabled (helps activate conservative suppliers)"
        )

    # Moderate behavior
    if num_fornecedores >= 4:
        return (
            "Termômetro: Ativado (campo grande o suficiente para diluir risco de gaming)"
            if _is_pt else
            "Thermometer: Enabled (field large enough to dilute gaming risk)"
        )
    return (
        "Termômetro: Desativado (campo pequeno reduz valor de calibração)"
        if _is_pt else
        "Thermometer: Disabled (small field reduces calibration value)"
    )


# ─── Estimativa de saving ────────────────────────────────────────────

def estimar_saving(
    formato: FormatoLeilao,
    inp: InputLeilao,
    decremento: float,
) -> EstimativaSaving:
    """
    Estima faixa de saving (pessimista, realista, otimista).

    A estimativa é baseada em heurísticas calibradas por:
    - Formato do leilão (capacidade de extração)
    - Dispersão de preços (espaço disponível)
    - Comportamento dos fornecedores
    - Número de participantes
    - Interesse estratégico

    Referência: Auction Theory (Krishna) — Revenue Equivalence Theorem
    como baseline, com ajustes práticos para valores privados correlacionados.
    """

    # Base de saving por formato (% sobre melhor proposta)
    # Calibrated to real-world benchmark: ~11% average saving in strategic sourcing practice
    base = {
        FormatoLeilao.INGLES_COMPLETO: (2.0, 5.0, 11.0),
        FormatoLeilao.INGLES_REDUZIDO: (1.5, 4.0, 9.0),
        FormatoLeilao.HOLANDES: (0.5, 2.5, 6.0),
        FormatoLeilao.JAPONES: (2.0, 5.0, 10.0),
    }.get(formato, (0, 0, 0))

    pessimista, realista, otimista = base

    # Ajuste por dispersão — mais espaço = mais potencial
    if inp.dispersao_precos > 20:
        fator_dispersao = 1.3
    elif inp.dispersao_precos > 10:
        fator_dispersao = 1.1
    else:
        fator_dispersao = 0.85

    # Ajuste por número de fornecedores
    if inp.num_fornecedores >= 5:
        fator_fornecedores = 1.2
    elif inp.num_fornecedores >= 3:
        fator_fornecedores = 1.0
    else:
        fator_fornecedores = 0.7

    # Ajuste por comportamento predominante
    fator_comportamento = {
        Comportamento.COMPETITIVO: 1.2,
        Comportamento.MODERADO: 1.0,
        Comportamento.CONSERVADOR: 0.75,
    }[inp.comportamento_predominante]

    # Ajuste por interesse estratégico predominante
    fator_interesse = {
        NivelTripartido.ALTO: 1.15,
        NivelTripartido.MEDIO: 1.0,
        NivelTripartido.BAIXO: 0.8,
    }[inp.interesse_predominante]

    fator_total = fator_dispersao * fator_fornecedores * fator_comportamento * fator_interesse

    pessimista = round(pessimista * fator_total, 1)
    realista = round(realista * fator_total, 1)
    otimista = round(otimista * fator_total, 1)

    # Cap: saving otimista nunca supera a dispersão (não faz sentido)
    otimista = min(otimista, inp.dispersao_precos)

    # Snap each saving to the nearest lower multiple of the minimum decrement
    # (a saving not achievable in whole decrement steps is not credible)
    # Guarantee: if raw saving > 0, result is at least 1x decrement (never zeros out)
    import math

    def _snap(saving: float, dec: float) -> float:
        if dec <= 0 or saving <= 0:
            return saving
        snapped = math.floor(saving / dec) * dec
        # If snapped rounds down to 0 (saving < 1 full decrement), use 1x decrement
        return round(max(snapped, dec), 2)

    pessimista = _snap(pessimista, decremento)
    realista   = _snap(realista,   decremento)
    otimista   = _snap(otimista,   decremento)

    # Preserve ordering after snap (snapping can collapse pessimista == realista == otimista)
    # Ensure pessimista <= realista <= otimista
    realista = max(realista, pessimista)
    otimista = max(otimista, realista)

    # Valores em $
    mp = inp.melhor_proposta_brl
    pessimista_brl = round(mp * pessimista / 100, 2) if mp else None
    realista_brl = round(mp * realista / 100, 2) if mp else None
    otimista_brl = round(mp * otimista / 100, 2) if mp else None

    return EstimativaSaving(
        pessimista_pct=pessimista,
        realista_pct=realista,
        otimista_pct=otimista,
        pessimista_brl=pessimista_brl,
        realista_brl=realista_brl,
        otimista_brl=otimista_brl,
    )


# ─── Referências teóricas por formato ────────────────────────────────

def gerar_referencias(formato: FormatoLeilao) -> list[ReferenciaTeórica]:
    """Retorna as referências teóricas relevantes para o formato recomendado."""

    refs: list[ReferenciaTeórica] = []

    if formato in (FormatoLeilao.INGLES_COMPLETO, FormatoLeilao.INGLES_REDUZIDO):
        refs.append(ReferenciaTeórica(
            livro="Auction Theory",
            autor="Vijay Krishna",
            conceito="English auction with independent private values",
            aplicacao=(
                "English Reverse allows suppliers to reveal information gradually, "
                "leading to greater saving extraction when private values are heterogeneous."
            ),
        ))
        refs.append(ReferenciaTeórica(
            livro="The Psychology of Price",
            autor="Leigh Caldwell",
            conceito="Psychological effect of ranking and thermometer",
            aplicacao=(
                "Ranking visibility creates social pressure and perceived urgency. "
                "The thermometer amplifies this effect by giving each supplier "
                "a continuous measure of their 'distance from the leader'."
            ),
        ))

    elif formato == FormatoLeilao.HOLANDES:
        refs.append(ReferenciaTeórica(
            livro="Auction Theory",
            autor="Vijay Krishna",
            conceito="Dutch–Sealed Bid strategic equivalence",
            aplicacao=(
                "Dutch Reverse is strategically equivalent to a sealed bid — "
                "each supplier decides independently without observing competitors. "
                "In practice, full opacity reduces tacit coordination and is "
                "preferred when the active field is small."
            ),
        ))
        refs.append(ReferenciaTeórica(
            livro="Negotiation Genius",
            autor="Deepak Malhotra & Max Bazerman",
            conceito="Anchoring via opening price",
            aplicacao=(
                "In Dutch Reverse the buyer controls the anchor — "
                "a low starting price forces suppliers to recalibrate "
                "their expectation downward before any acceptance decision."
            ),
        ))

    elif formato == FormatoLeilao.JAPONES:
        refs.append(ReferenciaTeórica(
            livro="Auction Theory",
            autor="Vijay Krishna",
            conceito="Clock auctions and progressive elimination",
            aplicacao=(
                "Japanese Reverse with active elimination resolves the free-riding problem — "
                "suppliers who do not act are eliminated, forcing continuous "
                "revelation of preferences."
            ),
        ))
        refs.append(ReferenciaTeórica(
            livro="Thinking Strategically",
            autor="Avinash Dixit & Barry Nalebuff",
            conceito="Nash equilibrium in sequential games",
            aplicacao=(
                "Round-by-round elimination creates a sequential game where "
                "each decision to stay or exit reveals information. "
                "Higher-cost suppliers exit first and the equilibrium "
                "resolves naturally."
            ),
        ))

    elif formato == FormatoLeilao.NAO_LEILAO:
        refs.append(ReferenciaTeórica(
            livro="Competitive Procurement Strategy",
            autor="David Muir",
            conceito="Procurement mechanism selection",
            aplicacao=(
                "Not every purchase benefits from a reverse auction. "
                "When the supply market is concentrated or the item is strategic, "
                "open price competition may damage the relationship "
                "without generating additional saving."
            ),
        ))

    # Cross-format reference
    refs.append(ReferenciaTeórica(
        livro="Negotiation Genius",
        autor="Deepak Malhotra & Max Bazerman",
        conceito="Auto-extension and residual value extraction",
        aplicacao=(
            "Automatic extension in the final minutes captures last-minute bids "
            "(sniping), extracting additional saving that would be lost "
            "with a fixed closing time."
        ),
    ))

    return refs


# ──────────────────────────────────────────────────────────────────────
# FUNÇÃO PRINCIPAL — Orquestra tudo
# ──────────────────────────────────────────────────────────────────────

def recomendar(inp: InputLeilao, lang: str = "en") -> Recomendacao:
    """
    Função principal do motor. Recebe o InputLeilao e retorna
    a Recomendação completa com formato, parâmetros, saving,
    referências e alertas.
    """

    # 1) Detectar se leilão é o mecanismo certo
    alerta = detectar_nao_leilao(inp, lang=lang)
    if alerta:
        return Recomendacao(
            formato=FormatoLeilao.NAO_LEILAO,
            justificativa=alerta.explicacao,
            parametros=None,
            saving=None,
            referencias=gerar_referencias(FormatoLeilao.NAO_LEILAO),
            alerta_nao_leilao=alerta,
            score_confianca=0.9,
        )

    # 2) Scoring de cada formato
    scores = {
        FormatoLeilao.INGLES_COMPLETO: _score_ingles_completo(inp),
        FormatoLeilao.INGLES_REDUZIDO: _score_ingles_reduzido(inp),
        FormatoLeilao.HOLANDES: _score_holandes(inp),
        FormatoLeilao.JAPONES: _score_japones(inp),
    }

    # Formato vencedor
    formato = max(scores, key=scores.get)  # type: ignore[arg-type]
    score_max = scores[formato]
    scores_sorted = sorted(scores.values(), reverse=True)
    runner_up_score = scores_sorted[1] if len(scores_sorted) > 1 else 0
    # (winner - runner_up) / winner: captura quão dominante é a recomendação
    if score_max > 0:
        score_confianca = round(min((score_max - runner_up_score) / score_max, 1.0), 2)
    else:
        score_confianca = 0.5

    # 3) Calcular parâmetros
    decremento_pct = calcular_decremento(
        inp._propostas, inp.comportamento_predominante, inp.melhor_proposta_brl
    )
    decremento_brl = (
        round(inp.melhor_proposta_brl * decremento_pct / 100, 2)
        if inp.melhor_proposta_brl
        else None
    )

    preco_abertura_pct, preco_abertura_brl = calcular_preco_abertura(
        formato=formato,
        melhor_proposta=inp.melhor_proposta_brl,
        media_propostas=inp.media_propostas_brl,
        pior_proposta=inp.pior_proposta_brl,
        num_fornecedores=inp.num_fornecedores,
        comoditizacao=inp.comoditizacao,
        dispersao=inp.dispersao_precos,
    )

    # Incremento Holandês calculado antes de calcular_duracao (necessário para estimar ticks)
    inc_pct, inc_brl = None, None
    if formato == FormatoLeilao.HOLANDES:
        inc_pct, inc_brl = calcular_incremento_holandes(
            inp.interesse_predominante,
            inp.dispersao_precos,
            inp.melhor_proposta_brl,
        )

    duracao, intervalo_rodada_calc = calcular_duracao(
        formato,
        inp.num_fornecedores,
        inp.dispersao_precos,
        decremento_pct,
        melhor_proposta=inp.melhor_proposta_brl,
        preco_abertura_pct=preco_abertura_pct,
        incremento_holandes_pct=inc_pct,
    )
    prorr_ext, prorr_trigger = calcular_prorrogacao(formato, inp.melhor_proposta_brl)

    # Visibilidade — derived directly from recommended format (consistent by definition)
    if formato == FormatoLeilao.INGLES_COMPLETO:
        visibilidade = (
            "Ativado (ranking + termômetro)" if lang == "pt"
            else "Enabled (ranking + thermometer)"
        )
    elif formato == FormatoLeilao.INGLES_REDUZIDO:
        visibilidade = (
            "Desativado (apenas ranking)" if lang == "pt"
            else "Disabled (ranking only)"
        )
    else:
        visibilidade = None

    # Rodadas e intervalo (apenas Japonês) — consistent with calcular_duracao output
    rodadas = None
    intervalo_rodada = None
    if formato == FormatoLeilao.JAPONES and intervalo_rodada_calc:
        intervalo_rodada = intervalo_rodada_calc
        rodadas = duracao // intervalo_rodada if intervalo_rodada > 0 else calcular_rodadas_japones(inp.dispersao_precos, decremento_pct)

    parametros = ParametrosOtimizados(
        decremento_min_pct=decremento_pct,
        decremento_min_brl=decremento_brl,
        preco_abertura_pct=preco_abertura_pct,
        preco_abertura_brl=preco_abertura_brl,
        duracao_minutos=duracao,
        prorrogacao_minutos=prorr_ext,
        prorrogacao_trigger_minutos=prorr_trigger,
        visibilidade=visibilidade,
        rodadas_estimadas=rodadas,
        intervalo_rodada_minutos=intervalo_rodada,
        incremento_holandes_pct=inc_pct,
        incremento_holandes_brl=inc_brl,
    )

    # 4) Estimativa de saving
    saving = estimar_saving(formato, inp, decremento_pct)

    # 5) Referências teóricas
    referencias = gerar_referencias(formato)

    # 6) Justificativa em linguagem natural
    justificativa = _gerar_justificativa(formato, inp, scores, parametros, lang=lang)

    return Recomendacao(
        formato=formato,
        justificativa=justificativa,
        parametros=parametros,
        saving=saving,
        referencias=referencias,
        alerta_nao_leilao=None,
        score_confianca=score_confianca,
    )


def _gerar_justificativa(
    formato: FormatoLeilao,
    inp: InputLeilao,
    scores: dict[FormatoLeilao, float],
    parametros: ParametrosOtimizados,
    lang: str = "en",
) -> str:
    """
    Gera justificativa em linguagem natural para a recomendação.
    Esta é a versão determinística — a versão com Claude API
    (em prompt_engine.py) a complementará com profundidade.
    """
    partes: list[str] = []
    _is_pt = lang == "pt"

    _fmt_label = {
        "Inglês Reverso — Ranking + Termômetro": (
            "English Reverse — Ranking + Termômetro" if _is_pt
            else "English Reverse — Ranking + Thermometer"
        ),
        "Inglês Reverso — Apenas Ranking": (
            "English Reverse — Apenas Ranking" if _is_pt
            else "English Reverse — Ranking Only"
        ),
        "Holandês Reverso": "Dutch Reverse",
        "Japonês Reverso":  "Japanese Reverse",
        "Não fazer leilão": "Não fazer leilão" if _is_pt else "Do not auction",
    }

    if _is_pt:
        partes.append(
            f"Recomendação: {_fmt_label.get(formato.value, formato.value)} para este cenário "
            f"com {inp.num_fornecedores} fornecedor(es) qualificado(s) e "
            f"dispersão de preços de {inp.dispersao_precos}%."
        )
    else:
        partes.append(
            f"Recommendation: {_fmt_label.get(formato.value, formato.value)} for this scenario "
            f"with {inp.num_fornecedores} qualified supplier(s) and a "
            f"price spread of {inp.dispersao_precos}%."
        )

    if formato == FormatoLeilao.INGLES_COMPLETO:
        partes.append(
            "O English Reverse com ranking e termômetro é recomendado porque o campo de "
            "fornecedores é grande o suficiente para gerar competição dinâmica real. "
            "O termômetro amplifica a pressão psicológica — cada fornecedor sente a "
            "'temperatura' da competição e tende a licitar de forma mais agressiva. "
            "A regra de prorrogação automática garante que o saving seja extraído até o último lance possível."
            if _is_pt else
            "English Reverse with ranking and thermometer is recommended because "
            "the supplier field is large enough to generate real dynamic competition. "
            "The thermometer amplifies psychological pressure — each supplier feels "
            "the 'temperature' of the competition and tends to bid more aggressively. "
            "The auto-extension rule ensures saving is extracted down to the last possible bid."
        )

    elif formato == FormatoLeilao.INGLES_REDUZIDO:
        partes.append(
            "O English Reverse somente com ranking (sem termômetro) é recomendado porque, "
            "embora a competição seja suficiente, o cenário apresenta risco moderado de que "
            "os fornecedores usem o termômetro para calibrar o mínimo exato necessário para vencer. "
            "Remover o termômetro preserva a pressão competitiva do ranking "
            "ao mesmo tempo que reduz a capacidade dos fornecedores de 'ler' seus concorrentes."
            if _is_pt else
            "English Reverse with ranking only (no thermometer) is recommended because, "
            "while competition is sufficient, the scenario presents a moderate risk that "
            "suppliers would use the thermometer to calibrate the exact minimum needed to win. "
            "Removing the thermometer preserves the competitive pressure of ranking "
            "while reducing suppliers' ability to 'read' their competitors."
        )

    elif formato == FormatoLeilao.HOLANDES:
        partes.append(
            "O Dutch Reverse é recomendado porque o cenário apresenta poucos participantes "
            "e/ou alto risco de conluio. No Dutch, cada fornecedor decide de forma completamente "
            "independente — é o formato de maior opacidade disponível no Coupa, "
            "funcionando na prática como um lance selado. O comprador controla o ritmo "
            "e o primeiro fornecedor a aceitar vence, encerrando o leilão imediatamente."
            if _is_pt else
            "Dutch Reverse is recommended because the scenario features few participants "
            "and/or high collusion risk. In Dutch, each supplier decides completely "
            "independently — it is the highest-opacity format available on Coupa, "
            "functioning in practice as a sealed bid. The buyer controls the pace "
            "and the first supplier to accept wins, closing the auction immediately."
        )

    elif formato == FormatoLeilao.JAPONES:
        if _is_pt:
            partes.append(
                "O Japanese Reverse é recomendado porque o campo de fornecedores é grande "
                "e o item é altamente comoditizado. A eliminação progressiva resolve o "
                "problema de passividade — fornecedores que não aceitam ativamente cada rodada são "
                f"eliminados. Com ~{parametros.rodadas_estimadas} rodadas estimadas, o formato "
                f"converge naturalmente para o fornecedor com o menor custo real."
            )
        else:
            partes.append(
                "Japanese Reverse is recommended because the supplier field is large "
                "and the item is highly commoditized. Progressive elimination solves the "
                "passivity problem — suppliers who do not actively accept each round are "
                f"eliminated. With ~{parametros.rodadas_estimadas} estimated rounds, the format "
                f"converges naturally to the supplier with the lowest real cost."
            )

    # Runner-up: concrete reason why recommended beats it
    ranking = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    segundo = ranking[1]

    if _is_pt:
        _runner_reason_pt = {
            FormatoLeilao.INGLES_COMPLETO: "também viável, mas o termômetro aumenta o risco de calibração com este perfil de fornecedores",
            FormatoLeilao.INGLES_REDUZIDO: "também viável, mas sem a pressão de eliminação que melhor se adapta a este tamanho de campo",
            FormatoLeilao.HOLANDES: "também viável, mas perde a vantagem de descoberta de preço progressiva necessária aqui",
            FormatoLeilao.JAPONES: "também viável, mas leva mais rodadas para convergir e pode exceder o tempo disponível",
        }
        partes.append(
            f"Alternativa considerada: {_fmt_label.get(segundo[0].value, segundo[0].value)} — "
            f"{_runner_reason_pt.get(segundo[0], 'também um formato viável para este cenário')}."
        )
    else:
        _runner_reason_en = {
            FormatoLeilao.INGLES_COMPLETO: "also viable but thermometer increases calibration risk with this supplier profile",
            FormatoLeilao.INGLES_REDUZIDO: "also viable but lacks the elimination pressure that best fits this field size",
            FormatoLeilao.HOLANDES: "also viable but loses the progressive price-discovery advantage needed here",
            FormatoLeilao.JAPONES: "also viable but takes more rounds to converge and may exceed available time",
        }
        partes.append(
            f"Alternative considered: {_fmt_label.get(segundo[0].value, segundo[0].value)} — "
            f"{_runner_reason_en.get(segundo[0], 'also a viable format for this scenario')}."
        )

    return " ".join(partes)


# ──────────────────────────────────────────────────────────────────────
# VALIDAÇÃO E TESTES RÁPIDOS
# ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Scenario 1: Large competitive field, commodity, high interest — expect English Complete
    print("=" * 70)
    print("SCENARIO 1: 6 suppliers, competitive, commodity, high interest")
    print("=" * 70)
    inp1 = InputLeilao(
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
    rec1 = recomendar(inp1)
    print(f"Format: {rec1.formato.value}")
    print(f"Confidence: {rec1.score_confianca}")
    print(f"Spread (auto): {inp1.dispersao_precos}%")
    print(f"Justification: {rec1.justificativa[:200]}...")
    if rec1.parametros:
        p = rec1.parametros
        print(f"Decrement: {p.decremento_min_pct}% (BRL {p.decremento_min_brl})")
        print(f"Opening price: {p.preco_abertura_pct}% (BRL {p.preco_abertura_brl})")
        print(f"Duration: {p.duracao_minutos} min")
        print(f"Extension: {p.prorrogacao_minutos} min")
        print(f"Visibility: {p.visibilidade}")
    if rec1.saving:
        s = rec1.saving
        print(f"Saving: {s.pessimista_pct}% / {s.realista_pct}% / {s.otimista_pct}%")
    print()

    # Scenario 2: 3 conservative, low-interest suppliers, narrow spread — expect Dutch or no-auction
    print("=" * 70)
    print("SCENARIO 2: 3 suppliers, conservative, low interest, narrow spread")
    print("=" * 70)
    inp2 = InputLeilao(
        fornecedores=[
            Fornecedor("Supplier A", 120_000.00, NivelTripartido.BAIXO, Comportamento.CONSERVADOR),
            Fornecedor("Supplier B", 125_000.00, NivelTripartido.BAIXO, Comportamento.CONSERVADOR),
            Fornecedor("Supplier C", 129_600.00, NivelTripartido.BAIXO, Comportamento.CONSERVADOR),
        ],
        kraljic=QuadranteKraljic.NAO_CRITICO,
        comoditizacao=NivelTripartido.MEDIO,
    )
    rec2 = recomendar(inp2)
    print(f"Format: {rec2.formato.value}")
    print(f"Confidence: {rec2.score_confianca}")
    print(f"Spread (auto): {inp2.dispersao_precos}%")
    if rec2.alerta_nao_leilao:
        print(f"ALERT: {rec2.alerta_nao_leilao.explicacao}")
    elif rec2.parametros:
        p = rec2.parametros
        print(f"Decrement: {p.decremento_min_pct}%")
        print(f"Duration: {p.duracao_minutos} min")
    if rec2.saving:
        s = rec2.saving
        print(f"Saving: {s.pessimista_pct}% / {s.realista_pct}% / {s.otimista_pct}%")
    print()

    # Scenario 3: Single supplier — must trigger no-auction alert
    print("=" * 70)
    print("SCENARIO 3: Single supplier (must recommend NO auction)")
    print("=" * 70)
    inp3 = InputLeilao(
        fornecedores=[
            Fornecedor("Monopoly Inc", None, NivelTripartido.BAIXO, Comportamento.CONSERVADOR),
        ],
        kraljic=QuadranteKraljic.GARGALO,
        comoditizacao=NivelTripartido.BAIXO,
    )
    rec3 = recomendar(inp3)
    print(f"Format: {rec3.formato.value}")
    if rec3.alerta_nao_leilao:
        print(f"Alternative mechanism: {rec3.alerta_nao_leilao.mecanismo_sugerido.value}")
        print(f"Reasons: {rec3.alerta_nao_leilao.motivos}")
    print()

    # Scenario 4: 8 moderate suppliers, wide spread — expect Japanese
    print("=" * 70)
    print("SCENARIO 4: 8 suppliers, moderate, wide spread — expect Japanese")
    print("=" * 70)
    inp4 = InputLeilao(
        fornecedores=[
            Fornecedor("S1", 1_200_000.00, NivelTripartido.ALTO,  Comportamento.MODERADO),
            Fornecedor("S2", 1_280_000.00, NivelTripartido.MEDIO, Comportamento.MODERADO),
            Fornecedor("S3", 1_330_000.00, NivelTripartido.MEDIO, Comportamento.MODERADO),
            Fornecedor("S4", 1_380_000.00, NivelTripartido.MEDIO, Comportamento.MODERADO),
            Fornecedor("S5", 1_420_000.00, NivelTripartido.ALTO,  Comportamento.MODERADO),
            Fornecedor("S6", 1_460_000.00, NivelTripartido.MEDIO, Comportamento.CONSERVADOR),
            Fornecedor("S7", 1_510_000.00, NivelTripartido.BAIXO, Comportamento.CONSERVADOR),
            Fornecedor("S8", 1_560_000.00, NivelTripartido.BAIXO, Comportamento.MODERADO),
        ],
        kraljic=QuadranteKraljic.ALAVANCA,
        comoditizacao=NivelTripartido.ALTO,
    )
    rec4 = recomendar(inp4)
    print(f"Format: {rec4.formato.value}")
    print(f"Confidence: {rec4.score_confianca}")
    print(f"Spread (auto): {inp4.dispersao_precos}%")
    if rec4.parametros:
        p = rec4.parametros
        print(f"Decrement: {p.decremento_min_pct}% (BRL {p.decremento_min_brl})")
        print(f"Duration: {p.duracao_minutos} min")
        if p.rodadas_estimadas:
            print(f"Estimated rounds: {p.rodadas_estimadas}")
    if rec4.saving:
        s = rec4.saving
        print(f"Saving: {s.pessimista_pct}% / {s.realista_pct}% / {s.otimista_pct}%")
    print()

    # Scenario 5: 4 moderate suppliers, medium spread — expect English Reduced
    print("=" * 70)
    print("SCENARIO 5: 4 suppliers, moderate, medium spread — expect English Reduced")
    print("=" * 70)
    inp5 = InputLeilao(
        fornecedores=[
            Fornecedor("Acme",    300_000.00, NivelTripartido.MEDIO, Comportamento.MODERADO),
            Fornecedor("Bravo",   318_000.00, NivelTripartido.MEDIO, Comportamento.MODERADO),
            Fornecedor("Charlie", 330_000.00, NivelTripartido.MEDIO, Comportamento.MODERADO),
            Fornecedor("Delta",   342_000.00, NivelTripartido.MEDIO, Comportamento.MODERADO),
        ],
        kraljic=QuadranteKraljic.ALAVANCA,
        comoditizacao=NivelTripartido.MEDIO,
    )
    rec5 = recomendar(inp5)
    print(f"Format: {rec5.formato.value}")
    print(f"Confidence: {rec5.score_confianca}")
    print(f"Spread (auto): {inp5.dispersao_precos}%")
    if rec5.parametros:
        p = rec5.parametros
        print(f"Decrement: {p.decremento_min_pct}%")
        print(f"Visibility: {p.visibilidade}")
        print(f"Duration: {p.duracao_minutos} min")
    if rec5.saving:
        s = rec5.saving
        print(f"Saving: {s.pessimista_pct}% / {s.realista_pct}% / {s.otimista_pct}%")
