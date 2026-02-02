Implemente a evolução da classe Java 'Nave' seguindo os requisitos divididos por etapas:

Exercício 2.5 - Identificação da Nave:

1. Adicione um atributo 'nome' do tipo String.

2. Inicialize este atributo com um valor de sua preferência no código.

3. Altere o método 'getTextoExibicao()' para que ele retorne o valor do atributo 'nome'.

Exercício 2.6 - Campo Magnético de Proteção:

1. Adicione um atributo 'nivelDeProtecao' do tipo int.

2. A nave deve iniciar sempre com 100 pontos de proteção.

3. Implemente a lógica para que, ao receber um tiro, a nave perca 20 pontos de proteção.

4. A nave só deve morrer (ser destruída) se tomar um tiro e o seu campo de proteção estiver abaixo de 20.

5. Garanta que ao reiniciar o jogo, o nível de proteção volte para 100.

Exercício 2.7 - Feedback Visual:

1. Atualize o método 'getTextoExibicao()' para que ele exiba o nome da nave e o nível de proteção atual de forma concatenada (Exemplo: "Nave Alpha - Proteção: 80").