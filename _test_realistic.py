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
            print(f"  Nao-leilao: {rec.alerta_nao_leilao.explicacao[:120]}...")
            print(f"  Mecanismo: {rec.alerta_nao_leilao.mecanismo_sugerido.value}")
        if rec.parametros:
            p = rec.parametros
            abertura = getattr(p, 'preco_abertura_descricao', None) or f"{p.preco_abertura_pct:+.1f}%"
            print(f"  Decremento: {p.decremento_min_pct}%  |  Abertura: {abertura}  |  Duracao: {p.duracao_minutos}min")
            if p.prorrogacao_minutos:
                print(f"  Prorrogacao: +{p.prorrogacao_minutos}min")
            if p.rodadas_estimadas:
                print(f"  Rodadas: ~{p.rodadas_estimadas}  |  Intervalo: {p.intervalo_rodada_minutos}min")
            if p.incremento_holandes_pct:
                print(f"  Incremento holandes: {p.incremento_holandes_pct}%")
        if rec.saving:
            s = rec.saving
            mp = inp.melhor_proposta_brl
            if mp:
                pess_brl = round(mp * s.pessimista_pct / 100)
                real_brl = round(mp * s.realista_pct / 100)
                otim_brl = round(mp * s.otimista_pct / 100)
                print(f"  Saving: {s.pessimista_pct}% (${pess_brl:,}) / {s.realista_pct}% (${real_brl:,}) / {s.otimista_pct}% (${otim_brl:,})")
            else:
                print(f"  Saving: {s.pessimista_pct}% / {s.realista_pct}% / {s.otimista_pct}%")
        sim = simular(inp, rec, lang='en')
        if sim.alertas:
            for a in sim.alertas:
                print(f"  [{a.severidade}] {a.tipo.value}: {a.descricao[:80]}")
        if sim.vencedor_provavel:
            print(f"  Vencedor provavel: {sim.vencedor_provavel.nome}  ({sim.preco_final_estimado_pct}% vs melhor proposta)")
    except Exception as e:
        import traceback
        print(f"  ERRO: {type(e).__name__}: {e}")
        traceback.print_exc()

# C1 — EPI
run("C1 - EPI (luvas, capacetes, botas)",
    [Fornecedor("A", 45000, NivelTripartido.ALTO,  Comportamento.COMPETITIVO),
     Fornecedor("B", 47000, NivelTripartido.ALTO,  Comportamento.COMPETITIVO),
     Fornecedor("C", 48000, NivelTripartido.ALTO,  Comportamento.COMPETITIVO),
     Fornecedor("D", 50000, NivelTripartido.ALTO,  Comportamento.COMPETITIVO),
     Fornecedor("E", 52000, NivelTripartido.MEDIO, Comportamento.MODERADO),
     Fornecedor("F", 58000, NivelTripartido.MEDIO, Comportamento.MODERADO)],
    QuadranteKraljic.NAO_CRITICO, NivelTripartido.ALTO)

# C2 — Refratarios
run("C2 - Refratarios para alto-forno",
    [Fornecedor("A", 1_200_000, NivelTripartido.ALTO,  Comportamento.MODERADO),
     Fornecedor("B", 1_350_000, NivelTripartido.ALTO,  Comportamento.MODERADO),
     Fornecedor("C", 1_400_000, NivelTripartido.MEDIO, Comportamento.MODERADO),
     Fornecedor("D", 1_550_000, NivelTripartido.MEDIO, Comportamento.CONSERVADOR)],
    QuadranteKraljic.ALAVANCA, NivelTripartido.MEDIO)

# C3 — Manutencao eletrica especializada
run("C3 - Manutencao eletrica especializada",
    [Fornecedor("A",  800_000, NivelTripartido.ALTO,  Comportamento.COMPETITIVO),
     Fornecedor("B",  950_000, NivelTripartido.MEDIO, Comportamento.MODERADO),
     Fornecedor("C", 1_100_000, NivelTripartido.BAIXO, Comportamento.CONSERVADOR)],
    QuadranteKraljic.ESTRATEGICO, NivelTripartido.BAIXO)

# C4 — Diesel frota mineracao
run("C4 - Diesel para frota de mineracao",
    [Fornecedor("A", 3_200_000, NivelTripartido.ALTO, Comportamento.COMPETITIVO),
     Fornecedor("B", 3_250_000, NivelTripartido.ALTO, Comportamento.COMPETITIVO),
     Fornecedor("C", 3_300_000, NivelTripartido.ALTO, Comportamento.COMPETITIVO),
     Fornecedor("D", 3_350_000, NivelTripartido.ALTO, Comportamento.COMPETITIVO),
     Fornecedor("E", 3_400_000, NivelTripartido.ALTO, Comportamento.COMPETITIVO)],
    QuadranteKraljic.ALAVANCA, NivelTripartido.ALTO)

# C5 — Transporte rodov minerio
run("C5 - Transporte rodoviario de minerio",
    [Fornecedor("A", 2_500_000, NivelTripartido.ALTO,  Comportamento.COMPETITIVO),
     Fornecedor("B", 2_800_000, NivelTripartido.ALTO,  Comportamento.COMPETITIVO),
     Fornecedor("C", 3_100_000, NivelTripartido.MEDIO, Comportamento.MODERADO),
     Fornecedor("D", 3_500_000, NivelTripartido.BAIXO, Comportamento.CONSERVADOR)],
    QuadranteKraljic.ALAVANCA, NivelTripartido.MEDIO)

# C6 — Pecas reposicao britador
run("C6 - Pecas de reposicao para britador",
    [Fornecedor("A", 350_000, NivelTripartido.MEDIO, Comportamento.MODERADO),
     Fornecedor("B", 420_000, NivelTripartido.BAIXO, Comportamento.CONSERVADOR)],
    QuadranteKraljic.GARGALO, NivelTripartido.BAIXO)

# C7 — Material de escritorio
run("C7 - Material de escritorio",
    [Fornecedor("A", 12000, NivelTripartido.MEDIO, Comportamento.COMPETITIVO),
     Fornecedor("B", 12500, NivelTripartido.MEDIO, Comportamento.COMPETITIVO),
     Fornecedor("C", 13000, NivelTripartido.MEDIO, Comportamento.COMPETITIVO),
     Fornecedor("D", 13200, NivelTripartido.MEDIO, Comportamento.COMPETITIVO),
     Fornecedor("E", 13500, NivelTripartido.MEDIO, Comportamento.COMPETITIVO),
     Fornecedor("F", 14000, NivelTripartido.MEDIO, Comportamento.COMPETITIVO),
     Fornecedor("G", 14500, NivelTripartido.BAIXO, Comportamento.MODERADO),
     Fornecedor("H", 16000, NivelTripartido.BAIXO, Comportamento.MODERADO)],
    QuadranteKraljic.NAO_CRITICO, NivelTripartido.ALTO)

# C8 — Correia transportadora
run("C8 - Correia transportadora",
    [Fornecedor("A", 650_000, NivelTripartido.ALTO,  Comportamento.MODERADO),
     Fornecedor("B", 720_000, NivelTripartido.ALTO,  Comportamento.MODERADO),
     Fornecedor("C", 780_000, NivelTripartido.MEDIO, Comportamento.CONSERVADOR)],
    QuadranteKraljic.ALAVANCA, NivelTripartido.MEDIO)

# C9 — CMMS
run("C9 - Software CMMS",
    [Fornecedor("A", 180_000, NivelTripartido.ALTO,  Comportamento.COMPETITIVO),
     Fornecedor("B", 250_000, NivelTripartido.MEDIO, Comportamento.MODERADO),
     Fornecedor("C", 320_000, NivelTripartido.BAIXO, Comportamento.CONSERVADOR)],
    QuadranteKraljic.ESTRATEGICO, NivelTripartido.BAIXO)

# C10 — Reagentes quimicos
run("C10 - Reagentes quimicos para tratamento de agua",
    [Fornecedor("A",  90_000, NivelTripartido.MEDIO, Comportamento.COMPETITIVO),
     Fornecedor("B",  95_000, NivelTripartido.MEDIO, Comportamento.COMPETITIVO),
     Fornecedor("C",  98_000, NivelTripartido.MEDIO, Comportamento.COMPETITIVO),
     Fornecedor("D", 102_000, NivelTripartido.BAIXO, Comportamento.MODERADO),
     Fornecedor("E", 110_000, NivelTripartido.BAIXO, Comportamento.MODERADO)],
    QuadranteKraljic.ALAVANCA, NivelTripartido.ALTO)

# C11 — Construcao civil galpao
run("C11 - Construcao civil de galpao industrial",
    [Fornecedor("A",  8_000_000, NivelTripartido.ALTO,  Comportamento.MODERADO),
     Fornecedor("B",  8_500_000, NivelTripartido.ALTO,  Comportamento.MODERADO),
     Fornecedor("C",  9_200_000, NivelTripartido.MEDIO, Comportamento.MODERADO),
     Fornecedor("D", 10_000_000, NivelTripartido.BAIXO, Comportamento.CONSERVADOR)],
    QuadranteKraljic.ALAVANCA, NivelTripartido.MEDIO)

# C12 — Catering
run("C12 - Catering industrial",
    [Fornecedor("A", 35000, NivelTripartido.ALTO,  Comportamento.COMPETITIVO),
     Fornecedor("B", 37000, NivelTripartido.ALTO,  Comportamento.COMPETITIVO),
     Fornecedor("C", 38000, NivelTripartido.ALTO,  Comportamento.COMPETITIVO),
     Fornecedor("D", 39000, NivelTripartido.ALTO,  Comportamento.COMPETITIVO),
     Fornecedor("E", 40000, NivelTripartido.ALTO,  Comportamento.COMPETITIVO),
     Fornecedor("F", 42000, NivelTripartido.MEDIO, Comportamento.MODERADO),
     Fornecedor("G", 48000, NivelTripartido.MEDIO, Comportamento.MODERADO)],
    QuadranteKraljic.NAO_CRITICO, NivelTripartido.ALTO)

# C13 — Transformador de potencia
run("C13 - Transformador de potencia",
    [Fornecedor("A", 4_500_000, NivelTripartido.ALTO,  Comportamento.MODERADO),
     Fornecedor("B", 5_200_000, NivelTripartido.MEDIO, Comportamento.CONSERVADOR)],
    QuadranteKraljic.GARGALO, NivelTripartido.BAIXO)

# C14 — Limpeza industrial
run("C14 - Servico de limpeza industrial",
    [Fornecedor("A",  60000, NivelTripartido.ALTO,  Comportamento.COMPETITIVO),
     Fornecedor("B",  62000, NivelTripartido.ALTO,  Comportamento.COMPETITIVO),
     Fornecedor("C",  63000, NivelTripartido.ALTO,  Comportamento.COMPETITIVO),
     Fornecedor("D",  65000, NivelTripartido.ALTO,  Comportamento.COMPETITIVO),
     Fornecedor("E",  66000, NivelTripartido.ALTO,  Comportamento.COMPETITIVO),
     Fornecedor("F",  68000, NivelTripartido.ALTO,  Comportamento.COMPETITIVO),
     Fornecedor("G",  70000, NivelTripartido.MEDIO, Comportamento.COMPETITIVO),
     Fornecedor("H",  72000, NivelTripartido.MEDIO, Comportamento.MODERADO),
     Fornecedor("I",  75000, NivelTripartido.MEDIO, Comportamento.MODERADO),
     Fornecedor("J",  82000, NivelTripartido.MEDIO, Comportamento.MODERADO)],
    QuadranteKraljic.NAO_CRITICO, NivelTripartido.ALTO)

# C15 — Contrato guarda-chuva soldagem
run("C15 - Contrato guarda-chuva de soldagem",
    [Fornecedor("A", 500_000, NivelTripartido.ALTO,  Comportamento.COMPETITIVO),
     Fornecedor("B", 520_000, NivelTripartido.ALTO,  Comportamento.COMPETITIVO),
     Fornecedor("C", 540_000, NivelTripartido.ALTO,  Comportamento.COMPETITIVO),
     Fornecedor("D", 600_000, NivelTripartido.MEDIO, Comportamento.MODERADO),
     Fornecedor("E", 680_000, NivelTripartido.BAIXO, Comportamento.CONSERVADOR)],
    QuadranteKraljic.ALAVANCA, NivelTripartido.ALTO)

print("\nDone.")
