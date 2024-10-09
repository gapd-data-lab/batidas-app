### Objetivo

Este prompt instrui sobre o processo de elaboração do programa de análise de dados em Streamlit, que visa gerar histogramas e tabelas estatísticas a partir de dados de batidas de lotes de confinamento. Deve-se compreender a estrutura do programa, seus parâmetros necessários e a lógica de funcionamento, garantindo que todas as escolhas do usuário sejam respeitadas durante a análise e exibição dos resultados.

### Estrutura do Programa

O programa será desenvolvido em Python utilizando o framework Streamlit para criar uma interface gráfica intuitiva e interativa para o usuário. O objetivo é realizar análises estatísticas sobre um arquivo Excel (.xlsx) contendo dados de batidas de rações de lotes de confinamento, gerando histogramas e uma tabela detalhada com informações estatísticas relevantes das diferenças percentuais encontradas nas misturas de ração.

O código é dividido em quatro partes principais:

1. **Upload e Configurações do Arquivo**: Área onde o usuário faz o upload do arquivo Excel, define parâmetros de seleção, como operadores e tipos de alimentos, e seleciona o tipo de gráfico.
2. **Processamento dos Dados**: Parte que trata o arquivo, faz a limpeza dos dados, lida com outliers e calcula as estatísticas necessárias para a análise.
3. **Visualização dos Resultados**: Gera o gráfico (histograma) e uma tabela detalhada com as estatísticas dos dados, considerando as escolhas do usuário, exibindo-os na ordem correta.
4. **Tabela de Estatísticas**: Exibição de uma tabela clara e organizada, com contagem de batidas, médias e medianas, além de percentuais das diferenças.

### Passos e Orientações

#### 1. Configuração do Arquivo e Interface do Usuário

- Utilize a biblioteca `Streamlit` para configurar a página inicial e o layout da aplicação.
- Utilize duas colunas, uma para o upload do arquivo e seleção dos parâmetros (`col1`) e outra para exibição dos resultados (`col2`).
- **Upload do Arquivo**: Utilize `st.file_uploader()` para permitir o upload do arquivo Excel.
- **Seleção de Parâmetros**: Utilize `st.multiselect()` para selecionar um ou mais operadores, tipos de alimentos e dietas.
  - Ordene os operadores, alimentos e dietas em ordem alfabética, com a opção "Todos" sempre no início.
- **Checkbox de Outliers**: Adicione um checkbox que permite ao usuário escolher se deseja remover os outliers do histograma de médias das diferenças percentuais.
- **Botão Gerar**: Crie um botão "Gerar" que, quando pressionado, inicia o processamento dos dados e a geração dos gráficos.

#### 2. Processamento e Limpeza dos Dados

- **Leitura do Arquivo**:
  - Leia o arquivo Excel com a função `pd.read_excel()`, ignorando as duas primeiras linhas e removendo a primeira coluna que está vazia.
- **Tratamento dos Dados**:
  - Converta a coluna "DIFERENÇA (%)" para numérica usando `pd.to_numeric()` e remova valores ausentes.
  - Calcule outliers utilizando o método do Intervalo Interquartil (IQR) e remova-os para os cálculos sem outliers.
  - Garanta que todas as operações de filtragem e cálculo levem em conta as escolhas do usuário, como operadores, alimentos e dietas.
- **Filtragem dos Dados com Outliers**:
  - Filtre os dados sem outliers considerando apenas as escolhas do usuário para os operadores, alimentos e dietas selecionados.

#### 3. Cálculo das Estatísticas

- **Cálculo de Média e Mediana**:
  - Calcule a média e a mediana dos dados com e sem outliers para a coluna "DIFERENÇA (%)", levando em conta apenas os dados selecionados pelo usuário.
- **Contagem de Batidas em Faixas de Diferença**:
  - Conte a quantidade de batidas cujas diferenças ultrapassam os níveis de tolerância (3%) em faixas de 2%:
    - Entre 3% e 5%
    - Entre 5% e 7%
    - Acima de 7%
  - Calcule também o percentual relativo ao total de batidas para cada uma dessas faixas.

#### 4. Visualização dos Resultados

- **Criação dos Gráficos**:
  - Crie um histograma que mostre a distribuição da média das diferenças percentuais de todas as batidas.
  - Use uma escala de cinza para os bins, que começa branca no ponto central (0) e se torna mais escura conforme se afasta do zero.
  - Inclua uma linha vertical verde destacada exatamente no valor 0 do eixo X.
  - **Título do Gráfico**: Adicione um título mais informativo ao gráfico, como:
    - "Distribuição da Média da Diferença Percentual das Batidas (Sem Outliers) - Confinamento SJudas"
    - ou "Distribuição da Média da Diferença Percentual das Batidas (Com Outliers) - Confinamento SJudas"
  - Personalize os rótulos do eixo X:
    - Números **menores ou iguais a -4%**: Vermelho.
    - Números **maiores ou iguais a +4%**: Azul.
    - Números entre **-3% e +3%** (inclusive): Verde.
    - **Números ímpares**: Maior tamanho de fonte.
    - **Números pares**: Menor tamanho de fonte.
- **Renderização no Streamlit**:
  - Utilize `st.pyplot(fig)` para renderizar o gráfico no Streamlit, garantindo que ele seja exibido antes da tabela de estatísticas.

#### 5. Tabela de Estatísticas

- **Criação da Tabela**:
  - Crie uma tabela para exibir as estatísticas calculadas, incluindo:
    - **Número de Batidas**: Com e sem outliers.
    - **Média (%)** e **Mediana (%)**: Com e sem outliers.
    - **Contagem de Batidas e Percentuais** em diferentes faixas de diferença:
      - Entre 3% e 5%
      - Entre 5% e 7%
      - Acima de 7%
  - Separe claramente as colunas de **Contagem** e **Percentual** para tornar a leitura mais fácil.
- **Estilização da Tabela**:
  - Utilize o método `style` do Pandas para aplicar **alinhamento à direita** em todas as células, facilitando a comparação visual.
  - Ajuste o **tamanho da fonte** e a **largura das colunas** para melhorar a legibilidade.
  - Exiba a tabela com `st.write()` usando `to_html()` para permitir uma apresentação mais customizável.

### Parâmetros e Considerações Gerais

- **Bibliotecas Utilizadas**:
  - `streamlit`, `pandas`, `numpy`, `matplotlib.pyplot`, `matplotlib.colors`.
- **Configuração da Página**:
  - Defina o layout da página como "wide" para melhorar a visualização dos gráficos e tabelas.
- **Tratamento de Erros**:
  - Caso a coluna "DIFERENÇA (%)" não seja encontrada, mostre uma mensagem de erro clara usando `st.error()`.
  - Certifique-se de tratar valores ausentes e conversões de tipos para evitar falhas durante o processamento dos dados.

### Comandos para Commit e Push no GitHub

```bash
git status
git add batidas.py "prompt de instrução para o app batidas.md" "requirements.txt"
git commit -m "Versão atualizada do app batidas - melhorias no gráfico e na tabela de estatísticas"
git push origin main
```

### Comando para ativar o ambiente virtual

```bash
source venv/bin/activate
```