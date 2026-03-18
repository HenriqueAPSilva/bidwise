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
    # Per-supplier realistic target drop + range for chart rendering.
    # Each entry: {nome, proposta_inicial, alvo_realista, range_min, range_max, arquetipo}
    alvos_por_fornecedor: list[dict] = field(default_factory=list)


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
    lang: str = "en",
) -> list[AlertaSimulacao]:
    alertas: list[AlertaSimulacao] = []
    _is_pt = lang == "pt"

    n_dropouts = sum(1 for f in fornecedores if f.arquetipo == Arquetipo.DROPOUT_CANDIDATE)
    n_ativos = inp.num_fornecedores - n_dropouts
    interesse = inp.interesse_predominante
    comportamento = inp.comportamento_predominante

    # Desert auction risk
    if n_ativos <= 1:
        alertas.append(AlertaSimulacao(
            tipo=TipoAlerta.LEILAO_DESERTO,
            descricao=(
                f"Com {n_dropouts} candidatos a desistência de {inp.num_fornecedores} "
                f"fornecedores, há alto risco de leilão deserto — apenas "
                f"{n_ativos} fornecedor(es) deve(m) licitar ativamente."
                if _is_pt else
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
                f"Grupo efetivo de apenas {n_ativos} fornecedores ativos. "
                "Competição limitada — considere o Leilão Reverso Holandês para cenários "
                "com poucos participantes reais."
                if _is_pt else
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
                "Grupo ativo pequeno com comportamento não competitivo e termômetro ativado. "
                "Os fornecedores podem usar o sinal de proximidade para coordenação tácita "
                "e convergir para o mínimo absoluto sem competição real."
                if _is_pt else
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
                "Risco moderado de coordenação tácita: poucos fornecedores ativos tornam "
                "a observação mútua mais fácil, possibilitando comportamento estratégico "
                "de 'espera e veja'."
                if _is_pt else
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
                    f"Com {len(leaders)} Líder(es) Agressivo(s) e alto interesse estratégico, "
                    "há risco de aceite nos primeiros ticks antes que o preço atinja o "
                    "potencial máximo de saving. Considere um incremento mais lento (0,5%/tick) "
                    "para maximizar a extração."
                    if _is_pt else
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
                    f"{n_dropouts} de {inp.num_fornecedores} fornecedores "
                    f"({dropouts_pct:.0%}) devem ser eliminados nas rodadas iniciais. "
                    "O leilão pode convergir mais rápido que o planejado — considere "
                    "intervalos de rodada mais longos (7–10 min) para evitar pressão excessiva."
                    if _is_pt else
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
                "Comportamento conservador combinado com baixo interesse estratégico sugere "
                "que múltiplos fornecedores podem desistir antes que o leilão atinja saving "
                "significativo. Verifique se os fornecedores receberam briefing adequado sobre "
                "volume do contrato e condições comerciais."
                if _is_pt else
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
    rodadas_japones: int = 10,
    lang: str = "en",
) -> str:
    from collections import defaultdict

    partes: list[str] = []
    _is_pt = lang == "pt"

    _arq_desc: dict[Arquetipo, str]
    if _is_pt:
        _arq_desc = {
            Arquetipo.AGGRESSIVE_LEADER:  "competitivo, alto interesse — tende a licitar cedo e com frequência",
            Arquetipo.CAUTIOUS_FOLLOWER:  "calculado, observa o ranking — ativa no sprint final",
            Arquetipo.FLOOR_SETTER:       "postura moderada — marca posição mas não se expõe demais",
            Arquetipo.DROPOUT_CANDIDATE:  "conservador ou baixo interesse — tende a se retirar cedo",
        }
    else:
        _arq_desc = {
            Arquetipo.AGGRESSIVE_LEADER:  "competitive, high interest — likely to bid early and often",
            Arquetipo.CAUTIOUS_FOLLOWER:  "calculated, watches ranking — activates in final sprint",
            Arquetipo.FLOOR_SETTER:       "moderate stance — will mark position but not overextend",
            Arquetipo.DROPOUT_CANDIDATE:  "conservative or low interest — likely to withdraw early",
        }

    # ── Group suppliers by archetype for compact, natural-language descriptions ──
    grupos: dict[Arquetipo, list[str]] = defaultdict(list)
    for f in fornecedores:
        label = f.nome_original or (f"Fornecedor {f.id}" if _is_pt else f"Supplier {f.id}")
        grupos[f.arquetipo].append(label)

    def _join(nomes: list[str]) -> str:
        if len(nomes) == 1:
            return nomes[0]
        conj = " e " if _is_pt else " and "
        return ", ".join(nomes[:-1]) + conj + nomes[-1]

    def _verb(nomes: list[str], singular: str, plural: str) -> str:
        return singular if len(nomes) == 1 else plural

    # Supplier profiles summary — one line per archetype group
    perfil_lines = []
    for arq in [Arquetipo.AGGRESSIVE_LEADER, Arquetipo.CAUTIOUS_FOLLOWER,
                Arquetipo.FLOOR_SETTER, Arquetipo.DROPOUT_CANDIDATE]:
        nomes = grupos.get(arq, [])
        if nomes:
            perfil_lines.append(
                f"{_join(nomes)} ({arq.value}): {_arq_desc[arq]}"
            )
    _perfil_header = "Perfis dos fornecedores: " if _is_pt else "Supplier profiles: "
    partes.append(_perfil_header + " — ".join(perfil_lines) + ".")

    if formato in (FormatoLeilao.INGLES_COMPLETO, FormatoLeilao.INGLES_REDUZIDO):
        tem_term = formato == FormatoLeilao.INGLES_COMPLETO

        leaders   = grupos.get(Arquetipo.AGGRESSIVE_LEADER, [])
        followers = grupos.get(Arquetipo.CAUTIOUS_FOLLOWER, [])
        dropouts  = grupos.get(Arquetipo.DROPOUT_CANDIDATE, [])

        if leaders:
            if _is_pt:
                partes.append(
                    f"{_join(leaders)} (Aggressive Leader{'s' if len(leaders)>1 else ''}) "
                    f"{'devem' if len(leaders)>1 else 'deve'} abrir imediatamente com lances "
                    f"agressivos para estabelecer o piso de preço."
                )
            else:
                partes.append(
                    f"{_join(leaders)} (Aggressive Leader{'s' if len(leaders)>1 else ''}) "
                    f"{_verb(leaders, 'is', 'are')} expected to open immediately with aggressive "
                    f"bids to establish the price floor."
                )
        else:
            partes.append(
                "Nenhum fornecedor com perfil agressivo foi identificado — "
                "a fase de abertura pode ser lenta."
                if _is_pt else
                "No supplier with an aggressive profile was identified — "
                "the opening phase may be slow."
            )

        if dropouts:
            if _is_pt:
                partes.append(
                    f"{_join(dropouts)} (Dropout Candidate{'s' if len(dropouts)>1 else ''}) "
                    f"{'tendem' if len(dropouts)>1 else 'tende'} a se retirar cedo ou não licitar "
                    f"ativamente devido a postura conservadora ou baixo interesse estratégico."
                )
            else:
                partes.append(
                    f"{_join(dropouts)} (Dropout Candidate{'s' if len(dropouts)>1 else ''}) "
                    f"{_verb(dropouts, 'is', 'are')} likely to withdraw early or not bid "
                    f"actively due to conservative stance or low strategic interest."
                )

        if followers:
            if _is_pt:
                partes.append(
                    f"{_join(followers)} (Cautious Follower{'s' if len(followers)>1 else ''}) "
                    f"{'devem' if len(followers)>1 else 'deve'} ativar no sprint final. "
                    + (
                        "O termômetro sinalizará a proximidade do líder, acionando lances de sniping."
                        if tem_term else
                        "Sem o termômetro, apenas a posição no ranking orienta o timing do lance final."
                    )
                )
            else:
                partes.append(
                    f"{_join(followers)} (Cautious Follower{'s' if len(followers)>1 else ''}) "
                    f"{_verb(followers, 'is', 'are')} expected to activate in the final sprint. "
                    + (
                        "The thermometer will signal proximity to the leader, triggering sniping bids."
                        if tem_term else
                        "Without the thermometer, ranking position alone guides their final bid timing."
                    )
                )

    elif formato == FormatoLeilao.HOLANDES:
        leaders  = grupos.get(Arquetipo.AGGRESSIVE_LEADER, [])
        dropouts = grupos.get(Arquetipo.DROPOUT_CANDIDATE, [])

        if leaders:
            if _is_pt:
                partes.append(
                    f"{_join(leaders)} (Aggressive Leader{'s' if len(leaders)>1 else ''}) "
                    f"{'têm' if len(leaders)>1 else 'tem'} threshold de aceite baixo e "
                    f"{'podem' if len(leaders)>1 else 'pode'} aceitar o preço nos primeiros ticks — "
                    f"o incremento por tick deve ser calibrado com cuidado para maximizar a extração."
                )
            else:
                partes.append(
                    f"{_join(leaders)} (Aggressive Leader{'s' if len(leaders)>1 else ''}) "
                    f"{_verb(leaders, 'has', 'have')} a low acceptance threshold and may accept "
                    f"the price in early ticks — the tick increment must be calibrated carefully "
                    f"to maximize extraction."
                )
        if dropouts:
            if _is_pt:
                partes.append(
                    f"{_join(dropouts)} (Dropout Candidate{'s' if len(dropouts)>1 else ''}) "
                    f"{'são' if len(dropouts)>1 else 'é'} improvável que aceite{'m' if len(dropouts)>1 else ''} "
                    f"a menos que o preço suba próximo à proposta original."
                )
            else:
                partes.append(
                    f"{_join(dropouts)} (Dropout Candidate{'s' if len(dropouts)>1 else ''}) "
                    f"{_verb(dropouts, 'is', 'are')} unlikely to accept unless the price climbs "
                    f"close to the original proposal."
                )

    elif formato == FormatoLeilao.JAPONES:
        dropouts      = grupos.get(Arquetipo.DROPOUT_CANDIDATE, [])
        floor_setters = grupos.get(Arquetipo.FLOOR_SETTER, [])
        followers     = grupos.get(Arquetipo.CAUTIOUS_FOLLOWER, [])
        leaders       = grupos.get(Arquetipo.AGGRESSIVE_LEADER, [])

        num_r    = rodadas_japones
        fs_round = max(2, num_r // 3)
        cf_round = max(3, num_r * 2 // 3)

        if dropouts:
            if _is_pt:
                partes.append(
                    f"{_join(dropouts)} (Dropout Candidate{'s' if len(dropouts)>1 else ''}) "
                    f"{'devem' if len(dropouts)>1 else 'deve'} ser eliminado{'s' if len(dropouts)>1 else ''} "
                    f"na rodada 1 — perfil conservador ou baixo interesse estratégico impede "
                    f"a aceitação ao preço de abertura."
                )
            else:
                partes.append(
                    f"{_join(dropouts)} (Dropout Candidate{'s' if len(dropouts)>1 else ''}) "
                    f"{_verb(dropouts, 'is', 'are')} expected to be eliminated in round 1 "
                    f"— conservative profile or low strategic interest prevents acceptance at opening price."
                )
        if floor_setters:
            if _is_pt:
                partes.append(
                    f"{_join(floor_setters)} (Floor-setter{'s' if len(floor_setters)>1 else ''}) "
                    f"{'devem' if len(floor_setters)>1 else 'deve'} sair por volta das rodadas "
                    f"{fs_round}–{fs_round + 1} à medida que os preços se aproximam do piso de custo."
                )
            else:
                partes.append(
                    f"{_join(floor_setters)} (Floor-setter{'s' if len(floor_setters)>1 else ''}) "
                    f"{_verb(floor_setters, 'is', 'are')} expected to exit around rounds "
                    f"{fs_round}–{fs_round + 1} as prices approach their cost floor."
                )
        if followers:
            if _is_pt:
                partes.append(
                    f"{_join(followers)} (Cautious Follower{'s' if len(followers)>1 else ''}) "
                    f"{'devem ser eliminados' if len(followers)>1 else 'deve ser eliminado'} por volta da rodada {cf_round}, "
                    f"quando os preços caem abaixo do threshold de viabilidade."
                )
            else:
                partes.append(
                    f"{_join(followers)} (Cautious Follower{'s' if len(followers)>1 else ''}) "
                    f"{_verb(followers, 'is', 'are')} projected to be eliminated around round {cf_round}, "
                    f"when prices drop below their viability threshold."
                )

        # Final rounds prediction
        finalists: list[str] = leaders[:]
        if not finalists and followers:
            finalists = followers
        elif followers:
            finalists = leaders + followers[:1]
        if len(finalists) >= 2:
            partes.append(
                f"As rodadas finais devem se resolver entre {_join(finalists)}."
                if _is_pt else
                f"The final rounds are expected to resolve between {_join(finalists)}."
            )
        elif finalists:
            partes.append(
                f"{finalists[0]} deve ser o último fornecedor em pé."
                if _is_pt else
                f"{finalists[0]} is projected to be the last supplier standing."
            )

    if vencedor:
        venc_nome = vencedor.nome_original or (f"Fornecedor {vencedor.id}" if _is_pt else f"Supplier {vencedor.id}")
        bidders = [f for f in fornecedores if f.arquetipo != Arquetipo.DROPOUT_CANDIDATE]
        others = sorted(
            [f for f in bidders if f.id != vencedor.id],
            key=lambda f: f.custo_relativo,
        )
        runner_up = others[0] if others else None
        runner_nome = (
            runner_up.nome_original or (f"Fornecedor {runner_up.id}" if _is_pt else f"Supplier {runner_up.id}")
        ) if runner_up else None

        if runner_nome:
            partes.append(
                f"Melhor posicionado para vencer: {venc_nome}, com base na menor proposta "
                f"equalizada e perfil comportamental, seguido de {runner_nome}. "
                f"Leilão deve fechar em aproximadamente {abs(preco_final_pct):.1f}% "
                f"abaixo do melhor preço de equalização (cenário realista)."
                if _is_pt else
                f"Best positioned to win: {venc_nome}, based on lowest equalized proposal "
                f"and behavioral profile, followed by {runner_nome}. "
                f"Auction expected to close at approximately {abs(preco_final_pct):.1f}% "
                f"below the best equalization price (realistic scenario)."
            )
        else:
            partes.append(
                f"Melhor posicionado para vencer: {venc_nome}, com base na menor proposta "
                f"equalizada e perfil comportamental. "
                f"Fechamento esperado: {abs(preco_final_pct):.1f}% abaixo do melhor preço de equalização."
                if _is_pt else
                f"Best positioned to win: {venc_nome}, based on lowest equalized proposal "
                f"and behavioral profile. "
                f"Expected closing: {abs(preco_final_pct):.1f}% below best equalization price."
            )

    if alertas:
        alertas_altos = [a for a in alertas if a.severidade == "Alta"]
        if alertas_altos:
            partes.append(
                f"ATENÇÃO — {len(alertas_altos)} alerta(s) de alta severidade: "
                + " | ".join(a.descricao for a in alertas_altos)
                if _is_pt else
                f"WARNING — {len(alertas_altos)} high-severity alert(s): "
                + " | ".join(a.descricao for a in alertas_altos)
            )

    return "\n\n".join(partes)


# ──────────────────────────────────────────────────────────────────────
# ALVOS POR FORNECEDOR (para gráfico)
# ──────────────────────────────────────────────────────────────────────

def _calcular_alvos_por_fornecedor(
    inp: InputLeilao,
    fornecedores: list[FornecedorSimulado],
    saving_alvo: float,  # rec.saving.realista_pct (positive %)
    formato: Optional[FormatoLeilao] = None,
    params=None,  # ParametrosLeilao or None
) -> list[dict]:
    """
    Calcula o alvo de saving individual por fornecedor, para renderização de gráfico.

    Aggressive Leader cede mais (saving × 1.3), Cautious Follower e Floor-setter
    cedem o saving base, Dropout cede menos (saving × 0.5).
    Range = ±30% do alvo individual.

    Dutch: range_min/max rounded to nearest Dutch increment.
    Japanese: range_min/max rounded to nearest round decrement.
    """
    _MULT = {
        Arquetipo.AGGRESSIVE_LEADER:  1.3,
        Arquetipo.CAUTIOUS_FOLLOWER:  1.0,
        Arquetipo.FLOOR_SETTER:       1.0,
        Arquetipo.DROPOUT_CANDIDATE:  0.5,
    }

    def _snap_to_step(value: float, step: float) -> float:
        if step and step > 0:
            return round(round(value / step) * step, 2)
        return round(value, 2)

    # Determine discretization step for range bounds
    _step: Optional[float] = None
    if formato == FormatoLeilao.HOLANDES and params and params.incremento_holandes_pct:
        _step = params.incremento_holandes_pct
    elif formato == FormatoLeilao.JAPONES and params and params.decremento_min_pct:
        _step = params.decremento_min_pct

    resultado = []
    for idx, fs in enumerate(fornecedores):
        proposta_inicial = (
            inp.fornecedores[idx].proposta_brl
            if idx < len(inp.fornecedores)
            else None
        )
        alvo = round(saving_alvo * _MULT[fs.arquetipo], 2)
        rmin = round(alvo * 0.7, 2)
        rmax = round(alvo * 1.3, 2)
        if _step:
            rmin = _snap_to_step(rmin, _step)
            rmax = _snap_to_step(rmax, _step)
        resultado.append({
            "nome": fs.nome_original or f"Supplier {fs.id}",
            "proposta_inicial": proposta_inicial,
            "alvo_realista": alvo,
            "range_min": rmin,
            "range_max": rmax,
            "arquetipo": fs.arquetipo.value,
        })
    return resultado


# ──────────────────────────────────────────────────────────────────────
# FUNÇÃO PRINCIPAL
# ──────────────────────────────────────────────────────────────────────

def simular(inp: InputLeilao, rec: Recomendacao, lang: str = "en") -> SimulacaoResult:
    """
    Função principal do simulador.
    Recebe InputLeilao + Recomendacao (do motor.py) e retorna SimulacaoResult.

    A Recomendacao é usada para extrair parâmetros já calculados
    (preço de abertura, incremento, rodadas estimadas).
    """
    formato = rec.formato

    # NAO_LEILAO — simulação não aplicável
    if formato == FormatoLeilao.NAO_LEILAO:
        _alerta_desc = (
            "Leilão não recomendado para este cenário — simulação não aplicável."
            if lang == "pt" else
            "Auction not recommended for this scenario — simulation not applicable."
        )
        _narrativa_nao = (
            "O motor de recomendação identificou que o leilão reverso não é o mecanismo "
            "adequado para este cenário. Nenhuma simulação de comportamento de fornecedores "
            "está disponível. Consulte o mecanismo alternativo sugerido."
            if lang == "pt" else
            "The recommendation engine identified that a reverse auction is not the "
            "appropriate mechanism for this scenario. No supplier behavior simulation "
            "is available. Refer to the suggested alternative mechanism."
        )
        return SimulacaoResult(
            formato=formato,
            fornecedores=[],
            eventos=[],
            alertas=[AlertaSimulacao(
                tipo=TipoAlerta.LEILAO_DESERTO,
                descricao=_alerta_desc,
                severidade="Alta",
            )],
            narrativa=_narrativa_nao,
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
    saving_alvo = rec.saving.realista_pct if (rec.saving and rec.saving.realista_pct) else None
    if saving_alvo:
        preco_final_canonico = -saving_alvo  # saving = price fell by this %
    else:
        preco_final_canonico = round(preco_final, 2)
        saving_alvo = abs(preco_final_canonico)

    # Update ENCERRAMENTO event to reflect canonical price (motor's realistic saving)
    for ev in eventos:
        if ev.tipo == TipoEvento.ENCERRAMENTO:
            ev.preco_relativo = preco_final_canonico
            venc_nome = ev.fornecedor.nome_original or f"Supplier {ev.fornecedor.id}"
            ev.descricao = (
                f"Auction closed. Best positioned to win: {venc_nome} "
                f"— expected closing at {abs(preco_final_canonico):.1f}% below best "
                f"equalization price (motor realistic saving)."
            )

    # Gerar alertas
    alertas = _gerar_alertas(inp, fornecedores, eventos, formato, lang=lang)

    # Gerar narrativa determinística (uses canonical price)
    narrativa = _gerar_narrativa(
        inp, fornecedores, eventos, alertas, formato, vencedor, abs(preco_final_canonico),
        rodadas_japones=rodadas_japones or 10,
        lang=lang,
    )

    # Calcular alvos individuais por fornecedor (para gráfico no app)
    alvos = _calcular_alvos_por_fornecedor(inp, fornecedores, saving_alvo, formato=formato, params=params)

    return SimulacaoResult(
        formato=formato,
        fornecedores=fornecedores,
        eventos=eventos,
        alertas=alertas,
        narrativa=narrativa,
        preco_final_estimado_pct=preco_final_canonico,
        vencedor_provavel=vencedor,
        alvos_por_fornecedor=alvos,
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
