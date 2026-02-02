
/**
 * Classe criada para facilitar a execucao do Jogo
 * 
 * @author (seu nome) 
 * @version (número de versão ou data)
 */
public class TesteJogo
{    
    private Cenario cenario;
    
    public TesteJogo()
    {
        Nave nave = new Nave();
        Inimigo inimigo = new Inimigo();
        Placar placar = new Placar();                
        cenario = new Cenario(nave, inimigo, placar);
        
        cenario.executarLoopDeJogo();
    }
}
