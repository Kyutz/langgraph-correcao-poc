public class ClassePrincipal {
    public static void main(String[] args) {
        int a = 10;
        int b = 5;

        int resultadoSoma = ClasseAuxiliar.somar(a, b);
        int resultadoSubtracao = ClasseAuxiliar.subtrair(a, b);

        System.out.println("Resultado da Soma: " + resultadoSoma);
        System.out.println("Resultado da Subtração: " + resultadoSubtracao);
    }
}
