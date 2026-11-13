:- encoding(utf8).
:- ensure_loaded('../consultas.pl').
:- use_module(library(plunit)).

:- begin_tests(regras_basicas).

test(vitoria_da_selecao_a) :-
    ganhador_resultado(a,b,vitoria,a,b).
test(vitoria_da_selecao_b) :-
    ganhador_resultado(a,b,derrota,b,a).
test(empate_nao_tem_vencedor, [fail]) :-
    ganhador_resultado(a,b,empate,_,_).
test(rankings_iguais_nao_tem_azara, [fail]) :-
    comparar_ranking(a,b,5,5,_,_,_,_).
test(posicao_maior_e_azara, true(A == b)) :-
    comparar_ranking(a,b,1,40,A,a,40,1).
test(limite_zero, true(Lista == [])) :- top_zebras(0,Lista).
test(limite_negativo, [error(type_error(nonneg,-1))]) :- top_zebras(-1,_).
test(minimo_zero, [error(type_error(positive_integer,0))]) :- desempenho_azaroes(0,_).
test(lideranca_empatada, true(Lideres == [copa(2002,10,40,25),copa(2006,16,64,25)])) :-
    lideres_da_tabela([copa(2002,10,40,25),copa(2006,16,64,25),copa(2010,10,64,15.625)],Lideres).

:- end_tests(regras_basicas).

:- begin_tests(base_real).

test(copas_sem_duplicatas, true(Edicoes == [2002,2006,2010,2014,2018])) :-
    findall(E,copa(E),Edicoes).
test(jogos_e_selecoes_por_copa) :-
    forall(copa(E), (
        findall(1,jogo(data(E,_,_),_,_,_,_,_,_,_,_,_),Jogos), length(Jogos,64),
        findall(S,ranking_pre_copa(E,S,_),Selecoes), length(Selecoes,32),
        sort(Selecoes,Unicas), length(Unicas,32)
    )).
test(senegal_franca_zebra_sem_penaltis) :-
    zebra(2002,data(2002,5,31),senegal,franca,42,1,41,nao).
test(brasil_alemanha_vitoria_favorita, [fail]) :-
    zebra(2002,data(2002,6,30),_,_,_,_,_,_).
test(brasil_mexico_empate_nao_e_zebra, [fail]) :-
    zebra(2014,data(2014,6,17),_,_,_,_,_,_).
test(russia_espanha_penaltis_com_rankings_fixos, [nondet]) :-
    zebra(2018,data(2018,7,1),russia,espanha,70,10,60,sim).
test(dez_maiores_e_ordenacao, true(N == 10)) :-
    top_zebras(10,Lista), length(Lista,N),
    findall(chave(Neg,D,V,P),
            (member(zebra(_,D,V,P,_,_,Dif,_),Lista),Neg is -Dif), Chaves),
    msort(Chaves,Chaves).
test(nao_duplica_partidas) :-
    findall(chave(E,D,V,P),zebra(E,D,V,P,_,_,_,_),Partidas),
    sort(Partidas,Unicas), length(Partidas,N), length(Unicas,N).
test(denominador_64_inclui_empates) :-
    forall(resumo_copa(_,Z,Total,P), (Total =:= 64, Z =< Total, P =:= 100*Z/Total)).
test(vitorias_limitadas_por_jogos_e_elegibilidade) :-
    desempenho_azaroes(3,Lista),
    forall(member(desempenho(_,V,J,T),Lista), (J >= 3,V =< J,T =:= 100*V/J)).
test(elegibilidade_exclui_dois_jogos) :-
    desempenho_azaroes(3,L3), desempenho_azaroes(1,L1),
    forall(member(desempenho(S,_,J,_),L1), (J < 3 -> \+ member(desempenho(S,_,_,_),L3) ; true)).
test(ordenacao_exata_da_taxa) :-
    desempenho_azaroes(3,Lista),
    findall(chave(Neg,NegJ,S),
            (member(desempenho(S,V,J,_),Lista),Neg is -(V rdiv J),NegJ is -J), Chaves),
    msort(Chaves,Chaves).
test(uma_unica_resposta_por_pergunta) :-
    findall(L,pergunta_1(L),[_]),
    findall(T-L,pergunta_2(T,L),[_]),
    findall(L,pergunta_3(L),[_]).
test(nao_divide_por_zero_para_selecao_inexistente, [fail]) :-
    desempenho_azarao(selecao_inexistente,_,_,_).

:- end_tests(base_real).

% Cenário isolado: o CSV não contém confrontos entre rankings fixos iguais.
% Os fatos artificiais só existem durante o teste e não entram nos resultados.
instalar_empate_de_ranking :-
    assertz(jogo(data(2099,1,1),teste_a,teste_b,5,5,1,0,fifa_world_cup,nao,vitoria)),
    assertz(ranking_pre_copa(2099,teste_a,5)),
    assertz(ranking_pre_copa(2099,teste_b,5)).

remover_empate_de_ranking :-
    retractall(jogo(data(2099,_,_),_,_,_,_,_,_,_,_,_)),
    retractall(ranking_pre_copa(2099,_,_)).

:- begin_tests(cenario_isolado,
               [setup(instalar_empate_de_ranking),cleanup(remover_empate_de_ranking)]).

test(rankings_iguais_nao_produzem_zebra, [fail]) :-
    zebra(2099,_,_,_,_,_,_,_).
test(igualdade_entra_no_total_da_copa) :-
    resumo_copa(2099,0,1,P), P =:= 0.
test(igualdade_fica_fora_dos_jogos_como_azara, [fail]) :-
    desempenho_azarao(teste_a,_,_,_).

:- end_tests(cenario_isolado).
