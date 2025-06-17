# CineDive 

Uma exploração interativa e visual do universo dos filmes indicados ao Oscar.

![CineDive Banner](banner.png) <!-- Coloque um banner ilustrativo aqui se desejar -->

## Sobre o Projeto

O **CineDive** é uma plataforma de visualização de dados voltada para revelar padrões, conexões e trajetórias no cinema premiado pela Academia (Oscar). A aplicação permite tanto análises globais (big picture) quanto explorações detalhadas de filmes, pessoas e colaborações.  
O usuário pode navegar pelas redes de filmes e profissionais, explorar mapas mundiais de indicações, analisar tendências históricas em heatmaps e comparar atributos em gráficos radiais.

## Funcionalidades

- **Mapa Mundial Interativo:** Descubra a distribuição geográfica dos filmes indicados/vencedores ao Oscar ao longo das décadas.
- **Grafo Filme-Pessoa Bipartido:** Visualize relações diretas entre filmes e seus profissionais (atores, diretores, roteiristas), com filtros dinâmicos.
- **Heatmap de Indicações vs. Vitórias:** Analise padrões de sucesso ao Oscar para diferentes combinações de indicações e prêmios.
- **Gráfico Radial Multivariado:** Compare atributos como nota média, votos, ano e duração de filmes de forma intuitiva.
- **Exploração “One vs All”:** Selecione um filme ou pessoa e veja como ele(a) se conecta e se destaca no universo total.
- **Filtros Avançados:** Filtre por ano, país, gênero, número de indicações/prêmios, nota, votos, etc.

## Tecnologias Utilizadas

- [Svelte](https://svelte.dev/) — Framework de desenvolvimento web reativo.
- [D3.js](https://d3js.org/) — Biblioteca para visualização de dados interativos e customizados.
- ETL em Python (pandas, scripts customizados) para processamento dos dados brutos.
- Visualizações otimizadas para desktop (melhor experiência em tela cheia).

## Dados

- IMDb (arquivos públicos: title.basics, title.principals, name.basics, etc.)
- Base oficial do Oscar (Academy Awards)
- Dados complementares via web scraping (Wikipedia, portais de cinema)

O pipeline de dados é expansível: para atualizar com novos filmes ou premiações, basta atualizar as tabelas básicas e rodar o script de processamento.

## Como Executar Localmente

1. **Clone o repositório:**
    ```bash
    git clone https://github.com/seu-usuario/cinedive.git
    cd cinedive
    ```
2. **Instale as dependências:**
    ```bash
    npm install
    ```
3. **Execute o projeto:**
    ```bash
    npm run dev
    ```
4. Acesse [http://localhost:5173](http://localhost:5173) no navegador.

> **Nota:** Para modificar ou atualizar os dados, confira a pasta `/data` e os scripts ETL (`/scripts`).

## Estrutura do Projeto


# see the ![report](https://github.com/FGV-VIS-2025/final-project-cinedive/blob/main/vis_project.pdf)

