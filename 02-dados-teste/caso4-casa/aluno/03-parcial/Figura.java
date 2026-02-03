/**
 * Esta classe representa uma figura simples. Você pode desenhar a figura
 * usando o método desenhar. Mas, como é uma figura eletrônica, ela pode
 * ser alterada. Você pode deixá-la em preto e branco ou colorida
 * (somente depois de desenhada, é claro).
 *
 * Esta classe foi criada como um exemplo de aulas em Java usando BlueJ.
 * 
 * Traduzido por Julio César Alves - 2023-08-25
 * 
 * @author  Michael Kölling and David J. Barnes
 * @version 2016.02.29
 */
public class Figura
{
    private Quadrado parede;
    private Quadrado janela;
    private Triangulo telhado;
    private Circulo sol;
    private Circulo sol2; // Adiciona sol2, mas não move
    private Pessoa morador; // Adiciona morador, mas não caminha
    private boolean desenhado;

    public Figura()
    {
        parede = new Quadrado();
        janela = new Quadrado();
        telhado = new Triangulo();  
        sol = new Circulo();
        sol2 = new Circulo();
        morador = new Pessoa();
        desenhado = false;
    }

    public void desenhar()
    {
        if(!desenhado) {
            parede.moverHorizontal(-140);
            parede.moverVertical(20);
            parede.mudarTamanho(120);
            parede.exibir();
            
            janela.mudarCor("preta");
            janela.moverHorizontal(-120);
            janela.moverVertical(40);
            janela.mudarTamanho(40);
            janela.exibir();
    
            telhado.mudarTamanho(60, 180);
            telhado.moverHorizontal(20);
            telhado.moverVertical(-60);
            telhado.exibir();
    
            sol.mudarCor("amarela");
            sol.moverHorizontal(100);
            sol.moverVertical(-40);
            sol.mudarTamanho(80);
            sol.exibir();

            sol2.mudarCor("amarela");
            sol2.moverHorizontal(180);
            sol2.moverVertical(-40);
            sol2.mudarTamanho(60);
            sol2.exibir();

            morador.moverHorizontal(220);
            morador.moverVertical(60);
            morador.exibir();

            desenhado = true;
        }
    }

    public void definirPretoEBranco()
    {
        parede.mudarCor("preta");
        janela.mudarCor("branca");
        telhado.mudarCor("preta");
        sol.mudarCor("preta");
        sol2.mudarCor("preta");
        morador.mudarCor("preto");
    }

    public void definirColorida()
    {
        parede.mudarCor("vermelha");
        janela.mudarCor("preta");
        telhado.mudarCor("verde");
        sol.mudarCor("amarela");
        sol2.mudarCor("amarela");
        morador.mudarCor("preto");
    }
}
