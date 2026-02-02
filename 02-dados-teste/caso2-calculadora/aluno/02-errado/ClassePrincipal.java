public class ClassePrincipal {
    public static void main(String[] args) {
        int a = 10;
        int b = 5;

        ClasseAuxiliar aux = new ClasseAuxiliar();
        // Soma errada
        int resultadoSoma = aux.somar(a, b);
        int resultadoSubtracao = aux.subtrair(a, b);

        System.out.println("Resultado da Soma: " + resultadoSoma);
        System.out.println("Resultado da Subtração: " + resultadoSubtracao);
    }
}

class ClasseAuxiliar {
    public int somar(int x, int y) {
        return x - y; // Erro proposital
    }

    public int subtrair(int x, int y) {
        return x + y; // Erro proposital
    }
}
