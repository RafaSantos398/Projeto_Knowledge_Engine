# Zebras nas Copas do Mundo de 2002 a 2018

Projeto de Knowledge Engine para Lógica e Matemática Discreta. A base reúne as 320 partidas das Copas de 2002, 2006, 2010, 2014 e 2018, incluindo a disputa de terceiro lugar. O objetivo é investigar vitórias de seleções pior colocadas no ranking e comparar essas surpresas por partida, edição e seleção.

O Python seleciona e valida os dados e gera a base de fatos e o arquivo de consultas. **As regras, as agregações, a ordenação e as respostas às três perguntas são executadas em Prolog.**

## Definição de zebra e referência de ranking

Uma zebra é uma vitória da seleção com posição numérica maior no ranking. Não há diferença mínima adicional. Vitórias nos pênaltis contam; empates sem pênaltis não são zebras. Confrontos com rankings iguais não têm favorita ou azarã.

Usamos uma referência fixa por seleção e edição: **o ranking registrado na estreia da equipe no CSV**. Esse valor é uma aproximação do ranking pré-Copa; não é alterado pelos registros das partidas seguintes. No código, o predicado correspondente chama-se `ranking_pre_copa/3`.

Há divergências históricas conhecidas em 2002 e 2006. A análise preserva os valores da única tabela-fonte, sem correções externas. Portanto, os resultados são condicionados à referência do CSV e não devem ser apresentados como uma análise com todos os rankings oficiais historicamente validados. A política e as divergências estão em [docs/validacao.md](docs/validacao.md).

## Três perguntas

1. **Quais foram as dez maiores zebras?** Calculamos a posição da vencedora menos a posição da perdedora. Ordenamos pela diferença decrescente; em empate, pela data crescente e pelos nomes da vencedora e da perdedora. O resultado inclui edição, data, seleções, rankings, diferença e pênaltis.
2. **Qual Copa teve a maior proporção de zebras?** Para cada edição, calculamos `100 × zebras / total de partidas`. O denominador inclui empates e confrontos com rankings iguais. Todas as edições empatadas na maior proporção são apresentadas como líderes.
3. **Quais seleções tiveram a maior taxa de vitória como azarãs?** Calculamos `100 × vitórias como azarã / jogos como azarã`, reunindo as cinco Copas. Exigimos pelo menos três jogos como azarã. Ordenamos pela taxa decrescente, pelo total de jogos decrescente e pelo nome crescente. A ordenação usa frações exatas antes de arredondar a exibição.

As três perguntas combinam predicados auxiliares, comparação, agregação e ordenação.

## Fonte e campos selecionados

Dataset: [FIFA World Cup 2022, de Brenda89, no Kaggle](https://www.kaggle.com/datasets/brenda89/fifa-world-cup-2022). A licença informada pelo catálogo na consulta de 13/11/2026 é **CC0: Public Domain**. O nome do dataset se refere a 2022, mas a cópia utilizada termina em 14/06/2022, antes daquela Copa.

Utilizamos uma [cópia pública do CSV com commit fixo](https://github.com/andyweaves/worldcup22/blob/6e8780b23a6453a9a18c60304b681aeec5b48da0/resources/international_matches.csv). Ela contém 23.921 partidas internacionais. Não se presume que seus bytes sejam iguais aos da versão mais recente do Kaggle. A procedência, o hash e os metadados estão em [data/fonte.json](data/fonte.json).

Há **uma única tabela-fonte**, `international_matches.csv`. Dos campos originais, selecionamos estes dez, mesclando informações qualitativas e quantitativas:

| Campo original | Uso |
| --- | --- |
| `date` | Data da partida e edição da Copa |
| `home_team` | Seleção A no registro |
| `away_team` | Seleção B no registro |
| `home_team_fifa_rank` | Ranking registrado de A |
| `away_team_fifa_rank` | Ranking registrado de B |
| `home_team_score` | Gols de A |
| `away_team_score` | Gols de B |
| `tournament` | Filtro de Copa do Mundo |
| `shoot_out` | Indicação de disputa de pênaltis |
| `home_team_result` | Vitória, derrota ou empate de A |

Os rótulos home/away indicam a ordem no registro, não uma vantagem de mando. As tabelas de rastreabilidade e os fatos de ranking são derivados do mesmo CSV.

## Como executar no computador

Requisitos: **Python 3.10 ou superior** e **SWI-Prolog**. O Python usa somente a biblioteca padrão; não é necessário instalar pacotes com pip. O SWI-Prolog pode ser obtido no [site oficial](https://www.swi-prolog.org/download/stable). Após instalá-lo, abra novamente o terminal e confira `swipl --version`.

Na pasta do repositório:

```powershell
python baixar_dados.py
python etl.py
swipl -q -s consultas.pl
```

O CSV original já está incluído. O primeiro comando verifica seu hash e só faz o download quando ele está ausente. Um arquivo existente com conteúdo diferente não é substituído. O ETL também rejeita versões com hash diferente, para garantir a reprodução do recorte estudado.

No terminal interativo do Prolog, execute uma consulta por vez:

```prolog
?- pergunta_1(Lista).
?- pergunta_2(Tabela, Lideres).
?- pergunta_3(Lista).
?- mostrar_resultados.
?- halt.
```

O texto `?-` representa o prompt do Prolog; digite somente o que vem depois dele. Todas as consultas terminam com ponto.

Para imprimir todas as respostas ou salvar o relatório sem abrir o modo interativo:

```powershell
swipl -q -s consultas.pl -g mostrar_resultados -t halt
swipl -q -s consultas.pl -g exportar_resultados -t halt
```

O segundo comando gera [docs/resultados.md](docs/resultados.md), inteiramente a partir das consultas em Prolog. Não edite manualmente os arquivos gerados.

## Como executar no navegador

O arquivo [projeto_swish.pl](projeto_swish.pl) reúne os mesmos fatos, regras, consultas e impressão de resultados em um único programa, sem operações de disco. Ele também é gerado pelo ETL.

1. Abra o [SWISH](https://swish.swi-prolog.org/) e crie um programa Prolog.
2. Cole o conteúdo completo de `projeto_swish.pl` na área **Program**.
3. Na área **Query**, digite `pergunta_1(Lista).`, `pergunta_2(Tabela,Lideres).` ou `pergunta_3(Lista).` e execute. Nessa área, não inclua `?-`.
4. Use `mostrar_resultados.` para imprimir as três tabelas.

O arquivo único não inclui a exportação de relatórios para o disco. Não carregue esse arquivo junto com os arquivos separados, pois isso duplicaria os fatos.

## Modelagem e transformações

Uma partida é representada por um fato com dez argumentos:

```prolog
jogo(Data, A, B, RankAOriginal, RankBOriginal,
     GolsA, GolsB, Torneio, Penaltis, ResultadoA).

jogo(data(2002,5,31),franca,senegal,1,42,0,1,fifa_world_cup,nao,derrota).
ranking_pre_copa(2002,senegal,42).
```

O ETL filtra `tournament = FIFA World Cup` nos cinco anos, verifica tipos, datas, campos vazios, duplicatas, placares e coerência dos resultados. Exige 64 jogos e 32 seleções em cada edição. Os nomes são convertidos para átomos sem espaços ou acentos; datas usam `data(Ano,Mes,Dia)`.

O nome `Serbia` de 2006 vira `servia_e_montenegro`; nas edições posteriores, vira `servia`. As duas equipes não são agregadas automaticamente. Os nomes originais e as linhas do CSV permanecem em [docs/rastreabilidade.csv](docs/rastreabilidade.csv).

O ranking de estreia é obtido por ordem cronológica. Os valores originais de cada partida continuam em `jogo/10`, enquanto as regras de favoritismo usam `ranking_pre_copa/3`. A data e a linha de origem de cada referência ficam em `referencia_ranking/4` e em [docs/referencias_ranking.csv](docs/referencias_ranking.csv).

## Como as regras respondem às perguntas

`vencedor/5` interpreta o resultado informado pela fonte, incluindo decisões por pênaltis. `azarao/6` compara as duas referências fixas e `zebra/8` exige que a azarã seja a vencedora.

`top_zebras/2` coleta as zebras com `findall/3`, constrói as chaves de ordenação e usa `keysort/2`. Esse predicado preserva partidas diferentes com a mesma diferença de posições.

`resumo_copas/1` enumera cada edição uma vez, conta partidas e zebras e ordena as proporções. `copas_mais_imprevisiveis/1` mantém todas as líderes empatadas. `desempenho_azaroes/2` agrupa por seleção, conta oportunidades e vitórias, aplica o mínimo de jogos e ordena os resultados. As chaves dos grupos são definidas antes de `findall/3`, evitando somas globais ou respostas repetidas.

## Resultados executados

Com a política de ranking acima, a maior zebra é **África do Sul sobre a França em 2010**, com diferença de 74 posições. **2006 e 2018** empatam na maior proporção: 21 zebras em 64 jogos, ou 32,8125%. A **França** lidera a taxa de vitória como azarã entre as seleções elegíveis: seis vitórias em sete jogos, cerca de 85,71%.

As tabelas completas estão em [docs/resultados.md](docs/resultados.md). Esses resultados foram produzidos pela execução do programa Prolog e dependem dos valores do CSV. A análise não estima probabilidades nem demonstra relações causais.

## Testes e reprodução

```powershell
python -m unittest discover -s tests -v
swipl -q -s tests/test_regras.pl -g run_tests -t halt
```

Os testes verificam o recorte, a rastreabilidade, a reprodução byte a byte dos arquivos gerados, entradas inválidas, duplicatas, a referência fixa, pênaltis, empates, igualdade de ranking, ausência de dupla contagem, elegibilidade, desempates e divisão por zero. Os cenários fictícios de teste não entram nos resultados entregues.

Ambiente de validação: Python 3.13.6 e SWI-Prolog 10.1.20, este executado pelo pacote oficial `swipl-wasm` 8.3.0 em um ambiente temporário. A versão WebAssembly foi usada para a verificação porque não havia um SWI-Prolog nativo instalado no computador. O programa entregue permanece em Python e Prolog; Node.js não é dependência do projeto.

## Organização

| Arquivo | Conteúdo |
| --- | --- |
| `data/international_matches.csv` | Tabela original preservada |
| `data/fonte.json` | Origem, licença informada, versão e hash |
| `baixar_dados.py` | Download da versão fixa e verificação de integridade |
| `etl.py` | Seleção, validação e geração dos fatos e consultas |
| `base.pl` | 320 fatos de partidas e 160 referências fixas, gerados |
| `regras.pl` | Inferências e agregações das três perguntas |
| `consultas.pl` | Três perguntas identificadas, geradas pelo ETL |
| `relatorio.pl` | Impressão e exportação dos resultados em Prolog |
| `projeto_swish.pl` | Programa único para o navegador, gerado |
| `docs/validacao.md` | Metodologia, divergências e limitações |
| `docs/validacao_automatica.json` | Checagens estruturais e alterações de ranking no CSV |
| `docs/resultados.md` | Respostas geradas pelo Prolog |
| `tests/` | Testes do ETL e das regras |

## Entrega

O repositório reúne o ETL, o dataset, os fatos, as três perguntas e as instruções de execução. Antes de entregar, reproduza os comandos, compreenda as regras e explique a limitação dos rankings. O PDF de referência é de 2026/1; o prazo aplicável à turma atual precisa ser confirmado. A entrega indicada no enunciado é o endereço do repositório GitHub no Blackboard.
