public class ClassePrincipal {
    public static void main(String[] args) {
        int a = 10;
        int b = 5;

        ClasseAuxiliar aux = new ClasseAuxiliar();
        int resultadoSoma = aux.somar(a, b);
        // Esqueceu de chamar subtrair
        System.out.println("Resultado da Soma: " + resultadoSoma);
    }
}

class ClasseAuxiliar {
    public int somar(int x, int y) {
        return x + y;
    }

    // Esqueceu de implementar subtrair
}
