import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.ticker import MaxNLocator, FuncFormatter
import datetime
import io
import base64
import pytz
import yaml

def read_config(config_file="config.yaml"):
    """
    Lê o arquivo de configuração YAML e carrega as configurações para o programa.

    Args:
    config_file (str): Caminho para o arquivo de configuração YAML. Padrão: 'config.yaml'.

    Returns:
    dict: Um dicionário contendo todas as configurações do programa, como colunas do Excel,
    parâmetros de análise, visualização, sliders e exportação.

    Esta função é responsável por carregar o arquivo de configuração YAML. Em caso de falha ao carregar
    ou encontrar o arquivo, ela exibe uma mensagem de erro apropriada. 
    
    O arquivo de configuração define parâmetros cruciais, como colunas de dados, limites para a análise de outliers,
    opções de exportação e ajustes de visualização, que são usados por várias partes do programa.
    """

    try:
        with open(config_file, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"O arquivo de configuração '{config_file}' não foi encontrado.")
    except yaml.YAMLError as e:
        raise ValueError(f"Erro ao ler o arquivo de configuração: {e}")

# Carregar configurações
config = read_config()

def load_and_process_data(uploaded_file):
    """
    Carrega e processa os dados de um arquivo Excel carregado pelo usuário.

    Args:
    uploaded_file: O arquivo Excel (.xlsx) carregado pelo usuário via interface Streamlit.

    Returns:
    DataFrame: Um DataFrame Pandas contendo os dados processados e prontos para análise.

    Processamento:
    1. Carrega o arquivo Excel, pulando o número de linhas configurado.
    2. Remove a primeira coluna, se especificado na configuração.
    3. Remove colunas especificadas no arquivo de configuração.
    4. Verifica se todas as colunas necessárias estão presentes no arquivo.
    5. Converte colunas específicas (como valores numéricos e datas) para os tipos apropriados.

    Exibe uma mensagem de erro se o arquivo não contém as colunas esperadas ou se houver qualquer
    problema ao carregar os dados.
    """

    try:
        # Carregar as configurações relevantes
        analysis_config = config['analysis']
        excel_columns = config['excel_columns']
        numeric_columns = config['numeric_columns'] 
        skip_rows = analysis_config['skip_rows']
        remove_first_column = analysis_config['remove_first_column']
        columns_to_remove = analysis_config.get('columns_to_remove', [])

        # Carregar o arquivo Excel
        df = pd.read_excel(uploaded_file, skiprows=skip_rows)

        # Remover a primeira coluna, se especificado
        if remove_first_column:
            df = df.iloc[:, 1:]

        # Remover colunas especificadas no arquivo de configuração
        removed_columns = []  # Lista para armazenar as colunas removidas
        for col in columns_to_remove:
            if col in df.columns:
                df = df.drop(columns=[col])
                removed_columns.append(col)

        # Verificar se as colunas necessárias estão presentes
        required_columns = list(excel_columns.values())
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Colunas ausentes no arquivo: {', '.join(missing_columns)}")

        # Converter colunas para tipos numéricos e de datas
        date_column = excel_columns['date']
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce')

        # Converter colunas numéricas especificadas na configuração
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    except Exception as e:
        st.error(f"Erro ao carregar ou processar o arquivo: {str(e)}")
        return None

def find_correct_columns(df, config):
    """
    Encontra os índices corretos das colunas no DataFrame com base no arquivo de configuração.

    Args:
    df (DataFrame): DataFrame contendo os dados carregados.
    config (dict): Dicionário de configuração contendo os nomes das colunas necessárias.

    Returns:
    dict: Um dicionário que mapeia as colunas esperadas para os seus respectivos índices no DataFrame.

    Este processo é necessário para garantir que as colunas do arquivo carregado estejam no formato
    e na ordem correta. Se alguma coluna obrigatória estiver ausente ou com um nome diferente,
    um erro é levantado para evitar inconsistências na análise posterior.
    """

    column_indices = {}
    columns = list(df.columns)
    
    # Encontrar o índice da última ocorrência de 'PREVISTO (KG)'
    previsto_indices = [i for i, col in enumerate(columns) if col == config['excel_columns']['previsto']]
    column_indices['previsto'] = previsto_indices[-1]
    
    # As colunas 'REALIZADO (KG)' e 'DIFERENÇA (%)' devem estar logo após 'PREVISTO (KG)'
    column_indices['realizado'] = column_indices['previsto'] + 1
    column_indices['diferenca'] = column_indices['previsto'] + 2
    
    # Verificar se os índices encontrados correspondem aos nomes esperados
    if (columns[column_indices['realizado']] != config['excel_columns']['realizado'] or
        columns[column_indices['diferenca']] != config['excel_columns']['diferenca_percentual']):
        raise ValueError("A estrutura da planilha não corresponde ao esperado.")
    
    return column_indices

def calculate_weighted_average_with_weights(df, pesos_relativos, config):
    """
    Calcula a média ponderada para cada batida com base nos pesos relativos dos tipos de alimento.

    Args:
    - df (DataFrame): DataFrame contendo os dados de entrada, incluindo informações como quantidade prevista,
                      quantidade realizada, diferença percentual e tipo de alimento.
    - pesos_relativos (dict): Dicionário contendo os pesos relativos de cada tipo de alimento. Os pesos indicam
                              a importância relativa de cada tipo no cálculo da média ponderada.
    - config (dict): Dicionário de configuração que contém parâmetros importantes, como nomes das colunas,
                     multiplicadores usados no cálculo e limites para a remoção de outliers.

    Returns:
    - DataFrame: DataFrame contendo as médias ponderadas para cada batida ('COD. BATIDA').

    Descrição do Cálculo:
    Esta função calcula uma média ponderada das diferenças percentuais entre o valor previsto e o realizado 
    para cada batida, utilizando os pesos relativos dos tipos de alimentos para ajustar a importância de 
    cada item no resultado final. O cálculo segue os seguintes passos:

    1. **Mapeamento dos Pesos Relativos**:
       A coluna que contém os tipos de alimento é mapeada para seus respectivos pesos relativos, conforme definido
       no dicionário `pesos_relativos`. Cada valor de tipo de alimento na coluna é substituído por seu peso correspondente.
       Se um tipo de alimento não for encontrado no dicionário, o valor resultante será `NaN`.

       Exemplo:
       ```
       tipos_alimentos = ['Tipo A', 'Tipo B', 'Tipo C']
       pesos_relativos = {'Tipo A': 1.2, 'Tipo B': 0.8, 'Tipo C': 1.5}
       ```

       O DataFrame resultante terá uma coluna `'PESO RELATIVO'` com os valores [1.2, 0.8, 1.5] correspondentes aos tipos.

    2. **Aplicação do Multiplicador de Pesos**:
       Se a configuração `peso_multiplicador` for ativada (`True`), o valor previsto é ajustado multiplicando-o
       pelo peso relativo, gerando a coluna `'PESO AJUSTADO'`. Caso contrário, o valor ajustado será igual ao valor previsto.

       - **Com `peso_multiplicador=True`**:
         ```
         PESO AJUSTADO = PREVISTO (KG) * PESO RELATIVO
         ```
       - **Com `peso_multiplicador=False`**:
         ```
         PESO AJUSTADO = PREVISTO (KG)
         ```

       Esse ajuste visa dar maior ou menor peso aos alimentos de acordo com sua importância, afetando diretamente 
       o valor de contribuição para a média ponderada.

    3. **Cálculo da Contribuição com Base na Diferença Percentual**:
       A contribuição de cada item é calculada multiplicando o valor ajustado (`PESO AJUSTADO`) pela diferença
       percentual absoluta (`DIFERENÇA (%) ABS`) e pelo peso relativo, dividindo o resultado por 100.

       Fórmula:
       ```
       CONTRIBUIÇÃO = PESO AJUSTADO * (DIFERENÇA (%) ABS * PESO RELATIVO) / 100
       ```
       
       - Isso assegura que diferenças maiores ou menores sejam proporcionalmente refletidas na média ponderada,
         e que alimentos com maior peso relativo tenham impacto maior na contribuição final.

    4. **Agrupamento e Cálculo da Média Ponderada por `COD. BATIDA`**:
       O DataFrame é então agrupado por `'COD. BATIDA'` para calcular a média ponderada das diferenças para cada batida.
       O agrupamento permite somar os valores de `'PESO AJUSTADO'` e `'CONTRIBUIÇÃO'` para cada batida.

       Fórmulas:
       - **Total Ajustado**:
         ```
         total_planned_quantity = grouped['PESO AJUSTADO'].sum()
         ```
       - **Total Contribuição**:
         ```
         total_contribution = grouped['CONTRIBUIÇÃO'].sum()
         ```
       - **Média Ponderada**:
         ```
         MÉDIA PONDERADA (%) = (total_contribution / total_planned_quantity) * 100
         ```

       O valor da média ponderada indica o desvio médio ajustado, considerando os pesos relativos de cada alimento.

    5. **Tratamento de Valores `NaN` e Retorno dos Resultados**:
       A média ponderada é calculada para cada batida, e valores `NaN` (que ocorrem, por exemplo, quando não há valor
       previsto ajustado para dividir) são substituídos por zero. Isso é feito para evitar resultados indefinidos que
       possam comprometer análises futuras.

    Exemplo de Uso:
    ```
    df = pd.DataFrame({
        'COD. BATIDA': [1, 1, 2, 2],
        'PREVISTO (KG)': [100, 150, 200, 250],
        'REALIZADO (KG)': [90, 140, 210, 260],
        'DIFERENÇA (%)': [-10, -6.67, 5, 4],
        'TIPO': ['Tipo A', 'Tipo B', 'Tipo A', 'Tipo C']
    })
    pesos_relativos = {'Tipo A': 1.2, 'Tipo B': 0.8, 'Tipo C': 1.5}
    config = {'weighted_average': {...}, 'excel_columns': {'cod_batida': 'COD. BATIDA'}}
    df_result = calculate_weighted_average_with_weights(df, pesos_relativos, config)
    ```

    Notas Adicionais:
    - **Erro `KeyError`**: Caso o nome de alguma coluna não seja encontrado no DataFrame, um erro é levantado,
      e uma mensagem é exibida ao usuário para ajudá-lo a corrigir o problema.
    - **Tratamento de Exceções Genéricas**: Mensagens de erro são exibidas em casos de exceções inesperadas,
      melhorando a experiência do usuário e auxiliando na depuração.
    - **Valores Faltantes (`NaN`)**: Quando um tipo de alimento não é encontrado no dicionário de pesos, o valor
      correspondente na coluna `'PESO RELATIVO'` será `NaN`. Recomenda-se tratar esses casos previamente, seja
      ajustando o dicionário de pesos ou substituindo valores faltantes por um peso padrão.

    A função é central para a análise dos dados de batidas e deve ser usada com atenção aos detalhes de configuração
    e à qualidade dos dados de entrada, para garantir a precisão dos resultados.
    """

    try:
        # Carregar parâmetros do arquivo de configuração
        previsto_col = config['weighted_average']['previsto_column']
        realizado_col = config['weighted_average']['realizado_column']
        diferenca_percentual_col = config['weighted_average']['diferenca_percentual_column']
        pesos_relativos_col = config['weighted_average']['pesos_relativos_column']
        peso_multiplicador = config['weighted_average']['peso_multiplicador']
        outlier_threshold = config['weighted_average']['outlier_threshold']
        
        # Criar uma cópia do DataFrame para evitar SettingWithCopyWarning
        df = df.copy()

        # Converter colunas para numérico, permitindo números com casas decimais
        df[previsto_col] = pd.to_numeric(df[previsto_col], errors='coerce')
        df[realizado_col] = pd.to_numeric(df[realizado_col], errors='coerce')
        df[diferenca_percentual_col] = pd.to_numeric(df[diferenca_percentual_col], errors='coerce')
        df['DIFERENÇA (%) ABS'] = df[diferenca_percentual_col].abs()

        # Mapeamento dos pesos relativos
        df['PESO RELATIVO'] = df[pesos_relativos_col].map(pesos_relativos)

        # Aplicar o multiplicador de pesos se configurado
        if peso_multiplicador:
            df['PESO AJUSTADO'] = df[previsto_col] * df['PESO RELATIVO']
        else:
            df['PESO AJUSTADO'] = df[previsto_col]

        # Calcular a contribuição com base na diferença percentual
        df['CONTRIBUIÇÃO'] = df['PESO AJUSTADO'] * ((df['DIFERENÇA (%) ABS'] * df['PESO RELATIVO']) / 100)

        # Agrupamento por COD. BATIDA e cálculo da média ponderada
        grouped = df.groupby(config['excel_columns']['cod_batida'])
        total_planned_quantity = grouped['PESO AJUSTADO'].sum()
        total_contribution = grouped['CONTRIBUIÇÃO'].sum()
        calculated_weighted_avg = (total_contribution / total_planned_quantity) * 100        
        # Retornar DataFrame com a média ponderada
        weighted_averages = pd.DataFrame({
            config['excel_columns']['cod_batida']: total_planned_quantity.index,
            'MÉDIA PONDERADA (%)': calculated_weighted_avg.fillna(0).astype(float)        
        })
        
        return weighted_averages

    except KeyError as e:
        st.error(f"Erro ao acessar coluna: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Erro no cálculo da média ponderada: {str(e)}")
        return None

def create_statistics_dataframe(weighted_average_df, remove_outliers=False):
    """
    Cria um DataFrame com as principais estatísticas das diferenças percentuais.

    Args:
    weighted_average_df (DataFrame): DataFrame contendo as médias ponderadas das diferenças percentuais.
    remove_outliers (bool): Se True, remove outliers antes de calcular as estatísticas.

    Returns:
    DataFrame: DataFrame contendo as estatísticas calculadas, incluindo:
        - Número de batidas (linhas no DataFrame)
        - Média ponderada das diferenças percentuais
        - Mediana das diferenças percentuais
        - Contagem de batidas em intervalos específicos (3% a 5%, 5% a 7%, >7%).

    A função calcula a média e mediana das diferenças percentuais e conta quantas batidas estão em 
    intervalos específicos de variação. Se solicitado, remove outliers antes do cálculo.
    """

    # Criar uma cópia do DataFrame para não modificar o original
    df = weighted_average_df.copy()

    if remove_outliers:
        df = remove_outliers_from_df(df, 'MÉDIA PONDERADA (%)')

    # Calcular as estatísticas com base na média ponderada corrigida
    stats_data = {
        'Estatística': [
            'Número de Batidas', 
            'Média Ponderada (%)', 
            'Mediana Ponderada (%)',
            'Diferença entre 3% e 5%',
            'Diferença entre 5% e 7%',
            'Diferença acima de 7%'
        ],
        'Valor': [
            len(df),  # Número total de batidas
            f"{df['MÉDIA PONDERADA (%)'].mean():.2f}",  # Média ponderada
            f"{df['MÉDIA PONDERADA (%)'].median():.2f}",  # Mediana ponderada
            ((df['MÉDIA PONDERADA (%)'] >= 3) & (df['MÉDIA PONDERADA (%)'] < 5)).sum(),  # Contagem entre 3% e 5%
            ((df['MÉDIA PONDERADA (%)'] >= 5) & (df['MÉDIA PONDERADA (%)'] < 7)).sum(),  # Contagem entre 5% e 7%
            (df['MÉDIA PONDERADA (%)'] >= 7).sum()  # Contagem acima de 7%
        ]
    }

    # Garantir que os valores estão no formato numérico adequado
    stats_df = pd.DataFrame(stats_data)
    stats_df['Valor'] = pd.to_numeric(stats_df['Valor'], errors='coerce')  # Converter valores para numérico

    return stats_df

def remove_outliers_from_df(df, column):
    """
    Remove outliers de uma coluna específica de um DataFrame usando o intervalo interquartil (IQR).

    Args:
    df (DataFrame): DataFrame do qual os outliers serão removidos.
    column (str): Nome da coluna na qual os outliers serão identificados e removidos.

    Returns:
    DataFrame: DataFrame sem os outliers identificados na coluna especificada.

    A função usa o intervalo interquartil (IQR) para definir limites inferior e superior e
    remover valores que estão fora desses limites, considerando-os como outliers.
    """

    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    upper_bound = Q3 + 1.5 * IQR
    return df[df[column] <= upper_bound]

def filter_data(df, operadores, alimentos, dietas, start_date, end_date):
    """
    Filtra os dados com base nos operadores, alimentos, dietas e intervalo de datas fornecidos.

    Args:
    df (DataFrame): DataFrame contendo os dados brutos.
    operadores (list): Lista de operadores selecionados para filtrar os dados.
    alimentos (list): Lista de alimentos selecionados para filtrar os dados.
    dietas (list): Lista de dietas selecionadas para filtrar os dados.
    start_date (datetime): Data de início do filtro de datas.
    end_date (datetime): Data de término do filtro de datas.

    Returns:
    DataFrame: DataFrame filtrado conforme os critérios especificados.

    A função aplica filtros aos dados com base nos operadores, alimentos, dietas e o intervalo
    de datas definido pelo usuário, retornando apenas os registros que correspondem a esses critérios.
    """

    # Converter start_date e end_date para datetime
    start_datetime = pd.to_datetime(start_date)
    end_datetime = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    
    df = df[(df['DATA'] >= start_datetime) & (df['DATA'] <= end_datetime)]
    
    if 'Todos' not in operadores:
        df = df[df['OPERADOR'].isin(operadores)]
    if 'Todos' not in alimentos:
        df = df[df['ALIMENTO'].isin(alimentos)]
    if 'Todos' not in dietas:
        df = df[df['NOME'].isin(dietas)]
    
    return df

def calculate_histogram_bins(data):
    """
    Calcula os limites e o número de bins para o histograma usando a regra de Freedman-Diaconis.

    Args:
    data (Series): Série ou lista de dados numéricos para os quais o histograma será calculado.

    Returns:
    tuple: (limite inferior, limite superior, número de bins) para o histograma.

    Esta função calcula a largura dos bins e determina o número ideal de bins com base
    na regra de Freedman-Diaconis, que leva em conta o intervalo interquartil e o tamanho da amostra.
    """

    # Compute the first and third quartiles and the IQR
    q1, q3 = np.percentile(data, [25, 75])
    iqr = q3 - q1

    # Define the lower bound as the minimum non-negative value and calculate upper bound
    lower_bound = data[data >= 0].min()
    upper_bound = q3 + 1.5 * iqr

    # Ajustar os limites para o número inteiro mais próximo
    upper_bound = np.ceil(upper_bound)

    # Usar bins adaptativos
    bin_width = 2 * iqr * (len(data) ** (-1/3))  # Regra de Freedman-Diaconis
    n_bins = int((upper_bound - lower_bound) / bin_width)
    n_bins = min(n_bins, 100)  # Limitar o número máximo de bins

    return lower_bound, upper_bound, n_bins

def color_histogram_bars(patches, bins):
    """
    Aplica cores às barras do histograma com base nos valores dos bins.

    Args:
    patches (list): Lista de patches (barras) do histograma.
    bins (list): Lista de valores dos bins.

    A função aplica cores às barras do histograma, destacando os valores de acordo
    com a magnitude dos bins. A cor pode ser configurada para destacar intervalos específicos.
    """

    for patch, bin_value in zip(patches, bins[:-1]):
        if bin_value >= 3:
            color_intensity = min((bin_value - 3) / (bins[-1] - 3), 1)  # Intensidade baseada na distância do valor 3
            patch.set_facecolor((1, 0, 0, color_intensity))  # Escala de vermelho
        else:
            color_intensity = min((3 - bin_value) / 3, 1)  # Intensidade baseada na proximidade do valor 0
            patch.set_facecolor((0, 1, 0, color_intensity))  # Escala de verde

def create_histogram(df, start_date, end_date, remove_outliers, pesos_relativos):
    """
    Cria e exibe um histograma com base nas médias ponderadas das diferenças percentuais.

    Args:
    df (DataFrame): DataFrame contendo as médias ponderadas das diferenças percentuais.
    start_date (datetime): Data de início para o filtro de datas.
    end_date (datetime): Data de término para o filtro de datas.
    remove_outliers (bool): Se True, remove outliers dos dados antes de criar o histograma.
    pesos_relativos (dict): Dicionário contendo os pesos relativos de cada tipo de alimento.

    Returns:
    matplotlib.figure.Figure: A figura contendo o histograma gerado.

    A função cria um histograma para visualizar a distribuição das médias ponderadas das diferenças percentuais,
    removendo outliers conforme necessário. Ela também aplica uma linha vertical de referência com base no valor de tolerância
    e adiciona uma tabela de pesos ao gráfico. As configurações de layout e aparência são controladas pelas configurações 
    definidas no arquivo de configuração.
    """

    fig, ax = plt.subplots(figsize=tuple(config['visualization']['histogram_figsize']))
    
    if remove_outliers:
        df = remove_outliers_from_df(df, 'MÉDIA PONDERADA (%)')
    
    data = df['MÉDIA PONDERADA (%)']
    data = data[data >= 0]  # Considerar apenas valores positivos
    
    lower_bound, upper_bound, n_bins = calculate_histogram_bins(data)
    
    # Criar o histograma
    n, bins, patches = ax.hist(data, bins=n_bins, range=(lower_bound, upper_bound), edgecolor='black')
    
    # Colorir as barras com escala de cores
    color_histogram_bars(patches, bins)
    
    ax.set_xlabel(config['visualization']['x_label'])  # Usando o parâmetro do arquivo de configuração
    ax.set_ylabel(config['visualization']['y_label'])  # Usando o parâmetro do arquivo de configuração
    ax.set_title(config['visualization']['histogram_title'])
    
    # Adicionar linha vertical no valor de tolerância com estilo tracejado
    tolerance = config['analysis']['tolerance_threshold']
    ax.axvline(x=tolerance, color='green', linestyle='--', linewidth=2, 
               label=f'Tolerância Máxima ({tolerance}%)')
    
    legend_config = config['visualization']['legend']
    ax.legend(
        loc=legend_config['location'],
        fontsize=legend_config['fontsize'],
        frameon=True,
        facecolor=legend_config['facecolor'],
        edgecolor=legend_config['edgecolor'],
        framealpha=legend_config['framealpha'],
        bbox_to_anchor=tuple(legend_config['bbox_to_anchor']),
        bbox_transform=ax.transAxes
    )

    # Configurar o grid
    grid_config = config['visualization']['grid_style']
    ax.grid(axis=grid_config['axis'], linestyle=grid_config['linestyle'], linewidth=grid_config['linewidth'])
    ax.set_axisbelow(True)  # Colocar o grid atrás das barras
    ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=20, prune='both'))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: f"{int(x)}"))
    
    # Configurar o fuso horário de Brasília
    brasilia_tz = pytz.timezone(config['timezone'])
    now_brasilia = datetime.datetime.now(brasilia_tz)
    
    footer_config = config['visualization']['footer']
    # Adicionar informações no rodapé
    plt.figtext(0.5, 0.01, f"Período analisado: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}", 
                ha="center", fontsize=footer_config['fontsize'])
    plt.figtext(0.01, 0.01, f"Total de batidas: {len(df)}", fontsize=footer_config['fontsize'])
    plt.figtext(0.99, 0.01, f"Gerado em: {now_brasilia.strftime('%d/%m/%Y %H:%M')} (Horário de Brasília)", 
                ha="right", fontsize=footer_config['fontsize'])
    
    # Adicionar pesos relativos no lado direito da área do gráfico
    weights_config = config['visualization']['weights_table']
    pesos_text = "Pesos relativos dos tipos de alimento:\n"
    pesos_text += "\n".join([f"{tipo:>20}: {peso:>4.1f}" for tipo, peso in pesos_relativos.items()])
    fig.text(weights_config['position'][0], weights_config['position'][1], 
             pesos_text, ha='right', fontsize=weights_config['fontsize'], va='top', linespacing=1.5,
             bbox=dict(facecolor=weights_config['facecolor'], 
                       alpha=weights_config['alpha'], 
                       boxstyle=weights_config['boxstyle']))

    plt.tight_layout()
    subplot_config = config['visualization']['subplot_adjust']
    plt.subplots_adjust(left=subplot_config['left'],
                        right=subplot_config['right'],
                        bottom=subplot_config['bottom'],
                        top=subplot_config['top'])
    
    return fig

def save_histogram_as_image(fig):
    """
    Salva o histograma gerado como uma imagem PNG e retorna um link para download.

    Args:
    fig (matplotlib.figure.Figure): A figura do histograma a ser salva.

    Returns:
    str: Link para download da imagem gerada.

    Esta função salva o histograma como uma imagem PNG de alta resolução e retorna um link que pode ser usado
    para o usuário fazer o download da imagem diretamente da interface.
    """

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)
    b64 = base64.b64encode(buf.getvalue()).decode()
    href = f'<a href="data:image/png;base64,{b64}" download="histograma.png">Download do Histograma (PNG)</a>'
    return href

def save_statistics_as_csv(stats_df):
    """
    Salva as estatísticas geradas como um arquivo CSV e retorna um link para download.

    Args:
    stats_df (DataFrame): DataFrame contendo as estatísticas calculadas.

    Returns:
    str: Link para download do arquivo CSV gerado.

    A função exporta as estatísticas principais para um arquivo CSV e gera um link que permite
    ao usuário baixar o arquivo diretamente da interface Streamlit.
    """

    csv = stats_df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="estatisticas.csv">Download das Estatísticas (CSV)</a>'
    return href

def main():
    """
    Função principal que controla a execução do programa e a interação com o usuário via Streamlit.

    A função 'main()' orquestra as seguintes atividades:
    1. Carregamento do arquivo de configuração usando a função `read_config()`.
    2. Configuração da página e layout da interface do usuário.
    3. Gerenciamento do upload do arquivo Excel e processamento dos dados via `load_and_process_data()`.
    4. Filtragem dos dados com base nos operadores, alimentos, dietas e datas selecionadas pelo usuário.
    5. Cálculo das médias ponderadas das diferenças percentuais via `calculate_weighted_average_with_weights()`.
    6. Geração e exibição de um histograma usando a função `create_histogram()`.
    7. Cálculo e exibição das principais estatísticas com opção de exportação para CSV.
    8. Permite salvar o histograma como PNG e exibe links para download dos arquivos gerados.

    A função serve como ponto de entrada para o programa e gerencia todas as interações entre o usuário
    e os dados fornecidos, desde a configuração inicial até a geração dos resultados.
    """

    # Carregar configurações
    config = read_config()

    # Configuração da página Streamlit
    st.set_page_config(page_title=config['ui']['page_title'], layout="wide")
    
    st.title(config['ui']['page_title'])

    # Criar duas colunas principais
    col1, col2 = st.columns([1, 3])  # Proporção de 1:3 entre as colunas

    with col1:
        st.header(config['ui']['analysis_config_header'])
        
        # Upload do arquivo
        uploaded_file = st.file_uploader(
            config['ui']['file_uploader']['label'], 
            type=config['ui']['file_uploader']['allowed_types']
        )

        if uploaded_file is not None:
            df = load_and_process_data(uploaded_file)
            
            if df is not None:
                st.success("Arquivo carregado com sucesso!")

                # Filtros de data
                min_date = df[config['excel_columns']['date']].min().date()
                max_date = df[config['excel_columns']['date']].max().date()
                start_date, end_date = st.date_input(
                    config['ui']['date_input']['label'],
                    [min_date, max_date],
                    min_value=min_date,
                    max_value=max_date
                )

                # Seleção de operadores
                operadores = ['Todos'] + sorted(df[config['excel_columns']['operator']].unique().tolist())
                operadores_selecionados = st.selectbox(
                    config['ui']['multiselect']['operator_label'],
                    operadores
                )

                # Seleção de alimentos
                alimentos = ['Todos'] + sorted(df[config['excel_columns']['alimento']].unique().tolist())
                alimentos_selecionados = st.selectbox(
                    config['ui']['multiselect']['food_label'],
                    alimentos
                )

                # Seleção de dietas
                dietas = ['Todos'] + sorted(df[config['excel_columns']['nome']].unique().tolist())
                dietas_selecionadas = st.selectbox(
                    config['ui']['multiselect']['diet_label'],
                    dietas
                )

                # Encapsular em lista para uso com df.isin()
                operadores_selecionados = [operadores_selecionados]
                alimentos_selecionados = [alimentos_selecionados]
                dietas_selecionadas = [dietas_selecionadas]

                # Filtrar os dados
                df_filtered = filter_data(df, operadores_selecionados, alimentos_selecionados, dietas_selecionadas, start_date, end_date)

                # Configuração de pesos relativos com valores do config.yaml
                st.subheader(config['ui']['food_weights_subheader'])
                tipos_alimentos = df[config['excel_columns']['tipo']].unique().tolist()
                pesos_relativos = {}
                for tipo in tipos_alimentos:
                    peso = st.slider(
                        f"Peso para tipo de alimento '{tipo}':", 
                        min_value=config['slider']['min_value'],  # Valor mínimo definido no config.yaml
                        max_value=config['slider']['max_value'],  # Valor máximo definido no config.yaml
                        value=config['analysis']['default_weight'], 
                        step=config['slider']['step']  # Step definido no config.yaml
                    )
                    pesos_relativos[tipo] = peso

                # Opção para remover outliers
                remover_outliers = st.checkbox(
                    config['ui']['remove_outliers']['label'],
                    help=config['ui']['remove_outliers']['help']
                )

                # Botão para iniciar a análise
                iniciar_analise = st.button(config['ui']['generate_button'])

    with col2:
        if uploaded_file is not None and df is not None and iniciar_analise:
            st.header(config['ui']['results_header'])

            # Filtrar os dados
            df_filtered = filter_data(df, operadores_selecionados, alimentos_selecionados, dietas_selecionadas, start_date, end_date)
            
            if df_filtered.empty:
                st.warning("Não há dados suficientes para gerar a análise.")
            else:
                # Forçar a conversão de strings para números em todas as colunas numéricas
                df_filtered = df_filtered.copy()
                df_filtered[['PREVISTO (KG)', 'REALIZADO (KG)', 'PREVISTO (KG).1', 'REALIZADO (KG).1', 'DIFERENÇA (KG)', 'DIFERENÇA (%)']] = \
                df_filtered[['PREVISTO (KG)', 'REALIZADO (KG)', 'PREVISTO (KG).1', 'REALIZADO (KG).1', 'DIFERENÇA (KG)', 'DIFERENÇA (%)']].apply(pd.to_numeric, errors='coerce')
                
                # Calcular a média ponderada
                weighted_average_df = calculate_weighted_average_with_weights(df_filtered, pesos_relativos, config)
                
                if weighted_average_df is not None:
                    # Criar e exibir o histograma
                    fig = create_histogram(weighted_average_df, start_date, end_date, remover_outliers, pesos_relativos)
                    st.pyplot(fig)
                    
                    # Adicionar opção para salvar o histograma
                    st.markdown(save_histogram_as_image(fig), unsafe_allow_html=True)

                    # Criar duas colunas para exibir as tabelas lado a lado
                    col1, col2 = st.columns(2)

                    # Exibir estatísticas na primeira coluna
                    with col1:
                        st.subheader(config['ui']['statistics_title'])
                        stats_df = create_statistics_dataframe(weighted_average_df, remover_outliers)
                        st.write(stats_df)

                    # Exibir pesos relativos na segunda coluna
                    with col2:
                        st.subheader(config['ui']['food_weights_subheader'])
                        pesos_df = pd.DataFrame(list(pesos_relativos.items()), columns=['Tipo de Alimento', 'Peso Relativo'])
                        st.write(pesos_df)

                    # Adicionar data de geração e opção para download
                    data_geracao = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    stats_df['Data de Geração'] = data_geracao
                    pesos_df['Data de Geração'] = data_geracao
                    combined_df = pd.concat([stats_df, pesos_df], ignore_index=True, sort=False)
                    st.markdown(save_statistics_as_csv(combined_df), unsafe_allow_html=True)

                    # Informar sobre a remoção de outliers, se aplicável
                    if remover_outliers:
                        st.info(config['ui'].get('outliers_removed_message', "Outliers foram removidos do histograma para melhor visualização."))
                else:
                    st.error("Não foi possível calcular as médias ponderadas. Verifique os dados e tente novamente.")

if __name__ == "__main__":
    main()