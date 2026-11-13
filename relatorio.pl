% Apresentação das respostas. Nenhum resultado é pré-calculado ou embutido aqui.
:- encoding(utf8).
:- use_module(library(filesex)).

mostrar_resultados :-
    format('# Zebras nas Copas de 2002 a 2018~n~n'),
    format('Resultados calculados em Prolog a partir de 320 partidas do CSV.~n~n'),
    format('A referência é o ranking de estreia no CSV, fixo por seleção e edição. '),
    format('É uma aproximação do ranking pré-Copa, com divergências históricas '),
    format('documentadas em [validação](validacao.md). Os números abaixo são '),
    format('condicionados a essa escolha; não são uma validação dos rankings oficiais.~n~n'),
    mostrar_top_zebras,
    mostrar_resumo_copas,
    mostrar_desempenho.

mostrar_top_zebras :-
    format('## Pergunta 1 As dez maiores zebras~n~n'),
    format('| Posição | Copa | Data | Vencedora | Perdedora | Rank V | Rank P | Diferença | Pênaltis |~n'),
    format('| --- | --- | --- | --- | --- | --- | --- | --- | --- |~n'),
    top_zebras(10, Lista),
    imprimir_zebras(Lista, 1), format('~n').

imprimir_zebras([], _).
imprimir_zebras([zebra(E,D,V,P,RV,RP,Dif,Pen)|Resto], Posicao) :-
    texto_data(D, Texto),
    format('| ~d | ~d | ~w | ~w | ~w | ~d | ~d | ~d | ~w |~n',
           [Posicao,E,Texto,V,P,RV,RP,Dif,Pen]),
    Proxima is Posicao + 1,
    imprimir_zebras(Resto, Proxima).

texto_data(data(A,M,D), Texto) :-
    format(atom(Texto), '~d-~|~`0t~d~2+-~|~`0t~d~2+', [A,M,D]).

mostrar_resumo_copas :-
    format('## Pergunta 2 Proporção de zebras por Copa~n~n'),
    format('| Copa | Zebras | Total de jogos | Proporção |~n'),
    format('| --- | --- | --- | --- |~n'),
    resumo_copas(Tabela),
    forall(member(copa(E,Z,T,P),Tabela),
           format('| ~d | ~d | ~d | ~2f% |~n', [E,Z,T,P])),
    copas_mais_imprevisiveis(Lideres),
    findall(E, member(copa(E,_,_,_),Lideres), Edicoes),
    format('~nEdição ou edições líderes: ~w.~n~n', [Edicoes]).

mostrar_desempenho :-
    format('## Pergunta 3 Taxa de vitória como azarã~n~n'),
    format('Elegibilidade: pelo menos três jogos como azarã nas cinco Copas. '),
    format('Vitórias nos pênaltis contam. A ordem usa frações exatas; '),
    format('apenas a exibição é arredondada para duas casas.~n~n'),
    format('| Seleção | Vitórias como azarã | Jogos como azarã | Taxa |~n'),
    format('| --- | --- | --- | --- |~n'),
    desempenho_azaroes(3, Lista),
    forall(member(desempenho(S,V,J,T),Lista),
           format('| ~w | ~d | ~d | ~2f% |~n', [S,V,J,T])), format('~n'),
    format('Os nomes são os átomos padronizados da base. '),
    format('O arquivo `rastreabilidade.csv` mantém os nomes originais. '),
    format('Diferenças de posições não são probabilidades de vitória.~n').

% O destino padrão é relativo ao próprio projeto, mesmo se o terminal estiver fora dele.
:- dynamic diretorio_relatorio/1.
:- prolog_load_context(directory, Diretorio), assertz(diretorio_relatorio(Diretorio)).

exportar_resultados :-
    diretorio_relatorio(Raiz),
    directory_file_path(Raiz, docs, Docs),
    make_directory_path(Docs),
    directory_file_path(Docs, 'resultados.md', Destino),
    exportar_resultados(Destino).

exportar_resultados(Destino) :-
    setup_call_cleanup(
        open(Destino, write, Arquivo, [encoding(utf8)]),
        with_output_to(Arquivo, mostrar_resultados),
        close(Arquivo)
    ).
