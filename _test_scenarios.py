import sys
sys.path.insert(0, r'C:\Users\henri\bidwise')

from motor import (
    Comportamento, Fornecedor, FormatoLeilao, InputLeilao,
    NivelTripartido, QuadranteKraljic, recomendar
)
from simulador import simular

def run(label, fornecedores, kraljic, comod):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print('='*60)
    try:
        inp = InputLeilao(fornecedores=fornecedores, kraljic=kraljic, comoditizacao=comod)
        print(f"  Spread: {inp.dispersao_precos}%  |  Melhor: {inp.melhor_proposta_brl}  |  N: {inp.num_fornecedores}")
        rec = recomendar(inp, lang='en')
        print(f"  Formato: {rec.formato.value}")
        if rec.alerta_nao_leilao:
            print(f"  Motivo não-leilão: {rec.alerta_nao_leilao.explicacao}")
        if rec.parametros:
            p = rec.parametros
            print(f"  Decremento: {p.decremento_min_pct}%  |  Abertura: {getattr(p,'preco_abertura_descricao',None) or p.preco_abertura_pct}  |  Duração: {p.duracao_minutos}min")
            if p.prorrogacao_minutos:
                print(f"  Prorrogação: +{p.prorrogacao_minutos}min")
            if p.rodadas_estimadas:
                print(f"  Rodadas: ~{p.rodadas_estimadas}")
        if rec.saving:
            s = rec.saving
            print(f"  Saving: {s.pessimista_pct}% / {s.realista_pct}% / {s.otimista_pct}%")
        sim = simular(inp, rec, lang='en')
        if sim.alertas:
            for a in sim.alertas:
                print(f"  [{a.severidade}] {a.tipo.value}: {a.descricao}")
        if sim.vencedor_provavel:
            print(f"  Vencedor provável: {sim.vencedor_provavel.nome}  ({sim.preco_final_estimado_pct}%)")
    except Exception as e:
        print(f"  ERRO: {type(e).__name__}: {e}")

# Cenário 1 — Um centavo de diferença
run("C1 — Um centavo de diferença",
    [Fornecedor("A", 100000.00, NivelTripartido.ALTO,  Comportamento.COMPETITIVO),
     Fornecedor("B", 100000.01, NivelTripartido.ALTO,  Comportamento.COMPETITIVO),
     Fornecedor("C", 100000.02, NivelTripartido.ALTO,  Comportamento.COMPETITIVO),
     Fornecedor("D", 100000.03, NivelTripartido.ALTO,  Comportamento.COMPETITIVO)],
    QuadranteKraljic.ALAVANCA, NivelTripartido.ALTO)

# Cenário 2 — Um fornecedor absurdamente barato
run("C2 — Fornecedor absurdamente barato ($1)",
    [Fornecedor("A",      1.00, NivelTripartido.MEDIO, Comportamento.MODERADO),
     Fornecedor("B", 500000.00, NivelTripartido.MEDIO, Comportamento.MODERADO),
     Fornecedor("C", 510000.00, NivelTripartido.MEDIO, Comportamento.MODERADO),
     Fornecedor("D", 520000.00, NivelTripartido.MEDIO, Comportamento.MODERADO),
     Fornecedor("E", 530000.00, NivelTripartido.MEDIO, Comportamento.MODERADO)],
    QuadranteKraljic.ALAVANCA, NivelTripartido.ALTO)

# Cenário 3 — Todos com proposta zero
run("C3 — Todos com proposta zero",
    [Fornecedor("A", 0.0, NivelTripartido.ALTO, Comportamento.COMPETITIVO),
     Fornecedor("B", 0.0, NivelTripartido.ALTO, Comportamento.COMPETITIVO),
     Fornecedor("C", 0.0, NivelTripartido.ALTO, Comportamento.COMPETITIVO)],
    QuadranteKraljic.ALAVANCA, NivelTripartido.ALTO)

# Cenário 4 — 15 fornecedores
run("C4 — 15 fornecedores",
    [Fornecedor(f"S{i+1}", 100000 + i*10000,
                NivelTripartido.ALTO if i % 2 == 0 else NivelTripartido.MEDIO,
                Comportamento.COMPETITIVO if i % 2 == 0 else Comportamento.CONSERVADOR)
     for i in range(15)],
    QuadranteKraljic.ALAVANCA, NivelTripartido.ALTO)

# Cenário 5 — Proposta negativa
run("C5 — Proposta negativa (-$50k)",
    [Fornecedor("A", -50000.0, NivelTripartido.MEDIO, Comportamento.MODERADO),
     Fornecedor("B", 100000.0, NivelTripartido.MEDIO, Comportamento.MODERADO),
     Fornecedor("C", 200000.0, NivelTripartido.MEDIO, Comportamento.MODERADO)],
    QuadranteKraljic.ALAVANCA, NivelTripartido.MEDIO)

# Cenário 6 — Conservadores, interesse alto
run("C6 — Todos conservadores, interesse alto",
    [Fornecedor("A", 500000, NivelTripartido.ALTO, Comportamento.CONSERVADOR),
     Fornecedor("B", 520000, NivelTripartido.ALTO, Comportamento.CONSERVADOR),
     Fornecedor("C", 540000, NivelTripartido.ALTO, Comportamento.CONSERVADOR),
     Fornecedor("D", 560000, NivelTripartido.ALTO, Comportamento.CONSERVADOR),
     Fornecedor("E", 580000, NivelTripartido.ALTO, Comportamento.CONSERVADOR),
     Fornecedor("F", 600000, NivelTripartido.ALTO, Comportamento.CONSERVADOR)],
    QuadranteKraljic.ALAVANCA, NivelTripartido.ALTO)

# Cenário 7 — Um fornecedor, proposta altíssima
run("C7 — 1 fornecedor, $999M",
    [Fornecedor("A", 999999999.0, NivelTripartido.ALTO, Comportamento.COMPETITIVO)],
    QuadranteKraljic.NAO_CRITICO, NivelTripartido.ALTO)

# Cenário 8 — Dois fornecedores idênticos
run("C8 — 2 fornecedores idênticos ($500k, $500k)",
    [Fornecedor("A", 500000.0, NivelTripartido.MEDIO, Comportamento.MODERADO),
     Fornecedor("B", 500000.0, NivelTripartido.MEDIO, Comportamento.MODERADO)],
    QuadranteKraljic.ALAVANCA, NivelTripartido.ALTO)

# Cenário 9 — Spread 0%, perfis diferentes
run("C9 — Spread 0%, 4 perfis diferentes",
    [Fornecedor("A", 100000.0, NivelTripartido.ALTO,  Comportamento.COMPETITIVO),
     Fornecedor("B", 100000.0, NivelTripartido.MEDIO, Comportamento.MODERADO),
     Fornecedor("C", 100000.0, NivelTripartido.BAIXO, Comportamento.CONSERVADOR),
     Fornecedor("D", 100000.0, NivelTripartido.BAIXO, Comportamento.COMPETITIVO)],
    QuadranteKraljic.ALAVANCA, NivelTripartido.ALTO)

# Cenário 10 — Microvalores
run("C10 — Microvalores ($0.50, $0.75, $1.00)",
    [Fornecedor("A", 0.50, NivelTripartido.ALTO, Comportamento.COMPETITIVO),
     Fornecedor("B", 0.75, NivelTripartido.ALTO, Comportamento.COMPETITIVO),
     Fornecedor("C", 1.00, NivelTripartido.ALTO, Comportamento.COMPETITIVO)],
    QuadranteKraljic.NAO_CRITICO, NivelTripartido.ALTO)

# Cenário 11 — Bilhão, item estratégico
run("C11 — $1B, Estratégico, baixa commoditização",
    [Fornecedor("A", 1_000_000_000.0, NivelTripartido.MEDIO, Comportamento.MODERADO),
     Fornecedor("B", 1_100_000_000.0, NivelTripartido.MEDIO, Comportamento.MODERADO),
     Fornecedor("C", 1_200_000_000.0, NivelTripartido.MEDIO, Comportamento.MODERADO)],
    QuadranteKraljic.ESTRATEGICO, NivelTripartido.BAIXO)

# Cenário 12 — Metade sem proposta
run("C12 — 6 fornecedores, 3 sem proposta",
    [Fornecedor("A", 100000.0, NivelTripartido.MEDIO, Comportamento.MODERADO),
     Fornecedor("B", 120000.0, NivelTripartido.MEDIO, Comportamento.MODERADO),
     Fornecedor("C", 140000.0, NivelTripartido.MEDIO, Comportamento.MODERADO),
     Fornecedor("D", None, NivelTripartido.MEDIO, Comportamento.MODERADO),
     Fornecedor("E", None, NivelTripartido.MEDIO, Comportamento.MODERADO),
     Fornecedor("F", None, NivelTripartido.MEDIO, Comportamento.MODERADO)],
    QuadranteKraljic.ALAVANCA, NivelTripartido.MEDIO)

# Cenário 13 — Gargalo, campo grande
run("C13 — Gargalo, 8 fornecedores competitivos",
    [Fornecedor(f"S{i+1}", 50000 + i*5714, NivelTripartido.ALTO, Comportamento.COMPETITIVO)
     for i in range(8)],
    QuadranteKraljic.GARGALO, NivelTripartido.BAIXO)

# Cenário 14 — Japonês forçado, mega contrato
run("C14 — 5 fornecedores, $50M–$58M",
    [Fornecedor("A", 50_000_000, NivelTripartido.ALTO, Comportamento.MODERADO),
     Fornecedor("B", 52_000_000, NivelTripartido.ALTO, Comportamento.MODERADO),
     Fornecedor("C", 54_000_000, NivelTripartido.ALTO, Comportamento.MODERADO),
     Fornecedor("D", 56_000_000, NivelTripartido.ALTO, Comportamento.MODERADO),
     Fornecedor("E", 58_000_000, NivelTripartido.ALTO, Comportamento.MODERADO)],
    QuadranteKraljic.ALAVANCA, NivelTripartido.ALTO)

# Cenário 15 — Fornecedor fantasma ($1M entre $100k–$115k)
run("C15 — Fornecedor fantasma ($1M outlier)",
    [Fornecedor("A", 100000.0, NivelTripartido.MEDIO, Comportamento.MODERADO),
     Fornecedor("B", 105000.0, NivelTripartido.MEDIO, Comportamento.MODERADO),
     Fornecedor("C", 110000.0, NivelTripartido.MEDIO, Comportamento.MODERADO),
     Fornecedor("D", 115000.0, NivelTripartido.MEDIO, Comportamento.MODERADO),
     Fornecedor("E", 1000000.0, NivelTripartido.BAIXO, Comportamento.CONSERVADOR)],
    QuadranteKraljic.ALAVANCA, NivelTripartido.ALTO)

print("\nDone.")
