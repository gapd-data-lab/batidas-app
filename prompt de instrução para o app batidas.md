# Prompt de Instrução Completo para Desenvolvimento do Programa de Análise de Dados em Streamlit

## Objetivo
Este prompt instrui sobre o processo de elaboração do programa de análise de dados em Streamlit, que visa gerar gráficos (boxplot e histograma) para dados de batidas de lotes de confinamento. Deve-se compreender a estrutura do programa, seus parâmetros necessários e a lógica de funcionamento, garantindo que todas as escolhas do usuário sejam respeitadas durante a análise e exibição dos resultados.

## Estrutura do Programa
O programa é desenvolvido em Python utilizando o framework Streamlit para criar uma interface gráfica intuitiva e interativa para o usuário. O objetivo é realizar análises estatísticas sobre um arquivo Excel (.xlsx) contendo dados de batidas de rações de lotes de confinamento, gerando boxplots e histogramas a partir das diferenças percentuais encontradas nas misturas de ração.

O código é dividido em três partes principais:
1. **Upload e Configurações do Arquivo**: Área onde o usuário faz o upload do arquivo Excel, define parâmetros de seleção, como operadores e tipos de alimentos, e seleciona o tipo de gráfico.
2. **Processamento dos Dados**: Parte que trata o arquivo, faz a limpeza dos dados, lida com outliers e calcula as estatísticas necessárias para a análise.
3. **Visualização dos Resultados**: Gera o gráfico (boxplot ou histograma) e uma tabela com as estatísticas dos dados, considerando as escolhas do usuário, exibindo o gráfico e a tabela na ordem correta.

## Passos e Orientações

### 1. Configuração do Arquivo e Interface do Usuário
- Utilize a biblioteca `Streamlit` para configurar a página inicial e o layout da aplicação.
- Utilize duas colunas, uma para o upload do arquivo e seleção dos parâmetros (`col1`) e outra para exibição dos resultados (`col2`).
- **Upload do Arquivo**: Utilize `st.file_uploader()` para permitir o upload do arquivo Excel.
- **Seleção de Parâmetros**: Utilize `st.multiselect()` para selecionar um ou mais operadores e tipos de alimentos.
  - Ordene os operadores e alimentos em ordem alfabética, com a opção "Todos" sempre no início.
  - Permita ao usuário escolher o tipo de gráfico (`Boxplot` ou `Histograma`).
- **Botão Gerar**: Crie um botão "Gerar" que, quando pressionado, inicia o processamento dos dados e a geração dos gráficos.

### 2. Processamento e Limpeza dos Dados
- **Leitura do Arquivo**:
  - Leia o arquivo Excel com a função `pd.read_excel()`, ignorando as duas primeiras linhas e removendo a primeira coluna que está vazia.
- **Tratamento dos Dados**:
  - Converta a coluna "DIFERENÇA (%)" para numérica usando `pd.to_numeric()` e remova valores ausentes.
  - Calcule outliers utilizando o método do Intervalo Interquartil (IQR) e remova-os para os cálculos sem outliers.
  - Garanta que todas as operações de filtragem e cálculo levem em conta as escolhas do usuário, como operadores e alimentos.
- **Filtragem dos Dados com Outliers**:
  - Filtre os dados sem outliers considerando apenas as escolhas do usuário para os operadores e alimentos selecionados.

### 3. Cálculo das Estatísticas
- **Cálculo de Média e Mediana**:
  - Calcule a média e a mediana dos dados com e sem outliers para a coluna "DIFERENÇA (%)", levando em conta apenas os dados selecionados pelo usuário.
- **Contagem de Outliers**:
  - Calcule quantos outliers foram removidos ao comparar o número total de pontos antes e depois da remoção dos outliers.
- **Contagem de Lotes com Diferenças Toleradas**:
  - Conte a quantidade de lotes cujas diferenças ultrapassam os níveis de tolerância (± 3%) em faixas de 2%, para fornecer mais informações sobre o desvio em relação à meta.

### 4. Visualização dos Resultados
- **Criação dos Gráficos**:
  - Crie um gráfico de acordo com o tipo selecionado pelo usuário:
    - **Boxplot**: Utilize `ax.boxplot()` com as configurações para exibir a média e a mediana.
    - **Histograma**: 
      - Utilize `ax.bar()` para plotar um histograma em escala de cinza.
      - Implemente uma escala de cinza nos bins, onde a intensidade reflete a distância do zero.
      - Coloração dos rótulos do eixo X:
        - Vermelho para valores ≤ -4
        - Verde para valores entre -3 e 3 (inclusive)
        - Azul para valores ≥ 4
      - Destaque o eixo central (0):
        - Rótulo em verde escuro, negrito e ligeiramente maior
        - Adicione uma linha vertical tracejada verde escura marcando a posição do zero
  - Para o eixo X do histograma, utilize cores para diferenciar as faixas de diferenças.
- **Renderização no Streamlit**:
  - Utilize `st.pyplot(fig)` para renderizar o gráfico no Streamlit, garantindo que ele seja exibido antes da tabela de estatísticas.
- **Tabela de Estatísticas**:
  - Crie uma tabela com as estatísticas calculadas, incluindo a média, mediana, contagem de outliers e contagem de lotes em diferentes faixas de diferença.
  - Adicione uma coluna com percentuais relativos e uma linha indicando o total de pontos.
  - A tabela deve ser exibida logo abaixo do gráfico para manter a organização visual.
- **Legenda dos Gráficos**:
  - Inclua uma legenda clara no gráfico, exibindo a média, mediana e a contagem de outliers.

### 5. Download do Gráfico
- Ofereça ao usuário a possibilidade de baixar o gráfico gerado em formato PNG.
- Utilize `st.download_button()` para fornecer o botão de download, garantindo que o gráfico esteja em um buffer de memória (BytesIO) antes de ser baixado.

## Parâmetros e Considerações Gerais
- **Bibliotecas Utilizadas**:
  - `streamlit`, `pandas`, `numpy`, `matplotlib.pyplot`, `matplotlib.colors`, `io`
- **Configuração da Página**:
  - Defina o layout da página como "wide" para melhorar a visualização dos gráficos e tabelas.
- **Tratamento de Erros**:
  - Caso a coluna "DIFERENÇA (%)" não seja encontrada, mostre uma mensagem de erro clara usando `st.error()`.
  - Certifique-se de tratar valores ausentes e conversões de tipos para evitar falhas durante o processamento dos dados.

## Estrutura de Funções
O código deve ser organizado em funções modulares para melhor legibilidade e manutenção:
- `load_and_process_data()`: Para carregar e processar os dados iniciais
- `filter_data()`: Para filtrar os dados com base nas seleções do usuário
- `calculate_statistics()`: Para calcular as estatísticas necessárias
- `create_graph()`: Para criar o gráfico (boxplot ou histograma)
- `main()`: Função principal que organiza o fluxo do programa

## Resumo
Este prompt fornece todas as orientações necessárias para que outra LLM compreenda e reproduza o programa de análise de dados, respeitando a seleção dos usuários, gerando visualizações consistentes e realizando cálculos precisos com e sem outliers. Cada etapa do desenvolvimento foi explicada de forma detalhada para garantir que o código seja replicável e ajustável conforme as necessidades de diferentes usuários.