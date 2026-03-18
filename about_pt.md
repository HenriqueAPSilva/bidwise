## Sobre o BidWise

### Por que criei isso

Sou Henrique Silva, profissional de compras com mais de 7 anos em suprimentos estratégicos. Conduzi leilões reversos ao longo da minha carreira e acredito genuinamente no potencial desta ferramenta.

Todo leilão reverso começa com a mesma pergunta: qual formato devo usar e como configurá-lo? Não existe ferramenta para isso — é pura experiência e intuição. O BidWise codifica essa decisão em um motor transparente e auditável, baseado na teoria dos leilões.

### Como o motor pensa

O BidWise avalia quatro formatos de leilão e recomenda aquele que maximiza o saving esperado. Veja como funciona em detalhes:

**Passo 1 — Devo fazer um leilão?**
Antes de recomendar um formato, o BidWise verifica condições desqualificadoras: fornecedor único, itens estratégicos ou de gargalo com menos de 3 fornecedores, ou um cenário onde baixo interesse + comportamento conservador torna um leilão deserto provável. Se alguma condição for identificada, o BidWise recomenda um mecanismo alternativo (RFQ, negociação direta ou nova rodada de qualificação).

**Passo 2 — Pontuação de cada formato**
Quatro funções de pontuação rodam independentemente — uma por formato. Cada função avalia o cenário em múltiplos fatores: número de fornecedores, nível de comoditização, perfis individuais de comportamento, perfis de interesse estratégico, classificação Kraljic e dispersão de preços calculada. Cada fator adiciona ou subtrai pontos. O formato com maior pontuação total vence.

Os principais drivers por formato:

* **Leilão Reverso Inglês (ranking + termômetro):** Favorece grupos grandes (4+), alta comoditização, fornecedores competitivos, alto interesse estratégico. O termômetro amplifica a pressão psicológica.
* **Leilão Reverso Inglês (apenas ranking):** Favorece grupos moderados (3-5), comoditização média, comportamento moderado. Remove o termômetro para evitar que fornecedores calibrem o mínimo exato necessário para vencer.
* **Leilão Reverso Holandês:** Favorece grupos pequenos (2-3), fornecedores conservadores, baixa dispersão. Máxima opacidade — cada fornecedor decide independentemente. O mais próximo de um lance selado.
* **Leilão Reverso Japonês:** Favorece grupos grandes (5+), alta comoditização, comportamento heterogêneo. A eliminação progressiva força decisões ativas a cada rodada.

**Passo 3 — Calculando o decremento mínimo**
O decremento determina quanto um fornecedor deve reduzir por lance. Muito pequeno = fornecedores sobem no ranking sem competição real. Muito grande = fornecedores mais fracos desistem imediatamente.

O BidWise calcula a lacuna média entre propostas adjacentes no grupo de fornecedores e toma 40% dessa lacuna como decremento base. Isso garante que cada lance possa potencialmente mudar o ranking sem ser impossível.

O decremento é então limitado por caps dinâmicos baseados no valor do contrato:

* Contratos abaixo de $200k: faixa de 0,5% – 14% (alta autonomia, fornecedores decidem rápido)
* $200k – $2M: 0,3% – 10% (autonomia parcial)
* $2M – $10M: 0,2% – 6% (cada lance precisa de aprovação interna)
* Acima de $10M: 0,1% – 3% (decisões em nível de comitê por lance)

Ajustado pelo comportamento dos fornecedores: grupos competitivos recebem +10%, grupos conservadores recebem -20%.

**Passo 4 — Definindo o preço de abertura**
A estratégia de preço de abertura depende do formato:

* **English Reverse:** Melhor Resposta — cada fornecedor entra com sua proposta equalizada da rodada anterior de RFQ/RFP. O ranking e a pressão competitiva fazem o trabalho.
* **Dutch Reverse:** Piso definido pelo comprador. Com 4+ fornecedores: 20% abaixo da melhor proposta. Com menos: 10% abaixo. O preço sobe até alguém aceitar.
* **Japanese Reverse:** Teto definido pelo comprador. Para commodities (alta comoditização): começa na melhor proposta. Para itens complexos: começa na pior proposta, dando espaço para todos entrarem.

**Passo 5 — Duração e prorrogação**
A duração se adapta a três fatores: número de fornecedores, valor do contrato (maior = mais tempo para aprovações internas) e características do formato (o termômetro gera mais interação, precisa de mais tempo).

A prorrogação automática (apenas English) também escala com o valor do contrato: 2 minutos para contratos abaixo de $200k até 5 minutos para contratos acima de $2M. Isso captura lances de último minuto sem pressionar decisões de alto valor.

**Passo 6 — Estimativa de saving**
As estimativas de saving são calculadas por formato com quatro multiplicadores: dispersão de preços (mais espaço = mais potencial), número de fornecedores (mais competição = mais saving), comportamento predominante (competitivo = lances mais agressivos) e interesse estratégico predominante (alto interesse = mais disposição para reduzir).

Todas as estimativas são arredondadas para baixo ao múltiplo mais próximo do decremento mínimo — porque o saving só pode ocorrer em passos discretos de lance.

**Passo 7 — Simulação de comportamento dos fornecedores**
Cada fornecedor é classificado em um arquétipo com base em seu perfil individual de comportamento e interesse estratégico:

* Competitivo + Alto interesse → **Aggressive Leader**
* Competitivo + Médio / Moderado + Alto → **Cautious Follower**
* Moderado + Médio ou Baixo → **Floor-setter**
* Conservador + qualquer / qualquer + Baixo → **Dropout Candidate**

A simulação prevê quem licita quando, quem sai cedo e quem está melhor posicionado para vencer — mas nunca substitui a estimativa de saving do motor. O motor calcula os números; a simulação conta a história.

### Seus dados, seu controle

* Sem cookies. Sem rastreamento. Sem cadastro.
* Nenhum dado é armazenado — seus cenários existem apenas na sessão ativa do navegador
* Nenhum dado é transmitido a servidores externos
* O recurso "Copiar prompt" gera texto localmente — nada é enviado a menos que VOCÊ cole em algum lugar
* Analytics por Plausible (privacy-first, sem cookies, sem dados pessoais)

**Como verificar:** Abra as Ferramentas do Desenvolvedor do seu navegador (F12), vá para a aba Rede e execute uma análise. Você verá apenas requisições de assets estáticos para o Streamlit Cloud e Plausible — sem chamadas de API com seus dados.

### Código aberto

Cada linha de código está disponível em [github.com/HenriqueAPSilva/bidwise](https://github.com/HenriqueAPSilva/bidwise).

Quer construir algo parecido? Comece com um problema real no seu domínio, codifique sua expertise em regras explícitas e use IA como amplificador — não substituto. A parte mais valiosa deste projeto não é o código. É a lógica de decisão por trás dele.

### Fundamentação teórica

|Livro|Autor|Conceito aplicado|
|-|-|-|
|Auction Theory|Vijay Krishna|Seleção de formato, equivalência de receita, valores privados vs. comuns|
|The Theory of Auctions|Paul Klemperer|Valor de entrada, conluio em leilões ascendentes, redução de sinais|
|Thinking Strategically|Dixit & Nalebuff|Equilíbrios de Nash, backward induction, jogos sequenciais|
|Game Theory for Applied Economists|Robert Gibbons|Equilíbrio de Nash Bayesiano, jogos com informação incompleta|
|Negotiation Genius|Malhotra & Bazerman|Ancoragem, efeitos do preço de abertura, estratégia de prorrogação|
|The Psychology of Price|Leigh Caldwell|Efeitos psicológicos do ranking/termômetro nas decisões|
|Misbehaving|Richard H. Thaler|Aversão à perda, contabilidade mental, maldição do vencedor|
|Strategic Sourcing and Category Management|Magnus Carlsson|Matriz Kraljic e estratégias por categoria|
|eSourcing Capability Model|Sourcing Industry Group|Maturidade processual em sourcing, decisões auditáveis|

Algumas funcionalidades do BidWise — como a calibração do decremento baseada nos gaps entre propostas adjacentes, caps dinâmicos por valor do contrato e duração adaptativa — são heurísticas práticas desenvolvidas a partir de experiência real em sourcing, não derivadas de teoria formal. Acreditamos em transparência: onde o motor usa teoria, citamos. Onde usa heurísticas operacionais, rotulamos como tal.

### Criado por

**Henrique Silva** — Analista de Suprimentos Estratégico.

[LinkedIn](https://www.linkedin.com/in/henrique-alexandre-pinto-silva/) · [GitHub](https://github.com/HenriqueAPSilva)
