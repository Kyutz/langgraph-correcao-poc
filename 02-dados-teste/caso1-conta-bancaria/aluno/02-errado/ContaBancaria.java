public class ContaBancaria {
    public double saldo; // Não encapsulado
    
    public void depositar(double valor) {
        saldo = valor; // Não soma, apenas define
    }
    
    public void sacar(double valor) {
        saldo -= valor; // Não verifica saldo
    }
    
    public double getSaldo() {
        return saldo;
    }
}
