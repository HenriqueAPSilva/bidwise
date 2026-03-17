"""
simulador.py — Simulador de Comportamento de Fornecedores
Autor: Henrique Alexandre Pinto Silva
Descrição: Camada determinística de simulação de comportamento por arquétipo
           de fornecedor, por formato de leilão. Sem dependências externas.
           A narrativa em linguagem natural gerada aqui é a versão
           determinística — o prompt_engine.py a complementa via Claude API.

Referências teóricas:
- Auction Theory (Vijay Krishna) — comportamento em equilíbrio por formato
- Thinking Strategically (Dixit & Nalebuff) — estratégias dominantes e sniping
- The Psychology of Price (Leigh Caldwell) — ancoragem e limiar de aceitação
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from motor import (
    Comportamento,
    Fornecedor,
    FormatoLeilao,
    InputLeilao,
    NivelTripartido,
    Recomendacao,
    _normalizar_nivel,
)


# ──────────────────────────────────────────────────────────────────────
# ENUMS E DATACLASSES
# ──────────────────────────────────────────────────────────────────────

class Arquetipo(str, Enum):
    AGGRESSIVE_LEADER  = "Aggressive Leader"
    CAUTIOUS_FOLLOWER  = "Cautious Follower"
    FLOOR_SETTER       = "Floor-setter"
    DROPOUT_CANDIDATE  = "Dropout Candidate"


class TipoEvento(str, Enum):
    LANCE            = "Bid"
    ACEITE           = "Acceptance"      # Dutch
    ELIMINACAO       = "Elimination"     # Japanese
    ACEITACAO_RODADA = "Round acceptance"  # Japanese
    DESISTENCIA      = "Withdrawal"
    ENCERRAMENTO     = "Closing"


class TipoAlerta(str, Enum):
    LEILAO_DESERTO      = "Desert auction risk"
    DESISTENCIA_PRECOCE = "Early withdrawal risk"
    SINAL_CONLUIO       = "Collusion signal"
    CAMPO_FRACO         = "Weak supplier field"
    ACEITE_RAPIDO       = "Early acceptance risk (Dutch)"
    ELIMINACAO_RAPIDA   = "Rapid elimination forecast"


@dataclass
class FornecedorSimulado:
    """Representação de um fornecedor no contexto da simulação."""
    id: int                       # 1-based
    arquetipo: Arquetipo
    custo_relativo: float         # 0.0 (mais barato) → 1.0 (mais caro)
    interesse: float              # 0.0 (baixo) → 1.0 (alto)
    threshold_minimo: float       # menor % sobre melhor proposta que aceita (Holandês)
    nome_original: str = ""       # nome real do fornecedor (de Fornecedor.nome)

    @property
    def nome(self) -> str:
        label = self.nome_original or f"Supplier {self.id}"
        return f"{label} ({self.arquetipo.value})"


@dataclass
class Evento:
    """Evento estruturado durante a simulação."""
    tipo: TipoEvento
    fornecedor: FornecedorSimulado
    momento: str          # "Abertura", "Meio", "Sprint final", "Rodada N", "Tick N"
    preco_relativo: Optional[float]  # % sobre melhor proposta original (negativo = abaixo)
    descricao: str


@dataclass
class AlertaSimulacao:
    tipo: TipoAlerta
    descricao: str
    severidade: str  # "Alta", "Média", "Baixa"


@dataclass
class SimulacaoResult:
    """Output completo do simulador."""
    formato: FormatoLeilao
    fornecedores: list[FornecedorSimulado]
    eventos: list[Evento]
    alertas: list[AlertaSimulacao]
    narrativa: str
    preco_final_estimado_pct: Optional[float]  # % sobre melhor proposta original
    vencedor_provavel: Optional[FornecedorSimulado]


# ──────────────────────────────────────────────────────────────────────
# MAPEAMENTO DE ARQUÉTIPOS
# ──────────────────────────────────────────────────────────────────────

_INTERESSE_FLOAT = {
    NivelTripartido.ALTO:  0.85,
    NivelTripartido.MEDIO: 0.55,
    NivelTripartido.BAIXO: 0.25,
}

_THRESHOLD_POR_ARQUETIPO = {
    Arquetipo.AGGRESSIVE_LEADER:  -0.08,
    Arquetipo.CAUTIOUS_FOLLOWER:  -0.04,
    Arquetipo.FLOOR_SETTER:       -0.02,
    Arquetipo.DROPOUT_CANDIDATE:   0.02,
}


def _determinar_arquetipo(
    comportamento: Comportamento,
    interesse: NivelTripartido,
) -> Arquetipo:
    """
    Mapeia o perfil individual de um fornecedor para um arquétipo de simulação.

    Regras (em ordem de prioridade):
    - Competitive + High          → Aggressive Leader
    - Competitive + Medium        → Cautious Follower
    - Moderate + High             → Cautious Follower
    - Moderate + Medium/Low       → Floor-setter
    - Conservative + any          → Dropout Candidate
    - any + Low (remaining cases) → Dropout Candidate
    """
    if comportamento == Comportamento.COMPETITIVO and interesse == NivelTripartido.ALTO:
        return Arquetipo.AGGRESSIVE_LEADER
    if comportamento == Comportamento.COMPETITIVO and interesse == NivelTripartido.MEDIO:
        return Arquetipo.CAUTIOUS_FOLLOWER
    if comportamento == Comportamento.MODERADO and interesse == NivelTripartido.ALTO:
        return Arquetipo.CAUTIOUS_FOLLOWER
    if comportamento == Comportamento.MODERADO:
        # Moderate + Medium or Low → Floor-setter
        return Arquetipo.FLOOR_SETTER
    # Conservative + any, or Competitive + Low
    return Arquetipo.DROPOUT_CANDIDATE


def _mapear_fornecedores(inp: InputLeilao) -> list[FornecedorSimulado]:
    """
    Converte cada Fornecedor do InputLeilao em um FornecedorSimulado,
    usando o perfil individual (comportamento + interesse) para determinar
    o arquétipo e as propostas reais para calcular custo_relativo.
    """
    propostas = [f.proposta_brl for f in inp.fornecedores if f.proposta_brl is not None]
    preco_min = min(propostas) if propostas else None
    preco_max = max(propostas) if propostas else None
    spread = (preco_max - preco_min) if (preco_min and preco_max and preco_max > preco_min) else None

    resultado: list[FornecedorSimulado] = []
    for i, forn in enumerate(inp.fornecedores):
        arquetipo = _determinar_arquetipo(forn.comportamento, forn.interesse_estrategico)

        # custo_relativo: 0.0 = cheaper (near min), 1.0 = more expensive (near max)
        if spread and forn.proposta_brl is not None:
            custo_relativo = (forn.proposta_brl - preco_min) / spread
        else:
            custo_relativo = 0.5  # without real proposal, position in middle

        resultado.append(FornecedorSimulado(
            id=i + 1,
            arquetipo=arquetipo,
            custo_relativo=round(min(max(custo_relativo, 0.0), 1.0), 3),
            interesse=_INTERESSE_FLOAT[forn.interesse_estrategico],
            threshold_minimo=_THRESHOLD_POR_ARQUETIPO[arquetipo],
            nome_original=forn.nome,
        ))

    return resultado


# ──────────────────────────────────────────────────────────────────────
# SIMULAÇÃO POR FORMATO
# ──────────────────────────────────────────────────────────────────────

def _simular_ingles(
    inp: InputLeilao,
    fornecedores: list[FornecedorSimulado],
    tem_termometro: bool,
) -> tuple[list[Evento], Optional[FornecedorSimulado], float]:
    """
    Simula o Inglês Reverso em 3 ondas: Abertura, Meio, Sprint Final.

    - Abertura: Aggressive Leaders abrem com lance agressivo
    - Meio: Floor-setters marcam posição; Cautious Followers observam
    - Sprint Final: Cautious Followers ativam; sniping nos últimos minutos
    - Dropouts: saem ou não participam
    """
    eventos: list[Evento] = []
    dispersao = inp.dispersao_precos

    # Aggressive leaders open immediately
    lider_preco = -5.0  # opening price is already 5% below best proposal
    for forn in fornecedores:
        if forn.arquetipo == Arquetipo.AGGRESSIVE_LEADER:
            lance = round(lider_preco - (3.0 + forn.custo_relativo * 2), 1)
            lance = max(lance, -(dispersao * 0.7))
            lider_preco = min(lider_preco, lance)
            eventos.append(Evento(
                tipo=TipoEvento.LANCE,
                fornecedor=forn,
                momento="Opening",
                preco_relativo=lance,
                descricao=(
                    f"{forn.nome} opens with a bid of {lance:+.1f}% vs. best proposal "
                    f"— immediate leadership strategy to discourage competitors."
                ),
            ))

    # Floor-setters mark position in mid-period
    for forn in fornecedores:
        if forn.arquetipo == Arquetipo.FLOOR_SETTER:
            lance = round(lider_preco + 1.5, 1)
            eventos.append(Evento(
                tipo=TipoEvento.LANCE,
                fornecedor=forn,
                momento="Mid-period",
                preco_relativo=lance,
                descricao=(
                    f"{forn.nome} marks position with a bid of {lance:+.1f}% "
                    f"— floor-setting: signals participation without revealing true price floor."
                ),
            ))

    # Dropouts withdraw
    for forn in fornecedores:
        if forn.arquetipo == Arquetipo.DROPOUT_CANDIDATE:
            eventos.append(Evento(
                tipo=TipoEvento.DESISTENCIA,
                fornecedor=forn,
                momento="Mid-period",
                preco_relativo=None,
                descricao=(
                    f"{forn.nome} submits no further bids — "
                    f"high structural cost or low strategic interest makes "
                    f"continued competition unviable for this supplier."
                ),
            ))

    # Final sprint: Cautious Followers activate
    for forn in fornecedores:
        if forn.arquetipo == Arquetipo.CAUTIOUS_FOLLOWER:
            sniping_pct = -1.0 if tem_termometro else -0.5
            lance = round(lider_preco + sniping_pct, 1)
            lance = max(lance, -(dispersao * 0.85))
            lider_preco = min(lider_preco, lance)
            eventos.append(Evento(
                tipo=TipoEvento.LANCE,
                fornecedor=forn,
                momento="Final sprint",
                preco_relativo=lance,
                descricao=(
                    f"{forn.nome} enters in the final minutes with a bid of {lance:+.1f}% "
                    + (
                        "— the thermometer signaled proximity to the leader, triggering sniping."
                        if tem_termometro else
                        "— without the thermometer, relies on ranking to calibrate the minimum bid."
                    )
                ),
            ))

    # Determinar vencedor (menor preço)
    lances_por_forn = {}
    for ev in eventos:
        if ev.tipo == TipoEvento.LANCE and ev.preco_relativo is not None:
            atual = lances_por_forn.get(ev.fornecedor.id, 0.0)
            lances_por_forn[ev.fornecedor.id] = min(atual, ev.preco_relativo)

    vencedor = None
    melhor_lance = 0.0
    for forn in fornecedores:
        if forn.id in lances_por_forn:
            if vencedor is None or lances_por_forn[forn.id] < melhor_lance:
                melhor_lance = lances_por_forn[forn.id]
                vencedor = forn

    eventos.append(Evento(
        tipo=TipoEvento.ENCERRAMENTO,
        fornecedor=vencedor or fornecedores[0],
        momento="Closing",
        preco_relativo=melhor_lance,
        descricao=(
            f"Auction closed. Likely winner: {vencedor.nome if vencedor else 'N/A'} "
            f"with a final price of {melhor_lance:+.1f}% vs. best proposal received."
        ),
    ))

    return eventos, vencedor, melhor_lance


def _simular_holandes(
    inp: InputLeilao,
    fornecedores: list[FornecedorSimulado],
    preco_abertura_pct: float,
    incremento_pct: float,
) -> tuple[list[Evento], Optional[FornecedorSimulado], float]:
    """
    Simula o Holandês Reverso (preço sobe a cada tick).

    Cada arquétipo tem um threshold de aceitação.
    O primeiro a aceitar vence — leilão encerra imediatamente.
    """
    eventos: list[Evento] = []
    preco_atual = preco_abertura_pct  # começa abaixo da melhor proposta

    # Threshold de aceitação por arquétipo (% sobre melhor proposta)
    thresholds = {
        Arquetipo.AGGRESSIVE_LEADER:  preco_abertura_pct * 0.4,   # aceita bem abaixo
        Arquetipo.CAUTIOUS_FOLLOWER:  preco_abertura_pct * 0.6,
        Arquetipo.FLOOR_SETTER:       preco_abertura_pct * 0.8,
        Arquetipo.DROPOUT_CANDIDATE:  0.0,  # só aceita preço próximo ao original
    }

    # Ajustar por interesse estratégico predominante
    interesse = inp.interesse_predominante
    ajuste = {
        NivelTripartido.ALTO:  1.2,   # aceita mais cedo (maior interesse)
        NivelTripartido.MEDIO: 1.0,
        NivelTripartido.BAIXO: 0.75,  # exige preço mais alto para aceitar
    }[interesse]

    for arq in thresholds:
        thresholds[arq] = round(thresholds[arq] * ajuste, 2)

    tick = 0
    vencedor = None
    preco_aceite = 0.0

    while preco_atual <= 0 and tick < 50:
        tick += 1
        momento = f"Tick {tick}"
        preco_atual = round(preco_abertura_pct + (tick - 1) * incremento_pct, 2)

        for forn in sorted(fornecedores, key=lambda f: f.custo_relativo):
            threshold = thresholds[forn.arquetipo]
            if preco_atual >= threshold and forn.arquetipo != Arquetipo.DROPOUT_CANDIDATE:
                vencedor = forn
                preco_aceite = preco_atual
                eventos.append(Evento(
                    tipo=TipoEvento.ACEITE,
                    fornecedor=forn,
                    momento=momento,
                    preco_relativo=preco_atual,
                    descricao=(
                        f"{forn.nome} ACCEPTS the price at {preco_atual:+.1f}% vs. "
                        f"best proposal received (tick {tick}). Auction closes immediately "
                        f"— remaining suppliers do not get to participate."
                    ),
                ))
                break

        if vencedor:
            break

    # No supplier accepted — likely dropout-heavy field
    if not vencedor:
        eventos.append(Evento(
            tipo=TipoEvento.ENCERRAMENTO,
            fornecedor=fornecedores[-1],
            momento=f"Tick {tick}",
            preco_relativo=preco_atual,
            descricao=(
                f"No supplier accepted the price before the auction closed. "
                f"Final price reached: {preco_atual:+.1f}%. Possible desert auction."
            ),
        ))

    return eventos, vencedor, preco_aceite if vencedor else preco_atual


def _simular_japones(
    inp: InputLeilao,
    fornecedores: list[FornecedorSimulado],
    num_rodadas: int,
    decremento_pct: float,
    preco_abertura_pct: float,
) -> tuple[list[Evento], Optional[FornecedorSimulado], float]:
    """
    Simula o Japonês Reverso (eliminação progressiva).

    Cada rodada: preço desce X%. Quem não aceitar é eliminado.
    Dropouts saem nas primeiras rodadas. Última rodada = vencedor.
    """
    eventos: list[Evento] = []
    ativos = list(fornecedores)
    preco_atual = preco_abertura_pct  # começa acima da melhor proposta

    # Rodada de eliminação prevista por arquétipo
    eliminacao_rodada = {
        Arquetipo.DROPOUT_CANDIDATE:  1,                      # saem na rodada 1
        Arquetipo.FLOOR_SETTER:       max(2, num_rodadas // 3),
        Arquetipo.CAUTIOUS_FOLLOWER:  max(3, num_rodadas * 2 // 3),
        Arquetipo.AGGRESSIVE_LEADER:  num_rodadas,            # ficam até o fim
    }

    for rodada in range(1, num_rodadas + 1):
        preco_atual = round(preco_abertura_pct - (rodada - 1) * decremento_pct, 2)
        momento = f"Round {rodada}"
        eliminados_nesta_rodada: list[FornecedorSimulado] = []

        for forn in list(ativos):
            rodada_saida = eliminacao_rodada[forn.arquetipo]
            if rodada >= rodada_saida and forn.arquetipo != Arquetipo.AGGRESSIVE_LEADER:
                eliminados_nesta_rodada.append(forn)

        # Process acceptances for those who stay
        for forn in ativos:
            if forn not in eliminados_nesta_rodada:
                eventos.append(Evento(
                    tipo=TipoEvento.ACEITACAO_RODADA,
                    fornecedor=forn,
                    momento=momento,
                    preco_relativo=preco_atual,
                    descricao=(
                        f"{forn.nome} accepts {preco_atual:+.1f}% in {momento} "
                        f"and remains in the auction."
                    ),
                ))

        # Process eliminations
        for forn in eliminados_nesta_rodada:
            ativos.remove(forn)
            eventos.append(Evento(
                tipo=TipoEvento.ELIMINACAO,
                fornecedor=forn,
                momento=momento,
                preco_relativo=preco_atual,
                descricao=(
                    f"{forn.nome} does not accept {preco_atual:+.1f}% and is "
                    f"ELIMINATED in {momento}."
                ),
            ))

        # Auction closes when only 1 supplier remains
        if len(ativos) == 1:
            vencedor = ativos[0]
            eventos.append(Evento(
                tipo=TipoEvento.ENCERRAMENTO,
                fornecedor=vencedor,
                momento=momento,
                preco_relativo=preco_atual,
                descricao=(
                    f"Last active supplier: {vencedor.nome}. Auction closed in {momento} "
                    f"at {preco_atual:+.1f}% vs. best proposal received."
                ),
            ))
            return eventos, vencedor, preco_atual

        if not ativos:
            break

    # Último ativo (se mais de um sobrou, é empate — vence o de menor custo)
    vencedor = min(ativos, key=lambda f: f.custo_relativo) if ativos else None
    preco_final = preco_atual

    if vencedor:
        eventos.append(Evento(
            tipo=TipoEvento.ENCERRAMENTO,
            fornecedor=vencedor,
            momento=f"Round {num_rodadas}",
            preco_relativo=preco_final,
            descricao=(
                f"Rounds completed. Winner: {vencedor.nome} at "
                f"{preco_final:+.1f}% vs. best proposal received."
            ),
        ))

    return eventos, vencedor, preco_final


# ──────────────────────────────────────────────────────────────────────
# ALERTAS DE RISCO
# ──────────────────────────────────────────────────────────────────────

def _gerar_alertas(
    inp: InputLeilao,
    fornecedores: list[FornecedorSimulado],
    eventos: list[Evento],
    formato: FormatoLeilao,
) -> list[AlertaSimulacao]:
    alertas: list[AlertaSimulacao] = []

    n_dropouts = sum(1 for f in fornecedores if f.arquetipo == Arquetipo.DROPOUT_CANDIDATE)
    n_ativos = inp.num_fornecedores - n_dropouts
    interesse = inp.interesse_predominante
    comportamento = inp.comportamento_predominante

    # Desert auction risk
    if n_ativos <= 1:
        alertas.append(AlertaSimulacao(
            tipo=TipoAlerta.LEILAO_DESERTO,
            descricao=(
                f"With {n_dropouts} dropout candidates out of {inp.num_fornecedores} "
                f"suppliers, there is a high risk of a desert auction — only "
                f"{n_ativos} supplier(s) are expected to bid actively."
            ),
            severidade="Alta",
        ))
    elif n_ativos == 2 and formato != FormatoLeilao.HOLANDES:
        alertas.append(AlertaSimulacao(
            tipo=TipoAlerta.CAMPO_FRACO,
            descricao=(
                f"Effective field of only {n_ativos} active suppliers. "
                "Limited competition — consider Dutch Reverse for scenarios "
                "with few real participants."
            ),
            severidade="Média",
        ))

    # Tacit coordination signal — inferred from small active field + conservative behavior
    if n_ativos <= 2 and comportamento != Comportamento.COMPETITIVO and formato == FormatoLeilao.INGLES_COMPLETO:
        alertas.append(AlertaSimulacao(
            tipo=TipoAlerta.SINAL_CONLUIO,
            descricao=(
                "Small active field with non-competitive behavior and thermometer enabled. "
                "Suppliers may use the proximity signal to coordinate tacitly "
                "and converge to the absolute minimum without real competition."
            ),
            severidade="Alta",
        ))
    elif n_ativos <= 3 and comportamento == Comportamento.CONSERVADOR:
        alertas.append(AlertaSimulacao(
            tipo=TipoAlerta.SINAL_CONLUIO,
            descricao=(
                "Moderate risk of tacit coordination: few active suppliers make "
                "mutual observation easier, enabling strategic 'wait and see' behavior."
            ),
            severidade="Média",
        ))

    # Early acceptance risk (Dutch)
    if formato == FormatoLeilao.HOLANDES:
        leaders = [f for f in fornecedores if f.arquetipo == Arquetipo.AGGRESSIVE_LEADER]
        if leaders and interesse == NivelTripartido.ALTO:
            alertas.append(AlertaSimulacao(
                tipo=TipoAlerta.ACEITE_RAPIDO,
                descricao=(
                    f"With {len(leaders)} Aggressive Leader(s) and high strategic interest, "
                    "there is a risk of acceptance in the first ticks before the price reaches "
                    "maximum saving potential. Consider a slower increment (0.5%/tick) "
                    "to maximize extraction."
                ),
                severidade="Média",
            ))

    # Rapid elimination (Japanese)
    if formato == FormatoLeilao.JAPONES:
        dropouts_pct = n_dropouts / inp.num_fornecedores if inp.num_fornecedores > 0 else 0
        if dropouts_pct >= 0.4:
            alertas.append(AlertaSimulacao(
                tipo=TipoAlerta.ELIMINACAO_RAPIDA,
                descricao=(
                    f"{n_dropouts} of {inp.num_fornecedores} suppliers "
                    f"({dropouts_pct:.0%}) are expected to be eliminated in early rounds. "
                    "The auction may converge faster than planned — consider longer "
                    "round intervals (7–10 min) to avoid excessive pressure."
                ),
                severidade="Baixa",
            ))

    # Early dropout risk
    if (
        comportamento == Comportamento.CONSERVADOR
        and interesse == NivelTripartido.BAIXO
        and n_dropouts >= 2
    ):
        alertas.append(AlertaSimulacao(
            tipo=TipoAlerta.DESISTENCIA_PRECOCE,
            descricao=(
                "Conservative behavior combined with low strategic interest suggests "
                "multiple suppliers may withdraw before the auction reaches meaningful saving. "
                "Verify that suppliers received adequate briefing on contract volume "
                "and commercial conditions."
            ),
            severidade="Alta",
        ))

    return alertas


# ──────────────────────────────────────────────────────────────────────
# NARRATIVA DETERMINÍSTICA
# ──────────────────────────────────────────────────────────────────────

def _gerar_narrativa(
    inp: InputLeilao,
    fornecedores: list[FornecedorSimulado],
    eventos: list[Evento],
    alertas: list[AlertaSimulacao],
    formato: FormatoLeilao,
    vencedor: Optional[FornecedorSimulado],
    preco_final_pct: float,
) -> str:
    partes: list[str] = []

    # ── Per-supplier contextual description ──────────────────────────────
    _arq_desc = {
        Arquetipo.AGGRESSIVE_LEADER:  "competitive, high interest — likely to bid early and often",
        Arquetipo.CAUTIOUS_FOLLOWER:  "calculated, watches ranking — activates in final sprint",
        Arquetipo.FLOOR_SETTER:       "moderate stance — will mark position but not overextend",
        Arquetipo.DROPOUT_CANDIDATE:  "conservative or low interest — likely to withdraw early",
    }
    supplier_lines: list[str] = []
    for f in fornecedores:
        label = f.nome_original or f"Supplier {f.id}"
        supplier_lines.append(f"{label} ({_arq_desc[f.arquetipo]})")
    partes.append("Supplier profiles: " + "; ".join(supplier_lines) + ".")

    if formato in (FormatoLeilao.INGLES_COMPLETO, FormatoLeilao.INGLES_REDUZIDO):
        tem_term = formato == FormatoLeilao.INGLES_COMPLETO

        # Leaders who will open
        leaders = [f.nome_original or f"Supplier {f.id}" for f in fornecedores if f.arquetipo == Arquetipo.AGGRESSIVE_LEADER]
        followers = [f.nome_original or f"Supplier {f.id}" for f in fornecedores if f.arquetipo == Arquetipo.CAUTIOUS_FOLLOWER]
        dropouts = [f.nome_original or f"Supplier {f.id}" for f in fornecedores if f.arquetipo == Arquetipo.DROPOUT_CANDIDATE]

        opening = (
            f"{', '.join(leaders)} {'is' if len(leaders)==1 else 'are'} expected to open immediately "
            f"with aggressive bids to establish the price floor."
            if leaders else
            "No supplier with an aggressive profile was identified — the opening phase may be slow."
        )
        partes.append(opening)

        if dropouts:
            partes.append(
                f"{', '.join(dropouts)} {'is' if len(dropouts)==1 else 'are'} likely to "
                f"withdraw early or not bid actively due to conservative stance or low interest."
            )

        if followers:
            sprint = (
                f"{', '.join(followers)} {'is' if len(followers)==1 else 'are'} expected to "
                f"activate in the final sprint. "
                + (
                    "The thermometer will signal proximity to the leader, triggering sniping bids."
                    if tem_term else
                    "Without the thermometer, ranking position alone guides their final bid timing."
                )
            )
            partes.append(sprint)

    elif formato == FormatoLeilao.HOLANDES:
        low_threshold = [f.nome_original or f"Supplier {f.id}" for f in fornecedores if f.arquetipo == Arquetipo.AGGRESSIVE_LEADER]
        high_threshold = [f.nome_original or f"Supplier {f.id}" for f in fornecedores if f.arquetipo == Arquetipo.DROPOUT_CANDIDATE]
        if low_threshold:
            partes.append(
                f"{', '.join(low_threshold)} {'has' if len(low_threshold)==1 else 'have'} "
                f"a low acceptance threshold and may accept the price in early ticks — "
                f"the tick increment must be calibrated carefully to maximize extraction."
            )
        if high_threshold:
            partes.append(
                f"{', '.join(high_threshold)} {'is' if len(high_threshold)==1 else 'are'} "
                f"unlikely to accept unless the price climbs close to the original proposal."
            )

    elif formato == FormatoLeilao.JAPONES:
        early_exit = [f.nome_original or f"Supplier {f.id}" for f in fornecedores if f.arquetipo == Arquetipo.DROPOUT_CANDIDATE]
        mid_exit = [f.nome_original or f"Supplier {f.id}" for f in fornecedores if f.arquetipo == Arquetipo.FLOOR_SETTER]
        if early_exit:
            partes.append(
                f"{', '.join(early_exit)} {'is' if len(early_exit)==1 else 'are'} expected "
                f"to be eliminated in early rounds — conservative profile or low interest."
            )
        if mid_exit:
            partes.append(
                f"{', '.join(mid_exit)} {'is' if len(mid_exit)==1 else 'are'} expected "
                f"to exit in the first third of rounds as prices drop below their floor."
            )

    if vencedor:
        venc_nome = vencedor.nome_original or f"Supplier {vencedor.id}"
        # Find runner-up (second lowest cost among active bidders)
        bidders = [f for f in fornecedores if f.arquetipo != Arquetipo.DROPOUT_CANDIDATE]
        bidders_sorted = sorted(bidders, key=lambda f: f.custo_relativo)
        runner_up = bidders_sorted[1] if len(bidders_sorted) > 1 else None
        runner_nome = (runner_up.nome_original or f"Supplier {runner_up.id}") if runner_up else None

        if runner_nome:
            partes.append(
                f"Best positioned to win: {venc_nome}, based on lowest equalized proposal "
                f"and behavioral profile, followed by {runner_nome}. "
                f"Based on the recommendation engine's analysis, the auction is expected "
                f"to close at approximately {abs(preco_final_pct):.1f}% below the best "
                f"equalization price (realistic scenario)."
            )
        else:
            partes.append(
                f"Best positioned to win: {venc_nome}, based on lowest equalized proposal "
                f"and behavioral profile. "
                f"Expected closing: {abs(preco_final_pct):.1f}% below the best equalization price."
            )

    if alertas:
        alertas_altos = [a for a in alertas if a.severidade == "Alta"]
        if alertas_altos:
            partes.append(
                f"WARNING — {len(alertas_altos)} high-severity alert(s): "
                + " | ".join(a.descricao for a in alertas_altos)
            )

    return "\n\n".join(partes)


# ──────────────────────────────────────────────────────────────────────
# FUNÇÃO PRINCIPAL
# ──────────────────────────────────────────────────────────────────────

def simular(inp: InputLeilao, rec: Recomendacao) -> SimulacaoResult:
    """
    Função principal do simulador.
    Recebe InputLeilao + Recomendacao (do motor.py) e retorna SimulacaoResult.

    A Recomendacao é usada para extrair parâmetros já calculados
    (preço de abertura, incremento, rodadas estimadas).
    """
    formato = rec.formato

    # NAO_LEILAO — simulação não aplicável
    if formato == FormatoLeilao.NAO_LEILAO:
        return SimulacaoResult(
            formato=formato,
            fornecedores=[],
            eventos=[],
            alertas=[AlertaSimulacao(
                tipo=TipoAlerta.LEILAO_DESERTO,
                descricao="Auction not recommended for this scenario — simulation not applicable.",
                severidade="Alta",
            )],
            narrativa=(
                "The recommendation engine identified that a reverse auction is not the "
                "appropriate mechanism for this scenario. No supplier behavior simulation "
                "is available. Refer to the suggested alternative mechanism."
            ),
            preco_final_estimado_pct=None,
            vencedor_provavel=None,
        )

    # Mapear fornecedores reais para arquétipos de simulação
    fornecedores = _mapear_fornecedores(inp)

    # Extrair parâmetros da recomendação
    params = rec.parametros
    preco_abertura_pct = params.preco_abertura_pct if params else -5.0
    decremento_pct = params.decremento_min_pct if params else 1.0
    incremento_holandes = params.incremento_holandes_pct if params else 1.0
    rodadas_japones = params.rodadas_estimadas if params else 10

    # Executar simulação por formato
    if formato == FormatoLeilao.INGLES_COMPLETO:
        eventos, vencedor, preco_final = _simular_ingles(
            inp, fornecedores, tem_termometro=True
        )
    elif formato == FormatoLeilao.INGLES_REDUZIDO:
        eventos, vencedor, preco_final = _simular_ingles(
            inp, fornecedores, tem_termometro=False
        )
    elif formato == FormatoLeilao.HOLANDES:
        eventos, vencedor, preco_final = _simular_holandes(
            inp, fornecedores,
            preco_abertura_pct=preco_abertura_pct,
            incremento_pct=incremento_holandes or 1.0,
        )
    elif formato == FormatoLeilao.JAPONES:
        eventos, vencedor, preco_final = _simular_japones(
            inp, fornecedores,
            num_rodadas=rodadas_japones or 10,
            decremento_pct=decremento_pct,
            preco_abertura_pct=preco_abertura_pct or 5.0,
        )
    else:
        eventos, vencedor, preco_final = [], None, 0.0

    # Override final price with motor's realistic saving — simulator drives BEHAVIOR, motor drives NUMBERS
    # This ensures consistency: the displayed saving and the simulation closing price are always aligned.
    if rec.saving and rec.saving.realista_pct:
        preco_final_canonico = -rec.saving.realista_pct  # saving = price fell by this %
    else:
        preco_final_canonico = round(preco_final, 2)

    # Gerar alertas
    alertas = _gerar_alertas(inp, fornecedores, eventos, formato)

    # Gerar narrativa determinística (uses canonical price)
    narrativa = _gerar_narrativa(
        inp, fornecedores, eventos, alertas, formato, vencedor, abs(preco_final_canonico)
    )

    return SimulacaoResult(
        formato=formato,
        fornecedores=fornecedores,
        eventos=eventos,
        alertas=alertas,
        narrativa=narrativa,
        preco_final_estimado_pct=preco_final_canonico,
        vencedor_provavel=vencedor,
    )


# ──────────────────────────────────────────────────────────────────────
# TESTES — 5 cenários espelhando motor.py
# ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from motor import (
        QuadranteKraljic,
        recomendar,
    )

    def _print_simulacao(label: str, inp: InputLeilao) -> None:
        print("=" * 70)
        print(label)
        print("=" * 70)
        rec = recomendar(inp)
        sim = simular(inp, rec)

        print(f"Format simulated : {sim.formato.value}")
        print(f"Suppliers        : {len(sim.fornecedores)}")
        for f in sim.fornecedores:
            print(f"  * {f.nome}  cost={f.custo_relativo:.2f}  interest={f.interesse:.2f}")

        print(f"\nEvents ({len(sim.eventos)}):")
        for ev in sim.eventos:
            preco_str = f"{ev.preco_relativo:+.1f}%" if ev.preco_relativo is not None else "--"
            print(f"  [{ev.momento:15s}] {ev.tipo.value:20s} {preco_str:8s}  {ev.fornecedor.arquetipo.value}")

        if sim.alertas:
            print(f"\nAlerts ({len(sim.alertas)}):")
            for al in sim.alertas:
                print(f"  [{al.severidade}] {al.tipo.value}: {al.descricao[:100]}...")

        if sim.preco_final_estimado_pct is not None:
            print(f"\nEstimated final price : {sim.preco_final_estimado_pct:+.1f}%")
        else:
            print("\nFinal price: N/A")
        print(f"Likely winner         : {sim.vencedor_provavel.nome if sim.vencedor_provavel else 'N/A'}")
        print(f"\nNarrative:\n{sim.narrativa}")
        print()

    # Scenario 1: Large competitive field, commodity
    _print_simulacao(
        "SCENARIO 1: 6 suppliers, competitive, commodity, high interest",
        InputLeilao(
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
        ),
    )

    # Scenario 2: 3 conservative, low-interest suppliers
    _print_simulacao(
        "SCENARIO 2: 3 suppliers, conservative, low interest, narrow spread",
        InputLeilao(
            fornecedores=[
                Fornecedor("Supplier A", 120_000.00, NivelTripartido.BAIXO, Comportamento.CONSERVADOR),
                Fornecedor("Supplier B", 125_000.00, NivelTripartido.BAIXO, Comportamento.CONSERVADOR),
                Fornecedor("Supplier C", 129_600.00, NivelTripartido.BAIXO, Comportamento.CONSERVADOR),
            ],
            kraljic=QuadranteKraljic.NAO_CRITICO,
            comoditizacao=NivelTripartido.MEDIO,
        ),
    )

    # Scenario 3: Single supplier
    _print_simulacao(
        "SCENARIO 3: Single supplier (must recommend NO auction)",
        InputLeilao(
            fornecedores=[
                Fornecedor("Monopoly Inc", None, NivelTripartido.BAIXO, Comportamento.CONSERVADOR),
            ],
            kraljic=QuadranteKraljic.GARGALO,
            comoditizacao=NivelTripartido.BAIXO,
        ),
    )

    # Scenario 4: 8 moderate suppliers, wide spread
    _print_simulacao(
        "SCENARIO 4: 8 suppliers, moderate, wide spread",
        InputLeilao(
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
        ),
    )

    # Scenario 5: 4 moderate suppliers, medium spread
    _print_simulacao(
        "SCENARIO 5: 4 suppliers, moderate, medium spread",
        InputLeilao(
            fornecedores=[
                Fornecedor("Acme",    300_000.00, NivelTripartido.MEDIO, Comportamento.MODERADO),
                Fornecedor("Bravo",   318_000.00, NivelTripartido.MEDIO, Comportamento.MODERADO),
                Fornecedor("Charlie", 330_000.00, NivelTripartido.MEDIO, Comportamento.MODERADO),
                Fornecedor("Delta",   342_000.00, NivelTripartido.MEDIO, Comportamento.MODERADO),
            ],
            kraljic=QuadranteKraljic.ALAVANCA,
            comoditizacao=NivelTripartido.MEDIO,
        ),
    )
