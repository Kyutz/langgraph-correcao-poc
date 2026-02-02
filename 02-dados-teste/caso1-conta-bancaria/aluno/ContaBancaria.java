public class ContaBancaria {
    public double saldo; 
    
    public void depositar(double valor) {
        saldo = valor; 
    }
    
    public void sacar(double valor) {
        saldo -= valor; 
    }
    
    public double getSaldo() {
        return saldo;
    }
}