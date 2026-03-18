"""
i18n.py — Internacionalização do BidWise
Suporta EN (inglês) e PT-BR (português brasileiro).
"""

from __future__ import annotations

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "page_title": "BidWise — Reverse Auction Strategy Advisor",
        "tagline": "Powered by auction theory & Coupa platform rules",
        "privacy_bar": (
            "🔒 No cookies · No tracking · No data stored · "
            "Your scenarios exist only in your active session"
        ),
        "tab_advisor": "Auction Advisor",
        "tab_about": "About BidWise",
        "sidebar_title": "Configure your auction",
        "num_suppliers": "Number of qualified suppliers",
        "num_suppliers_help": "Total suppliers invited and qualified to participate.",
        "kraljic": "Kraljic quadrant",
        "kraljic_help": (
            "Position of this item on the Kraljic matrix. "
            "Leverage items (high spend, many suppliers) are the best auction candidates. "
            "Strategic items carry supply-continuity risk — auction with caution. "
            "Bottleneck items have few substitutes and respond poorly to price pressure. "
            "Non-critical items have low strategic relevance."
        ),
        "commoditization": "Item commoditization",
        "commoditization_help": (
            "How interchangeable this item is across suppliers. "
            "High: standard spec, any qualified supplier can deliver identically — "
            "auctions work best here. "
            "Medium: some differentiation exists but alternatives are available. "
            "Low: custom or proprietary spec — price comparison may be misleading."
        ),
        "supplier_profiles": "Supplier profiles",
        "name": "Name",
        "proposal": "Proposal value ($)",
        "proposal_help": (
            "Enter the equalized proposal value from the prior quotation round "
            "(RFQ/RFP). All calculations are performed locally in your browser "
            "— no data is transmitted."
        ),
        "interest": "Strategic interest",
        "interest_help": (
            "How much this supplier needs this contract. "
            "High: strategic account for them — they will bid hard to win. "
            "Medium: interested but winning is not critical. "
            "Low: indifferent — may not bid actively or may withdraw."
        ),
        "behavior": "Behavior",
        "behavior_help": (
            "Expected bidding style based on past interactions or market knowledge. "
            "Competitive: bids aggressively and responds quickly to being outbid. "
            "Moderate: calculated approach, bids when meaningful moves are available. "
            "Conservative: risk-averse, may withdraw if the auction gets too aggressive."
        ),
        "analyze": "Analyze",
        "reset": "🔄 Reset",
        "tip_min_proposals": (
            "Tip: Enter at least 2 supplier proposals for a more accurate "
            "spread calculation."
        ),
        "get_started": (
            "Configure your auction parameters in the sidebar and click **Analyze** to get started."
        ),
        "spread_warning": (
            "⚠️ Price spread exceeds 50%. Consider reviewing equalization data for outliers."
        ),
        "spread_warning_extreme": (
            "⚠️ Price spread exceeds 100%. This strongly suggests an outlier proposal or inconsistent equalization. Review data before proceeding."
        ),
        "saving_flat_warning": (
            "⚠️ All scenarios converge to the same estimate. This typically indicates a narrow price spread or low competitive pressure among suppliers."
        ),
        "bottleneck_large_field": (
            "ℹ️ Bottleneck classification is unusual with this many qualified suppliers. Consider re-evaluating the Kraljic classification for this item."
        ),
        "suggested_mechanism": "Suggested mechanism:",
        "optimized_params": "Optimized Parameters",
        "min_decrement": "Min. Decrement",
        "opening_price": "Opening",
        "duration": "Duration",
        "thermometer": "Thermometer",
        "est_rounds": "Est. Rounds",
        "dutch_increment": "Dutch Increment",
        "best_response": "Best Response",
        "best_response_note": "Suppliers enter with equalized prices",
        "opening_label": "Opening price",
        "opening_strategy": "Opening price strategy",
        "opening_suggestion": "Use BidWise suggestion ({pct:+.1f}% vs. best proposal)",
        "opening_equalization": "Use best proposal as ceiling (0% adjustment)",
        "opening_custom": "Custom adjustment",
        "opening_custom_label": "Custom opening price (% vs. best proposal)",
        "opening_ceiling_warning": (
            "Ceiling option requires at least one supplier proposal with a value. "
            "Using BidWise suggestion instead."
        ),
        "auto_ext_delta": "+{mins} min auto-ext.",
        "param_col_parameter": "Parameter",
        "param_col_value_pct": "Value (%)",
        "param_col_value_brl": "Value ($)",
        "min_decrement_param": "Minimum decrement",
        "opening_price_param": "Opening price",
        "duration_param": "Auction duration",
        "auto_ext_param": "Auto-extension (if bid in last {trigger} min)",
        "thermometer_param": "Thermometer visibility",
        "rounds_param": "Estimated rounds ({interval} min each)",
        "dutch_increment_param": "Dutch increment per tick",
        "saving_estimate": "Saving Estimate",
        "pessimistic": "Pessimistic saving",
        "realistic": "Realistic saving",
        "optimistic": "Optimistic saving",
        "projected_close_pessimistic": "Projected close (pessimistic)",
        "projected_close_realistic": "Projected close (realistic)",
        "projected_close_optimistic": "Projected close (optimistic)",
        "download_pdf": "📄 Download PDF",
        "chart_no_data": (
            "Enter supplier proposal values to see the uncertainty projection chart."
        ),
        "disclaimer_template": (
            "Estimates based on {format} dynamics with {n} suppliers and {spread:.1f}% "
            "price spread. Actual results depend on market conditions and real-time "
            "supplier behavior."
        ),
        "simulation": "Supplier Behavior Simulation",
        "archetype_aggressive": "Bids early and aggressively to discourage competitors",
        "archetype_cautious": "Watches ranking, activates in the final sprint",
        "archetype_floor": "Marks initial position without revealing true price floor",
        "archetype_dropout": "Conservative or low interest — likely to withdraw early",
        "projected_outcome": "**Projected outcome:**",
        "compare": "Compare Scenarios",
        "compare_max": "Max 3 scenarios saved. Remove one to add more.",
        "scenario_name_placeholder": "e.g., Base case, Aggressive, Conservative...",
        "save_scenario": "Save scenario",
        "scenario_saved": "'{label}' saved.",
        "clear_all": "🗑️ Clear all scenarios",
        "compare_hint": "Save your current scenario to compare configurations side by side.",
        "compare_one_saved": "Save another scenario to compare side by side.",
        "col_saving": "**Saving:**",
        "col_decrement": "**Decrement:**",
        "col_duration": "**Duration:**",
        "col_rounds": "**Rounds:**",
        "col_projected": "**Projected price:**",
        "take_to_ai": "📋 Take this analysis to your preferred AI",
        "copy_prompt_hint": (
            "Copy this prompt and paste it into any AI assistant you trust for a deeper analysis. "
            "No data leaves your browser unless you choose to share it."
        ),
        "theoretical": "Theoretical Foundation",
        "no_references": "No references available for this scenario.",
        "sidebar_no_analysis_tip": "👇 Fill in your scenario below and click **Analyze** to generate your report.",
        "about_from_sidebar": "ℹ️ About BidWise",
        "mobile_tip": "📱 On mobile, tap the **<** arrow at the top left to edit your scenario.",
        "mobile_edit_tip": "To edit your scenario, tap the arrow (›) at the top left corner",
        "footer_text": "Built by <b>Henrique Silva</b> — Strategic Sourcing Analyst",
        "github_link": "github.com/HenriqueAPSilva/bidwise",
        # PDF labels
        "pdf_report_title": "Reverse Auction Strategy Report",
        "pdf_generated_on": "Generated on {now}",
        "pdf_scenario_summary": "Scenario Summary",
        "pdf_param_header": "Parameter",
        "pdf_value_header": "Value",
        "pdf_supplier_header": "Supplier",
        "pdf_proposal_header": "Proposal ($)",
        "pdf_behavior_header": "Behavior",
        "pdf_interest_header": "Strategic Interest",
        "pdf_num_suppliers": "Number of suppliers",
        "pdf_price_spread": "Price spread",
        "pdf_section_rec": "1. Recommended Format",
        "pdf_section_params": "2. Optimized Parameters",
        "pdf_no_params": "No parameters available for this scenario.",
        "pdf_section_saving": "3. Saving Estimate",
        "pdf_no_saving": "No saving estimate available for this scenario.",
        "pdf_saving_pessimistic": "Pessimistic",
        "pdf_saving_realistic": "Realistic",
        "pdf_saving_optimistic": "Optimistic",
        "pdf_saving_note": (
            "Estimates based on auction theory benchmarks and historical procurement data. "
            "Actual saving depends on market conditions and supplier behavior."
        ),
        "pdf_section_simulation": "4. Supplier Behavior Simulation",
        "pdf_supplier_field": "Supplier field: {dist}",
        "pdf_projected_outcome": (
            "<b>Projected outcome:</b> {winner} wins at {pct:+.1f}% vs. best proposal "
            "received (saving: {saving:.1f}%)."
        ),
        "pdf_section_alerts": "5. Risk Alerts",
        "pdf_section_chart": "6. Uncertainty Projection",
        "pdf_no_chart": (
            "No chart available — enter supplier proposal values in the input form."
        ),
        "pdf_section_references": "7. Theoretical References",
        "pdf_book_header": "Book",
        "pdf_author_header": "Author",
        "pdf_concept_header": "Applied Concept",
        "pdf_footer_gen": "Generated by BidWise — github.com/HenriqueAPSilva/bidwise",
        "pdf_footer_disclaimer": (
            "This report is a recommendation tool. "
            "Final auction configuration decisions remain with the procurement professional."
        ),
        "pdf_confidence_high": "High confidence ({score:.0%})",
        "pdf_confidence_mid": "Moderate confidence ({score:.0%})",
        "pdf_confidence_low": "Low confidence — formats are close ({score:.0%})",
    },
    "pt": {
        "page_title": "BidWise — Consultor de Estratégia de Leilão Reverso",
        "tagline": "Baseado em teoria dos leilões e regras da plataforma Coupa",
        "privacy_bar": (
            "🔒 Sem cookies · Sem rastreamento · Nenhum dado armazenado · "
            "Seus cenários existem apenas na sessão ativa"
        ),
        "tab_advisor": "Consultor de Leilão",
        "tab_about": "Sobre o BidWise",
        "sidebar_title": "Configure seu leilão",
        "num_suppliers": "Número de fornecedores qualificados",
        "num_suppliers_help": (
            "Total de fornecedores convidados e qualificados para participar."
        ),
        "kraljic": "Quadrante Kraljic",
        "kraljic_help": (
            "Posição do item na matriz Kraljic. "
            "Itens de Alavancagem (alto gasto, muitos fornecedores) são os melhores candidatos para leilão. "
            "Itens Estratégicos têm risco de continuidade de fornecimento — licitar com cautela. "
            "Itens de Gargalo têm poucos substitutos e respondem mal à pressão de preço. "
            "Itens Não críticos têm baixa relevância estratégica."
        ),
        "commoditization": "Comoditização do item",
        "commoditization_help": (
            "Grau de intercambialidade do item entre fornecedores. "
            "Alto: especificação padrão, qualquer fornecedor qualificado entrega de forma idêntica — "
            "leilões funcionam melhor aqui. "
            "Médio: existe alguma diferenciação, mas alternativas estão disponíveis. "
            "Baixo: especificação customizada ou proprietária — comparação de preços pode ser enganosa."
        ),
        "supplier_profiles": "Perfis dos fornecedores",
        "name": "Nome",
        "proposal": "Valor da proposta ($)",
        "proposal_help": (
            "Insira o valor da proposta equalizada da rodada anterior de cotação (RFQ/RFP). "
            "Todos os cálculos são realizados localmente no seu navegador — nenhum dado é transmitido."
        ),
        "interest": "Interesse estratégico",
        "interest_help": (
            "O quanto este fornecedor precisa deste contrato. "
            "Alto: conta estratégica para eles — vão licitar forte para vencer. "
            "Médio: interessado, mas vencer não é crítico. "
            "Baixo: indiferente — pode não licitar ativamente ou desistir."
        ),
        "behavior": "Comportamento",
        "behavior_help": (
            "Estilo esperado de lance baseado em interações anteriores ou conhecimento de mercado. "
            "Competitivo: lances agressivos e resposta rápida ao ser superado. "
            "Moderado: abordagem calculada, lances quando há movimentos significativos. "
            "Conservador: avesso a risco, pode desistir se o leilão ficar muito agressivo."
        ),
        "analyze": "Analisar",
        "reset": "🔄 Limpar",
        "tip_min_proposals": (
            "Dica: Insira pelo menos 2 propostas para um cálculo de dispersão mais preciso."
        ),
        "get_started": (
            "Configure os parâmetros do leilão na barra lateral e clique em **Analisar** para começar."
        ),
        "spread_warning": (
            "⚠️ Dispersão de preços acima de 50%. Revise os dados da rodada de equalização."
        ),
        "spread_warning_extreme": (
            "⚠️ Dispersão de preços acima de 100%. Isso indica fortemente uma proposta fora do padrão ou equalização inconsistente. Revise os dados antes de prosseguir."
        ),
        "saving_flat_warning": (
            "⚠️ Todos os cenários convergem para a mesma estimativa. Isso normalmente indica uma dispersão de preços estreita ou baixa pressão competitiva entre os fornecedores."
        ),
        "bottleneck_large_field": (
            "ℹ️ A classificação Gargalo é incomum com tantos fornecedores qualificados. Considere reavaliar a classificação Kraljic deste item."
        ),
        "suggested_mechanism": "Mecanismo sugerido:",
        "optimized_params": "Parâmetros Otimizados",
        "min_decrement": "Decremento Mín.",
        "opening_price": "Abertura",
        "duration": "Duração",
        "thermometer": "Termômetro",
        "est_rounds": "Rodadas Est.",
        "dutch_increment": "Incremento Holandês",
        "best_response": "Melhor Resposta",
        "best_response_note": "Fornecedores entram com as propostas equalizadas",
        "opening_label": "Preço de abertura",
        "opening_strategy": "Estratégia de preço de abertura",
        "opening_suggestion": "Usar sugestão do BidWise ({pct:+.1f}% vs. melhor proposta)",
        "opening_equalization": "Usar melhor proposta como teto (0% de ajuste)",
        "opening_custom": "Ajuste personalizado",
        "opening_custom_label": "Preço de abertura personalizado (% vs. melhor proposta)",
        "opening_ceiling_warning": (
            "A opção de teto requer ao menos uma proposta com valor. "
            "Usando sugestão do BidWise."
        ),
        "auto_ext_delta": "+{mins} min prorrogação.",
        "param_col_parameter": "Parâmetro",
        "param_col_value_pct": "Valor (%)",
        "param_col_value_brl": "Valor ($)",
        "min_decrement_param": "Decremento mínimo",
        "opening_price_param": "Preço de abertura",
        "duration_param": "Duração do leilão",
        "auto_ext_param": "Prorrogação automática (lance nos últimos {trigger} min)",
        "thermometer_param": "Visibilidade do termômetro",
        "rounds_param": "Rodadas estimadas ({interval} min cada)",
        "dutch_increment_param": "Incremento holandês por tick",
        "saving_estimate": "Estimativa de Saving",
        "pessimistic": "Saving pessimista",
        "realistic": "Saving realista",
        "optimistic": "Saving otimista",
        "projected_close_pessimistic": "Fechamento projetado (pessimista)",
        "projected_close_realistic": "Fechamento projetado (realista)",
        "projected_close_optimistic": "Fechamento projetado (otimista)",
        "download_pdf": "📄 Baixar PDF",
        "chart_no_data": (
            "Insira valores de proposta para ver o gráfico de projeção de incerteza."
        ),
        "disclaimer_template": (
            "Estimativas baseadas na dinâmica do formato {format} com {n} fornecedores e "
            "{spread:.1f}% de dispersão. Resultados reais dependem das condições de mercado "
            "e do comportamento dos fornecedores em tempo real."
        ),
        "simulation": "Simulação de Comportamento dos Fornecedores",
        "archetype_aggressive": "Faz lances cedo e de forma agressiva para inibir concorrentes",
        "archetype_cautious": "Observa o ranking e ativa no sprint final",
        "archetype_floor": "Marca posição inicial sem revelar o piso real de preço",
        "archetype_dropout": "Conservador ou baixo interesse — tende a se retirar cedo",
        "projected_outcome": "**Resultado projetado:**",
        "compare": "Comparar Cenários",
        "compare_max": "Máx. 3 cenários salvos. Remova um para adicionar mais.",
        "scenario_name_placeholder": "ex: Caso base, Agressivo, Conservador...",
        "save_scenario": "Salvar cenário",
        "scenario_saved": "'{label}' salvo.",
        "clear_all": "🗑️ Limpar todos",
        "compare_hint": "Salve o cenário atual para comparar configurações lado a lado.",
        "compare_one_saved": "Salve outro cenário para comparar lado a lado.",
        "col_saving": "**Saving:**",
        "col_decrement": "**Decremento:**",
        "col_duration": "**Duração:**",
        "col_rounds": "**Rodadas:**",
        "col_projected": "**Preço projetado:**",
        "take_to_ai": "📋 Leve esta análise para sua IA preferida",
        "copy_prompt_hint": (
            "Copie este prompt e cole em qualquer assistente de IA de sua confiança. "
            "Nenhum dado sai do seu navegador a menos que você escolha compartilhar."
        ),
        "theoretical": "Fundamentação Teórica",
        "no_references": "Nenhuma referência disponível para este cenário.",
        "sidebar_no_analysis_tip": "👇 Preencha seu cenário abaixo e clique em **Analisar** para gerar o relatório.",
        "about_from_sidebar": "ℹ️ Sobre o BidWise",
        "mobile_tip": "📱 No celular, toque na seta **<** no canto superior esquerdo para editar o cenário.",
        "mobile_edit_tip": "Para editar seu cenário, toque na seta (›) no canto superior esquerdo",
        "footer_text": "Criado por <b>Henrique Silva</b> — Analista de Suprimentos Estratégico",
        "github_link": "github.com/HenriqueAPSilva/bidwise",
        # PDF labels
        "pdf_report_title": "Relatório de Estratégia de Leilão Reverso",
        "pdf_generated_on": "Gerado em {now}",
        "pdf_scenario_summary": "Resumo do Cenário",
        "pdf_param_header": "Parâmetro",
        "pdf_value_header": "Valor",
        "pdf_supplier_header": "Fornecedor",
        "pdf_proposal_header": "Proposta ($)",
        "pdf_behavior_header": "Comportamento",
        "pdf_interest_header": "Interesse Estratégico",
        "pdf_num_suppliers": "Número de fornecedores",
        "pdf_price_spread": "Dispersão de preços",
        "pdf_section_rec": "1. Formato Recomendado",
        "pdf_section_params": "2. Parâmetros Otimizados",
        "pdf_no_params": "Nenhum parâmetro disponível para este cenário.",
        "pdf_section_saving": "3. Estimativa de Saving",
        "pdf_no_saving": "Nenhuma estimativa de saving disponível para este cenário.",
        "pdf_saving_pessimistic": "Pessimista",
        "pdf_saving_realistic": "Realista",
        "pdf_saving_optimistic": "Otimista",
        "pdf_saving_note": (
            "Estimativas baseadas em benchmarks de teoria dos leilões e dados históricos de compras. "
            "O saving real depende das condições de mercado e do comportamento dos fornecedores."
        ),
        "pdf_section_simulation": "4. Simulação de Comportamento dos Fornecedores",
        "pdf_supplier_field": "Grupo de fornecedores: {dist}",
        "pdf_projected_outcome": (
            "<b>Resultado projetado:</b> {winner} vence a {pct:+.1f}% vs. melhor proposta "
            "recebida (saving: {saving:.1f}%)."
        ),
        "pdf_section_alerts": "5. Alertas de Risco",
        "pdf_section_chart": "6. Projeção de Incerteza",
        "pdf_no_chart": (
            "Gráfico não disponível — insira valores de proposta no formulário."
        ),
        "pdf_section_references": "7. Referências Teóricas",
        "pdf_book_header": "Livro",
        "pdf_author_header": "Autor",
        "pdf_concept_header": "Conceito Aplicado",
        "pdf_footer_gen": "Gerado pelo BidWise — github.com/HenriqueAPSilva/bidwise",
        "pdf_footer_disclaimer": (
            "Este relatório é uma ferramenta de recomendação. "
            "As decisões finais de configuração do leilão são responsabilidade do profissional de compras."
        ),
        "pdf_confidence_high": "Alta confiança ({score:.0%})",
        "pdf_confidence_mid": "Confiança moderada ({score:.0%})",
        "pdf_confidence_low": "Baixa confiança — formatos estão próximos ({score:.0%})",
    },
}

# ──────────────────────────────────────────────────────────────────────
# DROPDOWN OPTIONS
# ──────────────────────────────────────────────────────────────────────

KRALJIC_OPTIONS: dict[str, list[str]] = {
    "en": [
        "Leverage — High impact, low risk",
        "Strategic — High impact, high risk",
        "Bottleneck — Low impact, high risk",
        "Non-critical — Low impact, low risk",
    ],
    "pt": [
        "Alavancagem — Alto impacto, baixo risco",
        "Estratégico — Alto impacto, alto risco",
        "Gargalo — Baixo impacto, alto risco",
        "Não crítico — Baixo impacto, baixo risco",
    ],
}

COMMODITIZATION_OPTIONS: dict[str, list[str]] = {
    "en": [
        "High — Standard specs, many suppliers",
        "Medium — Some differentiation, limited alternatives",
        "Low — Custom/proprietary, few substitutes",
    ],
    "pt": [
        "Alto — Especificação padrão, muitos fornecedores",
        "Médio — Alguma diferenciação, alternativas limitadas",
        "Baixo — Customizado/proprietário, poucos substitutos",
    ],
}

BEHAVIOR_OPTIONS: dict[str, list[str]] = {
    "en": [
        "Competitive — Bids aggressively, responds to pressure",
        "Moderate — Calculated bids, doesn't overextend",
        "Conservative — Risk-averse, may withdraw if pushed",
    ],
    "pt": [
        "Competitivo — Faz lances agressivos, responde à pressão",
        "Moderado — Lances calculados, não se expõe demais",
        "Conservador — Avesso a risco, pode desistir sob pressão",
    ],
}

INTEREST_OPTIONS: dict[str, list[str]] = {
    "en": [
        "High — Wants contract for future revenue, will bid hard",
        "Medium — Interested but not dependent on winning",
        "Low — Indifferent, may not bid actively",
    ],
    "pt": [
        "Alto — Quer o contrato para receita futura, vai licitar forte",
        "Médio — Interessado, mas não depende de vencer",
        "Baixo — Indiferente, pode não licitar ativamente",
    ],
}


def t(key: str, lang: str) -> str:
    """Return the translated string for key in the given language."""
    _lang = lang if lang in TRANSLATIONS else "en"
    return TRANSLATIONS[_lang].get(key, TRANSLATIONS["en"].get(key, key))
