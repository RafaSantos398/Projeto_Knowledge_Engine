% Todas as inferências e respostas às perguntas são feitas neste arquivo.
:- encoding(utf8).
:- use_module(library(lists)).
:- use_module(library(pairs)).
:- use_module(library(error)).
:- dynamic jogo/10, ranking_pre_copa/3, referencia_ranking/4.
:- ensure_loaded('base.pl').

% As chaves de agrupamento são enumeradas sem duplicatas antes de findall/3.
copa(Edicao) :-
    findall(E, jogo(data(E,_,_),_,_,_,_,_,_,_,_,_), Repetidas),
    sort(Repetidas, Edicoes),
    member(Edicao, Edicoes).

selecao(Selecao) :-
    findall(S, ranking_pre_copa(_,S,_), Repetidas),
    sort(Repetidas, Selecoes),
    member(Selecao, Selecoes).

% Os gols podem estar empatados mesmo quando houve vencedor nos pênaltis.
ganhador_resultado(A, B, vitoria, A, B).
ganhador_resultado(A, B, derrota, B, A).

vencedor(Edicao, Data, Vencedora, Perdedora, Penaltis) :-
    jogo(Data,A,B,_,_,_,_,fifa_world_cup,Penaltis,ResultadoA),
    Data = data(Edicao,_,_),
    ganhador_resultado(A,B,ResultadoA,Vencedora,Perdedora).

% Posições iguais falham nas duas cláusulas: não há favorita ou azarã.
comparar_ranking(A,B,RankA,RankB,A,B,RankA,RankB) :- RankA > RankB.
comparar_ranking(A,B,RankA,RankB,B,A,RankB,RankA) :- RankB > RankA.

azarao(Edicao, Data, Azara, Favorita, RankAzara, RankFavorita) :-
    jogo(Data,A,B,_,_,_,_,fifa_world_cup,_,_),
    Data = data(Edicao,_,_),
    ranking_pre_copa(Edicao,A,RankA),
    ranking_pre_copa(Edicao,B,RankB),
    comparar_ranking(A,B,RankA,RankB,Azara,Favorita,RankAzara,RankFavorita).

favorito(Edicao, Data, Favorita, Azara, RankFavorita, RankAzara) :-
    azarao(Edicao,Data,Azara,Favorita,RankAzara,RankFavorita).

zebra(Edicao, Data, Vencedora, Perdedora, RankV, RankP, Diferenca, Penaltis) :-
    azarao(Edicao,Data,Vencedora,Perdedora,RankV,RankP),
    vencedor(Edicao,Data,Vencedora,Perdedora,Penaltis),
    Diferenca is RankV - RankP.

% P1: chave negativa inverte só a diferença; data e nomes continuam crescentes.
% keysort/2 preserva partidas distintas com a mesma diferença de ranking.
top_zebras(Limite, Lista) :-
    must_be(nonneg, Limite),
    findall(chave(Negativa,Data,V,P)-zebra(E,Data,V,P,RV,RP,D,Pen),
            (zebra(E,Data,V,P,RV,RP,D,Pen), Negativa is -D), Pares),
    keysort(Pares, Ordenados),
    pairs_values(Ordenados, Todas),
    primeiros(Limite, Todas, Lista).

top_zebras(Lista) :- top_zebras(10, Lista).

primeiros(0, _, []) :- !.
primeiros(_, [], []) :- !.
primeiros(N, [X|Xs], [X|Ys]) :-
    N > 0,
    Restantes is N - 1,
    primeiros(Restantes, Xs, Ys).

% P2: o total inclui empates e confrontos de ranking igual.
resumo_copa(Edicao, Zebras, Total, Porcentagem) :-
    copa(Edicao),
    findall(1, jogo(data(Edicao,_,_),_,_,_,_,_,_,fifa_world_cup,_,_), Jogos),
    length(Jogos, Total),
    Total > 0,
    findall(1, zebra(Edicao,_,_,_,_,_,_,_), Surpresas),
    length(Surpresas, Zebras),
    Porcentagem is 100 * Zebras / Total.

resumo_copas(Lista) :-
    findall(chave(Negativa,E)-copa(E,Z,T,P),
            (resumo_copa(E,Z,T,P), Negativa is -(Z rdiv T)), Pares),
    keysort(Pares, Ordenados),
    pairs_values(Ordenados, Lista).

% A igualdade é testada por multiplicação cruzada, sem arredondar percentuais.
copas_mais_imprevisiveis(Lideres) :-
    resumo_copas(Tabela),
    lideres_da_tabela(Tabela, Lideres).

lideres_da_tabela([], []).
lideres_da_tabela([copa(E,Z,T,P)|Restantes], [copa(E,Z,T,P)|Empatadas]) :-
    mesma_proporcao(Restantes, Z, T, Empatadas).

mesma_proporcao([], _, _, []).
mesma_proporcao([copa(E,Z,T,P)|Resto], Z0, T0, Resultado) :-
    ( Z*T0 =:= Z0*T ->
        Resultado = [copa(E,Z,T,P)|Outras],
        mesma_proporcao(Resto,Z0,T0,Outras)
    ; Resultado = []
    ).

% P3: empates e derrotas como azarã entram no denominador.
desempenho_azarao(Selecao, Vitorias, Jogos, Taxa) :-
    selecao(Selecao),
    findall(1, azarao(_,_,Selecao,_,_,_), Oportunidades),
    length(Oportunidades, Jogos),
    Jogos > 0,
    findall(1, zebra(_,_,Selecao,_,_,_,_,_), Sucessos),
    length(Sucessos, Vitorias),
    Taxa is 100 * Vitorias / Jogos.

desempenho_azaroes(Minimo, Lista) :-
    must_be(positive_integer, Minimo),
    findall(chave(NegTaxa,NegJogos,S)-desempenho(S,V,J,T),
            (desempenho_azarao(S,V,J,T), J >= Minimo,
             NegTaxa is -(V rdiv J), NegJogos is -J), Pares),
    keysort(Pares, Ordenados),
    pairs_values(Ordenados, Lista).

desempenho_azaroes(Lista) :- desempenho_azaroes(3, Lista).
