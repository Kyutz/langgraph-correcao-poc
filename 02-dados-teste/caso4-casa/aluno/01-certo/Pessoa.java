import java.awt.*;

/**
 * Uma pessoa que pode ser manipulada e se desenha na tela
 * 
 * Traduzido por Júlio César Alves - 2015-09-15
 * Atualizado por Júlio César Alves - 2016-04-0
 * 
 * @author  Michael Kölling and David J. Barnes
 * @version 2011.07.31
 */

public class Pessoa
{
    private int altura;
    private int largura;
    private int posX;
    private int posY;
    private String cor;
    private boolean estaVisivel;

    /**
     * Cria uma nova pessoa na posição padrão e com uma cor padrão
     */
    public Pessoa()
    {
        altura = 60;
        largura = 30;
        posX = 280;
        posY = 190;
        cor = "preto";
        estaVisivel = false;
    }

    /**
     * Deixa a pessoa visível. Se já estiver visível não faz nada
     */
    public void exibir()
    {
        estaVisivel = true;
        desenhar();
    }
    
    /**
     * Deixa a pessoa invisível. Se já estiver invisível não faz nada
     */
    public void esconder()
    {
        apagar();
        estaVisivel = false;
    }
    
    /**
     * Diz se a pessoa está desenhada na tela ou não
     */
    public boolean estaDesenhado()
    {
        return estaVisivel;
    }
    
    /**
     * Move a pessoa alguns pixels para a direita
     */
    public void moverDireita()
    {
        moverHorizontal(20);
    }

    /**
     * Move a pessoa alguns pixels para a esquerda
     */
    public void moverEsquerda()
    {
        moverHorizontal(-20);
    }

    /**
     * Move a pessoa alguns pixels para cima
     */
    public void moverCima()
    {
        moverVertical(-20);
    }

    /**
     * Move a pessoa alguns pixels para baixo
     */
    public void moverBaixo()
    {
        moverVertical(20);
    }

    /**
     * Move a pessoa na horizontal pela distância (número de pixels) passada
     */
    public void moverHorizontal(int distancia)
    {
        apagar();
        posX += distancia;
        desenhar();
    }

    /**
     * Move a pessoa na vertical pela distância (número de pixels) passada
     */
    public void moverVertical(int distancia)
    {
        apagar();
        posY += distancia;
        desenhar();
    }

    /**
     * Move a pessoa lentamente na horizontal pela distância (número de pixels) passada
     */
    public void moverHorizontalLento(int distancia)
    {
        int passo;

        if(distancia < 0) 
        {
            passo = -1;
            distancia = -distancia;
        }
        else 
        {
            passo = 1;
        }

        for(int i = 0; i < distancia; i++)
        {
            posX += passo;
            desenhar();
        }
    }

    /**
     * Move a pessoa lentamente na vertical pela distância (número de pixels) passada
     */
    public void moverVerticalLento(int distancia)
    {
        int passo;

        if(distancia < 0) 
        {
            passo = -1;
            distancia = -distancia;
        }
        else 
        {
            passo = 1;
        }

        for(int i = 0; i < distancia; i++)
        {
            posY += passo;
            desenhar();
        }
    }

    /**
     * Muda o tamanho da pessoa para as novas altura e largura (em pixels). Deve ser maior que zero.
     */
    public void mudarTamanho(int novaAltura, int novaLargura)
    {
        apagar();
        altura = novaAltura;
        largura = novaLargura;
        desenhar();
    }

    /**
     * Muda a cor da pessoa.
     * Cores válidas: "vermelha", "amarela", "azul", "verde", "magenta" e "preta"
     */
    public void mudarCor(String novaCor)
    {
        cor = novaCor;
        desenhar();
    }

    /**
     * Desenha a pessoa com as características atuais na tela
     */
    private void desenhar()
    {
        int ac = (int)(altura * 0.7);  // altura do corpo
        int mc = (altura - ac) / 2;  // altura de metade da cabeça
        int ml = largura / 2;  // metade da largura
        int x = posX;
        int y = posY;
        
        if(estaVisivel) 
        {
            Tela tela = Tela.getTela();
            
            int[] pontosX = { x-3, x-ml, x-ml, x-(int)(ml*0.2)-1, x-(int)(ml*0.2)-1, x-ml, 
                              x-ml+(int)(ml*0.4)+1, x, x+ml-(int)(ml*0.4)-1, x+ml, x+(int)(ml*0.2)+1, 
                              x+(int)(ml*0.2)+1, x+ml, x+ml, x+3, x+(int)(ml*0.6), 
                              x+(int)(ml*0.6), x+3, x-3, x-(int)(ml*0.6), x-(int)(ml*0.6) };
            int[] pontosY = { y, y+(int)(ac*0.2), y+(int)(ac*0.4), y+(int)(ac*0.2), 
                              y+(int)(ac*0.5), y+ac, y+ac, y+(int)(ac*0.65), y+ac, y+ac, 
                              y+(int)(ac*0.5), y+(int)(ac*0.2), y+(int)(ac*0.4), y+(int)(ac*0.2), 
                              y, y-mc+3, y-mc-3, y-mc-mc, y-mc-mc, y-mc-3, y-mc+3 };
                              
            tela.desenhar(this, cor, new Polygon(pontosX, pontosY, 21));
            
            tela.esperar(10);
        }
    }

    /**
     * Apaga a pessoa da tela
     */
    private void apagar()
    {
        if(estaVisivel) 
        {
            Tela tela = Tela.getTela();
            tela.apagar(this);
        }
    }
}
