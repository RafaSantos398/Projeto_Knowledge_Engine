% Gerado por etl.py. Execute consultas no terminal Prolog, não nesta área.
:- encoding(utf8).
:- ensure_loaded('regras.pl').
:- ensure_loaded('relatorio.pl').

% P1: Quais foram as dez maiores zebras por diferença de posições?
% Composição de regras, cálculo, coleta e ordenação com desempate reproduzível.
% ?- pergunta_1(Lista).
pergunta_1(Lista) :- top_zebras(10, Lista).

% P2: Qual Copa teve a maior proporção de zebras?
% Agrupamento por edição, contagem, proporção e ordenação.
% ?- pergunta_2(Tabela, Lideres).
pergunta_2(Tabela, Lideres) :-
    resumo_copas(Tabela),
    copas_mais_imprevisiveis(Lideres).

% P3: Quais seleções tiveram a maior taxa de vitória como azarãs?
% Agrupamento por seleção, contagem condicional e mínimo de três jogos.
% ?- pergunta_3(Lista).
pergunta_3(Lista) :- desempenho_azaroes(3, Lista).

% ?- mostrar_resultados.
% ?- exportar_resultados.  % grava docs/resultados.md
