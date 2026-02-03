import java.awt.*;

/**
 * Um triângulo que pode ser manipulado e se desenha na tela
 * 
 * Traduzido por Júlio César Alves - 2015-09-15
 * Atualizado por Júlio César Alves - 2016-04-07
 * 
 * @author  Michael Kölling and David J. Barnes
 * @version 2011.07.31
 */

public class Triangulo
{
    private int altura;
    private int largura;
    private int posX;
    private int posY;
    private String cor;
    private boolean estaVisivel;

    /**
     * Cria um novo triângulo na posição padrão e com uma cor padrão
     */
    public Triangulo()
    {
        altura = 60;
        largura = 70;
        posX = 210;
        posY = 140;
        cor = "verde";
        estaVisivel = false;
    }

    /**
     * Deixa o triângulo visível. Se já estiver visível não faz nada
     */
    public void exibir()
    {
        estaVisivel = true;
        desenhar();
    }
    
    /**
     * Deixa o triângulo invisível. Se já estiver invisível não faz nada
     */
    public void esconder()
    {
        apagar();
        estaVisivel = false;
    }
    
    /**
     * Diz se o triângulo está desenhado na tela ou não
     */
    public boolean estaDesenhado()
    {
        return estaVisivel;
    }
    
    /**
     * Move o triângulo alguns pixels para a direita
     */
    public void moverDireita()
    {
        moverHorizontal(20);
    }

    /**
     * Move o triângulo alguns pixels para a esquerda
     */
    public void moverEsquerda()
    {
        moverHorizontal(-20);
    }

    /**
     * Move o triângulo alguns pixels para cima
     */
    public void moverCima()
    {
        moverVertical(-20);
    }

    /**
     * Move o triângulo alguns pixels para baixo
     */
    public void moverBaixo()
    {
        moverVertical(20);
    }

    /**
     * Move o triângulo na horizontal pela distância (número de pixels) passada
     */
    public void moverHorizontal(int distancia)
    {
        apagar();
        posX += distancia;
        desenhar();
    }

    /**
     * Move o triângulo na vertical pela distância (número de pixels) passada
     */
    public void moverVertical(int distancia)
    {
        apagar();
        posY += distancia;
        desenhar();
    }

    /**
     * Move o triângulo lentamente na horizontal pela distância (número de pixels) passada
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
     * Move o triângulo lentamente na vertical pela distância (número de pixels) passada
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
     * Muda o tamanho do triângulo para as novas altura e largura (em pixels). Deve ser maior que zero.
     */
    public void mudarTamanho(int novaAltura, int novaLargura)
    {
        apagar();
        altura = novaAltura;
        largura = novaLargura;
        desenhar();
    }

    /**
     * Muda a cor do triângulo.
     * Cores válidas: "vermelha", "amarela", "azul", "verde", "magenta" e "preta"
     */
    public void mudarCor(String novaCor)
    {
        cor = novaCor;
        desenhar();
    }

    /**
     * Desenha o triângulo com as características atuais na tela
     */
    private void desenhar()
    {
        if(estaVisivel) 
        {
            Tela tela = Tela.getTela();
            
            int[] pontosX = { posX, posX + (largura/2), posX - (largura/2) };
            int[] pontosY = { posY, posY + altura, posY + altura };
            tela.desenhar(this, cor, new Polygon(pontosX, pontosY, 3));
            
            tela.esperar(10);
        }
    }

    /**
     * Apaga o triângulo da tela
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
