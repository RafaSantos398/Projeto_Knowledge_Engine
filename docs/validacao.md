# Validação dos dados e limites da análise

Este documento registra o que foi verificado no CSV e a referência usada para identificar zebras. O projeto preserva uma única tabela-fonte e apresenta resultados condicionados aos rankings nela registrados. Não foi concluída uma validação histórica independente de todas as 160 referências de ranking.

## Integridade e procedência

O arquivo `data/international_matches.csv` foi baixado em 13/11/2026 de uma cópia pública do dataset de Brenda89. Seus bytes foram preservados. O download fixa o commit `6e8780b23a6453a9a18c60304b681aeec5b48da0` do repositório `andyweaves/worldcup22`.

SHA-256: `1a7f6df7751eb39edb80b5c41afedbb27892762581c0755e52431a102386658b`.

A cópia contém 23.921 registros, de 08/08/1993 a 14/06/2022, e ocupa 3.148.074 bytes. A API do Kaggle informou licença CC0, versão 12 e atualização em 28/08/2022 na consulta realizada. Essa informação descreve o catálogo consultado; a versão da cópia efetivamente analisada é identificada por seu commit e hash. Não foi estabelecida igualdade entre ela e o arquivo mais recente no Kaggle.

## Checagens reproduzidas pelo ETL

| Edição | Partidas | Seleções | Referências fixas |
| --- | --- | --- | --- |
| 2002 | 64 | 32 | 32 |
| 2006 | 64 | 32 | 32 |
| 2010 | 64 | 32 | 32 |
| 2014 | 64 | 32 | 32 |
| 2018 | 64 | 32 | 32 |
| Total | 320 | 160 participações por edição | 160 |

O filtro seleciona o torneio exato `FIFA World Cup` nos cinco anos. As 320 partidas têm os dez campos escolhidos preenchidos. Não há duplicatas por data e par de seleções, incluindo o caso de ordem invertida. Os placares são inteiros não negativos; as posições de ranking são inteiros positivos. Os resultados são coerentes com o placar, salvo a decisão por pênaltis explicitamente identificada, que exige placar empatado e vencedor informado.

O relatório [validacao_automatica.json](validacao_automatica.json) é regenerado pelo ETL. [rastreabilidade.csv](rastreabilidade.csv) identifica a linha original de cada partida, contando o cabeçalho como linha 1. [referencias_ranking.csv](referencias_ranking.csv) identifica a estreia usada em cada referência.

## Referência fixa e atualização durante o torneio

Foi escolhida a posição registrada no primeiro jogo cronológico de cada seleção na edição. A referência fica fixa até o final daquela Copa. Os rankings originais dos outros jogos permanecem nos fatos, mas não alteram o favoritismo.

Foram encontradas 27 ocorrências de ranking diferente do da estreia, envolvendo 13 seleções, todas em 2018. Por exemplo, a Rússia estreia com posição 70; o registro contra a Espanha contém posição 49. A regra usa Rússia 70 e Espanha 10, suas referências fixas, e obtém diferença 60. Usar os rankings variáveis produziria outra análise e poderia incorporar informação do próprio torneio.

O nome `ranking_pre_copa/3` foi mantido conforme a modelagem do guia. Seu significado operacional é **ranking de estreia do CSV**, uma aproximação. O nome não certifica que cada valor corresponde à posição oficial da última publicação anterior à Copa.

## Divergências históricas de 2002

A [publicação histórica apresentada como FIFA de 15/05/2002, preservada no domínio fifa2.com](https://fifa2.com/rank/main/alpha_E_latest.html), registra Brasil e Argentina empatados em segundo lugar. A posição não pode ser substituída pelo índice sequencial de uma lista ordenada.

| Seleção | Referência do CSV | Publicação histórica citada |
| --- | --- | --- |
| Argentina | 3 | 2 |
| Equador | 36 | 35 |
| Rússia | 28 | 27 |
| Tunísia | 31 | 30 |

O guia fornecido já registrava essas quatro divergências. A publicação histórica foi consultada, mas não constitui uma validação integral da proveniência do espelho. Os valores externos não foram incorporados à base. As posições do CSV permanecem rastreáveis e a limitação deve acompanhar os resultados.

## Divergências históricas de 2006

O CSV registra `Serbia` na posição 47 e Costa Rica na posição 26. O guia informa referências divergentes de 44 e 25. A [publicação contemporânea de 01/07/2006](https://www.italiausa.com/ra/2637.htm), com a tabela de maio, apresenta Costa Rica em 26, sustentando o valor do CSV. A tabela nela disponível não cobre Sérvia e Montenegro.

A divergência de Sérvia e Montenegro não foi encerrada com uma publicação primária integral. Nenhum desses valores foi corrigido. Em termos de identidade histórica, `Serbia` em 2006 é padronizado como `servia_e_montenegro`, separado de `servia` em 2010 e 2018. A padronização altera o rótulo, não o ranking.

## Decisão adotada e implicações

O programa utiliza os rankings de estreia da própria tabela, inclusive os valores divergentes. Isso mantém a origem única dos fatos e permite reproduzir a análise sem acrescentar uma segunda base ou corrigir silenciosamente os dados.

Os resultados são válidos para essa definição operacional. Não são resultados definitivos de uma análise com todos os rankings oficiais pré-Copa validados. Se a avaliação exigir esses valores oficiais, será necessário concluir a conferência histórica e combinar com o professor uma política para correções externas antes de alterar os dados ou a interpretação. O código das consultas já funciona independentemente dessa futura decisão.

As diferenças de posições medem distância ordinal; não estimam chances de vitória. A taxa de sucesso como azarã depende do adversário e do tamanho da amostra. O mínimo de três jogos é um filtro descritivo e não um teste de significância.

## Pênaltis e testes das regras

As 16 decisões por pênaltis do recorte foram comparadas com os vencedores em [shootouts.csv, do projeto international_results](https://github.com/martj42/international_results/blob/master/shootouts.csv), em 13/11/2026. Todas coincidiram, normalizando as diferenças de nomes. O registro da conferência e o hash do arquivo consultado estão em [conferencia_penaltis.json](conferencia_penaltis.json). Esse arquivo externo serviu apenas para conferência; não é lido pelo ETL e não alimenta a base.

Os testes do ETL verificam entradas inválidas, duplicatas, recorte, nomes históricos, rastreabilidade e geração reproduzível. Os testes Prolog verificam zebra, favorita vencedora, empate, pênaltis, igualdade de ranking, agrupamentos, desempates, elegibilidade e denominadores. A igualdade de ranking é exercitada com um cenário fictício isolado, pois não há confrontos com referências fixas iguais nas 320 partidas.

O programa separado e a versão única foram executados com SWI-Prolog 10.1.20 pelo pacote oficial `swipl-wasm` 8.3.0. A validação nativa pelo comando `swipl` depende da instalação local desse programa. Os resultados em [resultados.md](resultados.md) foram exportados pelo código Prolog.
