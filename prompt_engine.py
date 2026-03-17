"""
prompt_engine.py — Integração com Claude API para narrativas ricas
Autor: Henrique Alexandre Pinto Silva
Descrição: Recebe dados estruturados do motor.py e simulador.py,
           monta prompts e retorna narrativas em linguagem natural
           via Claude API (Anthropic SDK).

           Esta camada é um AMPLIFICADOR — a inteligência real está em
           motor.py e simulador.py. Claude aqui converte dados estruturados
           em linguagem natural de alta qualidade.
"""

from __future__ import annotations

import json
from typing import Any

import anthropic

import config
from motor import (
    Comportamento,
    FormatoLeilao,
    InputLeilao,
    NivelTripartido,
    QuadranteKraljic,
    Recomendacao,
)
from simulador import Arquetipo, SimulacaoResult


# ──────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT
# ──────────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are an expert in auction theory and strategic procurement with deep knowledge \
of the Coupa platform's reverse auction capabilities.

Your background combines:
- Academic grounding in auction theory (Krishna, Dixit & Nalebuff, Malhotra & Bazerman)
- Extensive practical experience running reverse auctions in large industrial companies
- Mastery of all four Coupa reverse auction formats: English (full/reduced visibility), \
Dutch, and Japanese

Your communication style:
- Direct and professional — no filler phrases, no excessive caveats
- Concrete and actionable — buyers need specific guidance, not vague possibilities
- Evidence-based — cite theoretical principles when relevant, but keep it practical
- Structured — use short paragraphs; avoid walls of text

You always respond in English (MVP version). \
When referencing prices, use percentage changes relative to the best proposal received.\
"""


# ──────────────────────────────────────────────────────────────────────
# SERIALIZAÇÃO DOS DATACLASSES
# ──────────────────────────────────────────────────────────────────────

def _inp_to_dict(inp: InputLeilao) -> dict[str, Any]:
    suppliers = [
        {
            "name": f.nome,
            "proposal_brl": f.proposta_brl,
            "strategic_interest": f.interesse_estrategico.value,
            "behavior": f.comportamento.value,
        }
        for f in inp.fornecedores
    ]
    return {
        "num_suppliers": inp.num_fornecedores,
        "price_spread_pct": inp.dispersao_precos,
        "kraljic_quadrant": inp.kraljic.value,
        "predominant_behavior": inp.comportamento_predominante.value,
        "commoditization": inp.comoditizacao.value,
        "predominant_interest": inp.interesse_predominante.value,
        "best_proposal_brl": inp.melhor_proposta_brl,
        "avg_proposal_brl": inp.media_propostas_brl,
        "worst_proposal_brl": inp.pior_proposta_brl,
        "suppliers": suppliers,
    }


def _rec_to_dict(rec: Recomendacao) -> dict[str, Any]:
    params = None
    if rec.parametros:
        p = rec.parametros
        params = {
            "min_decrement_pct": p.decremento_min_pct,
            "min_decrement_brl": p.decremento_min_brl,
            "opening_price_pct": p.preco_abertura_pct,
            "opening_price_brl": p.preco_abertura_brl,
            "duration_minutes": p.duracao_minutos,
            "auto_extension_minutes": p.prorrogacao_minutos,
            "auto_extension_trigger_minutes": p.prorrogacao_trigger_minutos,
            "visibility": p.visibilidade,
            "estimated_rounds": p.rodadas_estimadas,
            "round_interval_minutes": p.intervalo_rodada_minutos,
            "dutch_increment_pct": p.incremento_holandes_pct,
        }

    saving = None
    if rec.saving:
        s = rec.saving
        saving = {
            "pessimistic_pct": s.pessimista_pct,
            "realistic_pct": s.realista_pct,
            "optimistic_pct": s.otimista_pct,
            "pessimistic_brl": s.pessimista_brl,
            "realistic_brl": s.realista_brl,
            "optimistic_brl": s.otimista_brl,
        }

    refs = [
        {
            "book": r.livro,
            "author": r.autor,
            "concept": r.conceito,
            "application": r.aplicacao,
        }
        for r in rec.referencias
    ]

    alert = None
    if rec.alerta_nao_leilao:
        alert = {
            "reasons": rec.alerta_nao_leilao.motivos,
            "suggested_mechanism": rec.alerta_nao_leilao.mecanismo_sugerido.value,
            "explanation": rec.alerta_nao_leilao.explicacao,
        }

    return {
        "recommended_format": rec.formato.value,
        "confidence_score": rec.score_confianca,
        "justification": rec.justificativa,
        "parameters": params,
        "saving_estimate": saving,
        "theoretical_references": refs,
        "no_auction_alert": alert,
    }


def _sim_to_dict(sim: SimulacaoResult) -> dict[str, Any]:
    suppliers = [
        {
            "id": f.id,
            "archetype": f.arquetipo.value,
            "relative_cost": round(f.custo_relativo, 2),
            "interest": round(f.interesse, 2),
            "acceptance_threshold_pct": f.threshold_minimo,
        }
        for f in sim.fornecedores
    ]

    # Summarize events to avoid token bloat: group by moment + type
    event_summary: list[dict[str, Any]] = []
    for ev in sim.eventos:
        event_summary.append({
            "moment": ev.momento,
            "type": ev.tipo.value,
            "archetype": ev.fornecedor.arquetipo.value if ev.fornecedor else None,
            "price_vs_best_pct": ev.preco_relativo,
            "description": ev.descricao,
        })

    alerts = [
        {
            "type": a.tipo.value,
            "severity": a.severidade,
            "description": a.descricao,
        }
        for a in sim.alertas
    ]

    return {
        "format": sim.formato.value,
        "suppliers": suppliers,
        "events": event_summary,
        "risk_alerts": alerts,
        "deterministic_narrative": sim.narrativa,
        "estimated_final_price_pct": sim.preco_final_estimado_pct,
        "likely_winner_archetype": (
            sim.vencedor_provavel.arquetipo.value if sim.vencedor_provavel else None
        ),
    }


# ──────────────────────────────────────────────────────────────────────
# CLIENTE ANTHROPIC (lazy init)
# ──────────────────────────────────────────────────────────────────────

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        if not config.ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. Set it in Streamlit secrets "
                "or as an environment variable."
            )
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


def _call_claude(user_prompt: str, max_tokens: int = 1024) -> str:
    """
    Wrapper com tratamento de erros para chamadas à Claude API.
    Retorna string com a resposta ou mensagem de erro amigável.
    """
    try:
        client = _get_client()
        message = client.messages.create(
            model=config.MODEL_DEFAULT,
            max_tokens=max_tokens,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return message.content[0].text

    except ValueError as exc:
        return f"[Configuration error] {exc}"

    except anthropic.AuthenticationError:
        return (
            "[API error] Invalid API key. Please check your ANTHROPIC_API_KEY "
            "in Streamlit secrets or environment variables."
        )

    except anthropic.RateLimitError:
        return (
            "[API error] Rate limit reached. Please wait a moment and try again."
        )

    except anthropic.APITimeoutError:
        return (
            "[API error] Request timed out. The Claude API did not respond in time. "
            "Try again in a few seconds."
        )

    except anthropic.APIStatusError as exc:
        return (
            f"[API error] Unexpected API response (status {exc.status_code}). "
            f"Details: {exc.message}"
        )

    except anthropic.APIConnectionError:
        return (
            "[API error] Could not reach the Anthropic API. "
            "Check your internet connection and try again."
        )

    except Exception as exc:  # noqa: BLE001
        return f"[Unexpected error] {type(exc).__name__}: {exc}"


# ──────────────────────────────────────────────────────────────────────
# FUNÇÃO 1 — Narrativa da simulação
# ──────────────────────────────────────────────────────────────────────

def gerar_narrativa_simulacao(
    inp: InputLeilao,
    rec: Recomendacao,
    sim: SimulacaoResult,
) -> str:
    """
    Recebe os dados estruturados do motor e simulador, e retorna uma narrativa
    rica em linguagem natural sobre como o leilão deve se desenrolar.

    Descreve: ondas de lance, comportamento por arquétipo, momento de virada,
    riscos principais e o que o comprador deve monitorar durante o evento.
    """
    payload = {
        "task": "simulate_auction_narrative",
        "inputs": _inp_to_dict(inp),
        "recommendation": _rec_to_dict(rec),
        "simulation": _sim_to_dict(sim),
    }

    user_prompt = f"""\
Based on the structured auction data below, write a rich narrative describing \
how this reverse auction is expected to unfold. Your response must follow this structure:

**Opening Phase**
Describe what happens in the first minutes: who bids, at what price level, and why.

**Mid-Auction Dynamics**
Describe the competitive dynamics in the middle period: who applies pressure, \
who waits, and what signals suppliers are reading.

**Final Sprint**
Describe the closing phase: sniping behavior, auto-extension triggers (if applicable), \
and the likely final price range.

**Key Risk to Watch**
One specific risk the buyer should monitor during the event (from the risk alerts \
or simulation data). Be concrete — what to look for and what to do if it happens.

Keep the total response under 350 words. Be direct and concrete. \
Use percentages relative to the best proposal received.

DATA:
{json.dumps(payload, ensure_ascii=False, indent=2)}
"""
    return _call_claude(user_prompt, max_tokens=600)


# ──────────────────────────────────────────────────────────────────────
# FUNÇÃO 2 — Justificativa aprofundada
# ──────────────────────────────────────────────────────────────────────

def gerar_justificativa_aprofundada(
    inp: InputLeilao,
    rec: Recomendacao,
) -> str:
    """
    Gera uma justificativa mais profunda que a determinística do motor,
    citando as referências teóricas com contexto aplicado ao cenário específico.

    Explica o "porquê" da recomendação de formato e parâmetros com base
    em teoria dos leilões e princípios de procurement estratégico.
    """
    payload = {
        "task": "deep_format_justification",
        "inputs": _inp_to_dict(inp),
        "recommendation": _rec_to_dict(rec),
    }

    ref_titles = [r.livro for r in rec.referencias]

    user_prompt = f"""\
Based on the auction scenario data below, write a deep justification for the \
recommended format. Your response must follow this structure:

**Why This Format**
In 2-3 sentences: explain the core logic of choosing {rec.formato.value} \
for this specific combination of inputs. Focus on the decisive factors \
(number of suppliers, behavior, collusion risk, etc.).

**Theoretical Grounding**
Cite 2 of the following references with specific application to this scenario: \
{', '.join(ref_titles)}. \
Each citation should be 1-2 sentences connecting the theory to the actual inputs.

**Parameter Rationale**
Explain the key parameter choices (opening price, decrement/increment, duration) \
in terms of what they are designed to extract from this specific supplier field.

**When This Could Go Wrong**
One scenario where this recommendation might underperform and what the buyer \
should do if that happens.

Keep the total response under 400 words. Be direct, specific, and avoid generic statements.

DATA:
{json.dumps(payload, ensure_ascii=False, indent=2)}
"""
    return _call_claude(user_prompt, max_tokens=700)


# ──────────────────────────────────────────────────────────────────────
# TESTES
# ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from motor import recomendar
    from simulador import simular

    print("BidWise — prompt_engine.py test")
    print("=" * 70)

    from motor import Fornecedor
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

    print(f"Format: {rec.formato.value}")
    print(f"Confidence: {rec.score_confianca}")
    print(f"API key present: {bool(config.ANTHROPIC_API_KEY)}")
    print()

    try:
        print("--- Simulation Narrative (Claude API) ---")
        narrativa = gerar_narrativa_simulacao(inp, rec, sim)
        print(narrativa)
        print()

        print("--- Deep Justification (Claude API) ---")
        justificativa = gerar_justificativa_aprofundada(inp, rec)
        print(justificativa)

    except Exception as exc:
        print(f"[Test skipped] {type(exc).__name__}: {exc}")
        print("Set ANTHROPIC_API_KEY environment variable to run API tests.")
