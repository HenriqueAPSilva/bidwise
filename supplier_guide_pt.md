## Como Modelar Seus Fornecedores

O BidWise usa dois inputs por fornecedor — **Comportamento** e **Interesse Estratégico** — para prever a dinâmica do leilão. Esses dois campos são flexíveis o suficiente para modelar situações complexas do mundo real. Veja como.

### Entendendo as combinações

| Comportamento | Interesse | Arquétipo | O que significa |
|---------------|-----------|-----------|----------------|
| Competitivo | Alto | Aggressive Leader | Vai dar lances cedo, frequente e agressivo. Puxa o preço pra baixo. |
| Competitivo | Médio | Cautious Follower | Observa o ranking, ativa no sprint final. |
| Moderado | Alto | Cautious Follower | Interessado mas calculista. Não vai se expor demais. |
| Moderado | Médio | Floor-setter | Marca posição, espera. Não revela o piso real. |
| Moderado | Baixo | Floor-setter | Participa mas passivamente. |
| Conservador | Alto | Floor-setter | Quer o contrato mas já deu o melhor preço. |
| Conservador | Médio | Dropout Candidate | Pode desistir se pressionado. |
| Conservador | Baixo | Dropout Candidate | Provavelmente não vai dar lances ativamente. |

### Cenários do mundo real

**🏢 O Incumbente**
O fornecedor que atualmente possui o contrato. Custos de troca (switching costs) jogam a favor dele — o comprador prefere mantê-lo se o preço estiver próximo. Ele raramente precisa ser agressivo.

→ Modele como: **Comportamento Moderado + Interesse Médio** (quer manter mas não vai lutar muito)
→ Se for um incumbente acomodado: **Conservador + Baixo**

**📉 O "Já Veio Barato"**
Entrou com preço agressivo na RFQ/rodada de equalização, mas não tem mais espaço pra descer. O preço equalizado dele JÁ É o piso.

→ Modele como: **Conservador + Alto** (quer o contrato mas não consegue mover mais)

**🌎 O Agressor Regional**
Empresa local com vantagem logística, com fome de market share. Vai cortar preço pra ganhar.

→ Modele como: **Competitivo + Alto**

**🏛️ A Multinacional**
Grande multinacional com política de preços global. Equipe local tem autoridade limitada para desviar das tabelas aprovadas pela matriz.

→ Modele como: **Conservador + Médio**

**🆕 O Novo Entrante**
Fornecedor tentando entrar no seu mercado. Aceita margens menores para estabelecer um caso de referência ou construir relacionamento.

→ Modele como: **Competitivo + Alto**

**😐 O Participante Relutante**
Foi convidado mas não quer realmente o contrato. Participa para manter o relacionamento ou por obrigação.

→ Modele como: **Conservador + Baixo** (BidWise vai classificar como Dropout Candidate)

**🏭 O Fornecedor com Capacidade Ociosa**
Tem excesso de capacidade produtiva e precisa de volume para diluir custo fixo. Altamente motivado a ganhar a quase qualquer preço.

→ Modele como: **Competitivo + Alto**

**💎 O Fornecedor Premium**
Vende qualidade e serviço, não preço. Não vai competir num leilão puramente de preço. Sua proposta de valor é suporte pós-venda, confiabilidade ou superioridade técnica.

→ Modele como: **Conservador + Baixo**

### Dicas

- **Na dúvida, use Comportamento Moderado + Interesse Médio.** Este é o perfil neutro — o BidWise vai classificar como Floor-setter, que é o comportamento mais comum no mundo real.

- **O input mais impactante é o valor da proposta.** Mesmo que você não tenha certeza sobre o comportamento, inserir propostas equalizadas precisas dá ao BidWise os dados de dispersão necessários para boas recomendações.

- **Teste perfis diferentes.** Use o recurso Comparar Cenários para ver como mudar o perfil de um fornecedor afeta a recomendação. Por exemplo: o que acontece se o incumbente ficar mais agressivo?
