public class ClasseAuxiliar {
    // ERRO: O método não é estático. A LLM deve identificar a inconsistência com a chamada em ClassePrincipal.
    public int somar(int x, int y) {
        // Erro lógico: está subtraindo em vez de somar!
        return x - y;
    }

    public static int subtrair(int x, int y) {
        return x - y;
    }
}
