public class ContaBancaria {
    public double saldo; // ERRO: Atributo público
    
    public void depositar(double valor) {
        saldo = valor; // ERRO: Sobrescreve
    }
    
    public void sacar(double valor) {
        saldo -= valor; // ERRO: Não verifica saldo
    }
    
    public double getSaldo() {
        return saldo;
    }
}