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

def preprocess_dataframe(df, config):
    """
    Pré-processa um DataFrame, convertendo colunas para numéricas e verificando colunas obrigatórias.

    Parâmetros:
    df (DataFrame): DataFrame a ser processado.
    config (dict): Configurações com colunas numéricas e obrigatórias.

    Retorna:
    DataFrame: DataFrame processado.

    Exceções:
    ValueError: Se faltar alguma coluna obrigatória.
    """
    # Carregar configurações de colunas numéricas e obrigatórias
    numeric_columns = config['numeric_columns']
    excel_columns = config['excel_columns']

    # Verificar se as colunas necessárias estão presentes
    required_columns = list(excel_columns.values())
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Colunas ausentes no arquivo: {', '.join(missing_columns)}")

    # Converter colunas numéricas especificadas na configuração
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df

def load_and_process_data(uploaded_file):
    """
    Carrega e processa dados de um arquivo Excel.

    Parâmetros:
    uploaded_file: Arquivo Excel (.xlsx) carregado pelo usuário.

    Retorna:
    DataFrame: Dados processados e prontos para análise.

    Processamento:
    1. Carrega o Excel, pulando linhas conforme configuração.
    2. Remove primeira coluna, se configurado.
    3. Remove colunas especificadas na configuração.
    4. Verifica presença de colunas necessárias.
    5. Converte colunas para tipos apropriados.

    Exibe erro se faltar colunas ou houver problemas no carregamento.
    """

    try:
        # Carregar as configurações relevantes
        analysis_config = config['analysis']
        excel_columns = config['excel_columns']
        skip_rows = analysis_config['skip_rows']
        remove_first_column = analysis_config['remove_first_column']
        columns_to_remove = analysis_config.get('columns_to_remove', [])

        # Carregar o arquivo Excel
        df = pd.read_excel(uploaded_file, skiprows=skip_rows)

        # Remover a primeira coluna, se especificado
        if remove_first_column:
            df = df.iloc[:, 1:]

        # Itera sobre a lista de colunas a serem removidas especificadas no arquivo de configuração.
        removed_columns = []  # Inicializa uma lista para armazenar os nomes das colunas que foram efetivamente removidas do DataFrame.
        for col in columns_to_remove:  # Para cada coluna na lista columns_to_remove:
            if col in df.columns:  # Verifica se a coluna atual está presente nas colunas do DataFrame.
                df = df.drop(columns=[col])  # Remove a coluna do DataFrame.
                removed_columns.append(col)  # Adiciona o nome da coluna removida à lista removed_columns.

        # Pré-processar o DataFrame (converter colunas numéricas e verificar colunas necessárias)
        df = preprocess_dataframe(df, config)

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

    Parâmetros:
    - df (DataFrame): Dados de entrada (quantidades previstas, realizadas, diferenças percentuais, tipos de alimento).
    - pesos_relativos (dict): Pesos relativos de cada tipo de alimento.
    - config (dict): Configurações (nomes de colunas, parâmetros de cálculo).

    Retorna:
    - DataFrame: Médias ponderadas para cada batida ('COD. BATIDA').

    Processo de cálculo:
    1. Mapeia tipos de alimento para seus pesos.
    2. Ajusta valores previstos com pesos (se configurado).
    3. Calcula contribuição: CONTRIBUIÇÃO = PESO AJUSTADO * (DIFERENÇA (%) ABS * PESO RELATIVO) / 100
    4. Agrupa por 'COD. BATIDA' e calcula média ponderada:
       MÉDIA PONDERADA (%) = (soma das contribuições / soma dos pesos ajustados) * 100
    5. Substitui NaN por zero no resultado.

    Exemplo de cálculo:
    Dados de entrada:
    COD. BATIDA | PREVISTO (KG) | REALIZADO (KG) | DIFERENÇA (%) | TIPO
    1           | 100           | 90             | -10           | A
    1           | 150           | 140            | -6.67         | B
    2           | 200           | 210            | 5             | A
    2           | 250           | 260            | 4             | C

    Pesos relativos: A: 1.2, B: 0.8, C: 1.5

    Cálculo para COD. BATIDA 1:
    1. PESO AJUSTADO: 100 * 1.2 = 120, 150 * 0.8 = 120
    2. CONTRIBUIÇÃO: (120 * 10 * 1.2) / 100 = 14.4, (120 * 6.67 * 0.8) / 100 = 6.4
    3. MÉDIA PONDERADA = (14.4 + 6.4) / (120 + 120) * 100 = 8.67%

    Resultado final:
    COD. BATIDA | MÉDIA PONDERADA (%)
    1           | 8.67
    2           | 5.71

    Observações:
    - Trata erros de chaves não encontradas e exceções genéricas.
    - Recomenda-se tratar valores faltantes nos pesos relativos antes do uso.
    """

    try:
        # Carregar as configurações relevantes
        weighted_config = config['weighted_average']
        excel_columns = config['excel_columns']
        previsto_col = weighted_config['previsto_column']
        realizado_col = weighted_config['realizado_column']
        diferenca_percentual_col = weighted_config['diferenca_percentual_column']
        pesos_relativos_col = weighted_config['pesos_relativos_column']
        peso_multiplicador = weighted_config['peso_multiplicador']

        # Criar uma cópia do DataFrame para evitar SettingWithCopyWarning
        df = df.copy()

        # Converter colunas para numérico, permitindo números com casas decimais
        df = preprocess_dataframe(df, config)
        df[diferenca_percentual_col] = df[diferenca_percentual_col].abs()

        # Mapeamento dos pesos relativos
        df['PESO RELATIVO'] = df[pesos_relativos_col].map(pesos_relativos)

        # Aplicar o multiplicador de pesos se configurado (caso contrário, usa o valor previsto diretamente)
        if peso_multiplicador:
            # Ajusta o peso multiplicando a coluna prevista pelo peso relativo
            df['PESO AJUSTADO'] = df[previsto_col] * df['PESO RELATIVO']
        else:
            # Caso não haja multiplicador, o peso ajustado é igual ao previsto
            df['PESO AJUSTADO'] = df[previsto_col]

        # CALCULAR A CONTRIBUIÇÃO COM BASE NA DIFERENÇA PERCENTUAL
        # Para cada linha, a contribuição é calculada multiplicando o peso ajustado pela diferença percentual (ajustada pelo peso relativo) e depois dividida por 100
        df['CONTRIBUIÇÃO'] = df['PESO AJUSTADO'] * ((df[diferenca_percentual_col] * df['PESO RELATIVO']) / 100)

        # Agrupa o DataFrame pelo código da batida para calcular somatórios
        grouped = df.groupby(excel_columns['cod_batida'])
        
        # Soma total dos pesos ajustados por grupo de código de batida
        total_planned_quantity = grouped['PESO AJUSTADO'].sum()
        
        # Soma total das contribuições por grupo de código de batida
        total_contribution = grouped['CONTRIBUIÇÃO'].sum()
        
        # Calcula a média ponderada da contribuição em relação ao peso ajustado, convertida para porcentagem
        calculated_weighted_avg = (total_contribution / total_planned_quantity) * 100

        # Retornar DataFrame com a média ponderada
        weighted_averages = pd.DataFrame({
            excel_columns['cod_batida']: total_planned_quantity.index,
            'MÉDIA PONDERADA (%)': calculated_weighted_avg.fillna(0).astype(float)
        })

        return weighted_averages

    except KeyError as e:
        st.error(f"Erro ao acessar coluna: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Erro no cálculo da média ponderada: {str(e)}")
        return None

def create_statistics_dataframe(weighted_average_df, remove_outliers=False, config=None):
    """
    Cria um DataFrame com as principais estatísticas das diferenças percentuais.

    Args:
    weighted_average_df (DataFrame): DataFrame contendo as médias ponderadas das diferenças percentuais.
    remove_outliers (bool): Se True, remove outliers antes de calcular as estatísticas.
    config (dict): Dicionário de configuração contendo os parâmetros necessários.

    Returns:
    DataFrame: DataFrame contendo as estatísticas calculadas, incluindo:
        - Número de batidas (linhas no DataFrame)
        - Média ponderada das diferenças percentuais
        - Mediana das diferenças percentuais
        - Contagem de batidas em intervalos específicos.

    A função calcula a média e mediana das diferenças percentuais e conta quantas batidas estão em 
    intervalos específicos de variação. Se solicitado, remove outliers antes do cálculo.
    """
    # Verificar se `config` foi passado e se contém a seção necessária
    if config is None:
        raise ValueError("O parâmetro `config` não foi fornecido para `create_statistics_dataframe`.")
    
    if 'statistics' not in config or 'interval_limits' not in config['statistics']:
        raise KeyError("A chave 'statistics' ou 'interval_limits' não está presente no `config`. "
                       "Verifique se o arquivo de configuração está correto e atualizado.")

    # Criar uma cópia do DataFrame para não modificar o original
    df = weighted_average_df.copy()

    if remove_outliers:
        df = remove_outliers_from_df(df, 'MÉDIA PONDERADA (%)')

    # Carregar limites dos intervalos do arquivo de configuração
    interval_limits = config['statistics']['interval_limits']

    # Calcular as estatísticas com base na média ponderada corrigida
    stats_data = {
        'Estatística': [
            'Número de Batidas', 
            'Média Ponderada (%)', 
            'Mediana Ponderada (%)',
            f"Diferença entre {interval_limits['low_1']}% e {interval_limits['high_1']}%",
            f"Diferença entre {interval_limits['low_2']}% e {interval_limits['high_2']}%",
            f"Diferença acima de {interval_limits['high_2']}%"
        ],
        'Valor': [
            len(df),  # Número total de registros de batidas
            round(df['MÉDIA PONDERADA (%)'].mean(), 1),  # Média ponderada dos valores na coluna MÉDIA PONDERADA (%), arredondada para 1 casa decimal
            round(df['MÉDIA PONDERADA (%)'].median(), 1),  # Mediana dos valores na coluna MÉDIA PONDERADA (%), arredondada para 1 casa decimal
            ((df['MÉDIA PONDERADA (%)'] >= interval_limits['low_1']) & 
             (df['MÉDIA PONDERADA (%)'] < interval_limits['high_1'])).sum(),  # Contagem de registros com MÉDIA PONDERADA (%) entre low_1% e high_1%
            ((df['MÉDIA PONDERADA (%)'] >= interval_limits['low_2']) & 
             (df['MÉDIA PONDERADA (%)'] < interval_limits['high_2'])).sum(),  # Contagem de registros com MÉDIA PONDERADA (%) entre low_2% e high_2%
            (df['MÉDIA PONDERADA (%)'] >= interval_limits['high_2']).sum()  # Contagem de registros com MÉDIA PONDERADA (%) acima de high_2%
        ]
    }

    # Criar o DataFrame com os resultados
    stats_df = pd.DataFrame(stats_data)

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

def create_histogram(df, start_date, end_date, remove_outliers, pesos_relativos, config):
    """
    Cria e exibe um histograma com base nas médias ponderadas das diferenças percentuais.

    Args:
    df (DataFrame): DataFrame contendo as médias ponderadas das diferenças percentuais.
    start_date (datetime): Data de início para o filtro de datas.
    end_date (datetime): Data de término para o filtro de datas.
    remove_outliers (bool): Se True, remove outliers dos dados antes de criar o histograma.
    pesos_relativos (dict): Dicionário contendo os pesos relativos de cada tipo de alimento.
    config (dict): Dicionário de configuração contendo as informações necessárias.

    Returns:
    matplotlib.figure.Figure: A figura contendo o histograma gerado.
    
    A função cria um histograma para visualizar a distribuição das médias ponderadas das diferenças percentuais,
    removendo outliers conforme necessário. Ela também aplica uma linha vertical de referência com base no valor de tolerância
    e adiciona uma tabela de pesos ao gráfico. As configurações de layout e aparência são controladas pelas configurações 
    definidas no arquivo de configuração.
    """

    # Configuração do tamanho do histograma (figura)
    figsize = tuple(config['visualization']['histogram_figsize'])
    fig, ax = plt.subplots(figsize=figsize)
    
    # Remover outliers se necessário
    if remove_outliers:
        df = remove_outliers_from_df(df, 'MÉDIA PONDERADA (%)')
    
    # Obter dados para o histograma e filtrar valores não negativos
    data = df['MÉDIA PONDERADA (%)']
    data = data[data >= 0]

    # Definir os limites e calcular a quantidade de bins do histograma
    lower_bound, upper_bound, n_bins = calculate_histogram_bins(data)
    
    # Criar o histograma
    n, bins, patches = ax.hist(data, bins=n_bins, range=(lower_bound, upper_bound), edgecolor='black')

    # Colorir as barras com escala de cores
    color_histogram_bars(patches, bins)
    
    # Configurações dos rótulos e título
    ax.set_xlabel(config['visualization']['x_label'])
    ax.set_ylabel(config['visualization']['y_label'])
    ax.set_title(config['visualization']['histogram_title'])

    # Adicionar linha vertical para marcar a tolerância
    tolerance = config['analysis']['tolerance_threshold']
    vertical_line_config = config['visualization']['vertical_line']
    ax.axvline(
        x=tolerance,
        color=vertical_line_config['color'],
        linestyle=vertical_line_config['linestyle'],
        linewidth=vertical_line_config['linewidth'],
        label=f"{vertical_line_config['label']} ({tolerance}%)"
    )
    
    # Configurar a legenda do histograma
    legend_config = config['visualization']['legend']
    ax.legend(
        loc=legend_config['location'],
        fontsize=legend_config['fontsize'],
        frameon=legend_config['frameon'],
        facecolor=legend_config['facecolor'],
        edgecolor=legend_config['edgecolor'],
        fancybox=legend_config['fancybox'],
        framealpha=legend_config['framealpha'],
        bbox_to_anchor=legend_config['bbox_to_anchor']
    )

    # Configurar o grid
    grid_config = config['visualization']['grid_style']
    ax.grid(axis=grid_config['axis'], linestyle=grid_config['linestyle'], linewidth=grid_config['linewidth'])
    ax.set_axisbelow(True)  # Colocar o grid atrás das barras

    # Ajustar o eixo X
    ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=20, prune='both'))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: f"{int(x)}"))

    # Configurar o fuso horário de Brasília
    brasilia_tz = pytz.timezone(config['timezone'])
    now_brasilia = datetime.datetime.now(brasilia_tz)

    # Configuração do rodapé usando as variáveis do arquivo de configuração
    footer_config = config['visualization']['footer']
    footer_texts = footer_config['texts']
    footer_positions = footer_config['positions']
    footer_alignments = footer_config['alignments']

    plt.figtext(
        footer_positions['period_position'][0], footer_positions['period_position'][1],
        footer_texts['period_text'].format(start_date=start_date.strftime('%d/%m/%Y'), end_date=end_date.strftime('%d/%m/%Y')),
        ha=footer_alignments['period_alignment'], fontsize=footer_config['fontsize']
    )
    plt.figtext(
        footer_positions['total_position'][0], footer_positions['total_position'][1],
        footer_texts['total_text'].format(total_batidas=len(df)),
        ha=footer_alignments['total_alignment'], fontsize=footer_config['fontsize']
    )
    plt.figtext(
        footer_positions['generated_position'][0], footer_positions['generated_position'][1],
        footer_texts['generated_text'].format(generated_time=now_brasilia.strftime('%d/%m/%Y %H:%M')),
        ha=footer_alignments['generated_alignment'], fontsize=footer_config['fontsize']
    )
    
    # Adicionar tabela de pesos relativos
    weights_config = config['visualization']['weights_table']
    pesos_text = "Pesos relativos dos tipos de alimentos:\n"
    pesos_text += "\n".join([f"{tipo:>20}: {peso:>4.1f}" for tipo, peso in pesos_relativos.items()])
    fig.text(
        weights_config['position'][0],
        weights_config['position'][1],
        pesos_text,
        ha='right',
        fontsize=weights_config['fontsize'],
        va='top',
        linespacing=1.5,
        bbox=dict(
            facecolor=weights_config['facecolor'],
            alpha=weights_config['alpha'],
            boxstyle=weights_config['boxstyle']
        )
    )

    # Ajustar o layout do gráfico
    subplot_config = config['visualization']['subplot_adjust']
    plt.subplots_adjust(
        left=subplot_config['left'],
        right=subplot_config['right'],
        bottom=subplot_config['bottom'],
        top=subplot_config['top']
    )
    
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
    5. Configuração dos pesos relativos uma única vez para os tipos de alimento.
    6. Cálculo das médias ponderadas das diferenças percentuais via `calculate_weighted_average_with_weights()`.
    7. Geração e exibição de um histograma usando a função `create_histogram()`.
    8. Cálculo e exibição das principais estatísticas com opção de exportação para CSV.
    9. Permite salvar o histograma como PNG e exibe links para download dos arquivos gerados.
    """

    # Configuração da página Streamlit
    st.set_page_config(page_title=config['ui']['page_title'], layout="wide")
    
    st.title(config['ui']['page_title'])

    # Criar duas colunas principais para a interface
    col1, col2 = st.columns([1, 3])  # Proporção de 1:3 entre as colunas

    with col1:
        st.header(config['ui']['analysis_config_header'])
        
        # Upload do arquivo Excel
        uploaded_file = st.file_uploader(
            config['ui']['file_uploader']['label'], 
            type=config['ui']['file_uploader']['allowed_types']
        )

        # Verificação inicial: se não houver arquivo, encerre a função
        if uploaded_file is None:
            st.warning("selecione o arquivo .XLSX para análise.")
            return  # Encerra a função principal se não houver arquivo carregado

        # Carregar e processar o arquivo Excel
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

            # Filtrar os dados e armazenar o resultado em `df_filtered`
            df_filtered = filter_data(df, operadores_selecionados, alimentos_selecionados, dietas_selecionadas, start_date, end_date)

            # Verificar se o DataFrame filtrado está vazio
            if df_filtered.empty:
                st.warning("Não há dados suficientes para análise com os filtros selecionados.")
                return  # Finaliza a função principal para evitar execuções subsequentes

            # Caso não esteja vazio, prosseguir
            st.success("Filtro aplicado com sucesso!")

            # Configuração dos pesos relativos para os tipos de alimentos - faz isso uma única vez
            st.subheader(config['ui']['food_weights_subheader'])
            tipos_alimentos = df[config['excel_columns']['tipo']].unique().tolist()
            pesos_relativos = {
                tipo: st.slider(
                    f"Peso para tipo de alimento '{tipo}':", 
                    min_value=config['slider']['min_value'],  # Valor mínimo definido no config.yaml
                    max_value=config['slider']['max_value'],  # Valor máximo definido no config.yaml
                    value=config['slider']['default_value'], 
                    step=config['slider']['step']  # Step definido no config.yaml
                ) for tipo in tipos_alimentos
            }

            # Opção para remover outliers
            remover_outliers = st.checkbox(
                config['ui']['remove_outliers']['label'],
                help=config['ui']['remove_outliers']['help']
            )

            # Botão para iniciar a análise
            iniciar_analise = st.button(config['ui']['generate_button'])

    with col2:
        # Apenas proceder com a análise se o botão for pressionado e se os dados estiverem carregados e filtrados
        if df is not None and iniciar_analise:
            st.header(config['ui']['results_header'])

            # Calcular a média ponderada das diferenças percentuais
            weighted_average_df = calculate_weighted_average_with_weights(df_filtered, pesos_relativos, config)

            if weighted_average_df is not None:
                # Criar e exibir o histograma com os dados filtrados
                fig = create_histogram(weighted_average_df, start_date, end_date, remover_outliers, pesos_relativos, config=config)
                st.pyplot(fig)

                # Adicionar opção para salvar o histograma
                st.markdown(save_histogram_as_image(fig), unsafe_allow_html=True)

                # Criar duas colunas para exibir as tabelas de estatísticas e pesos lado a lado
                col1, col2 = st.columns(2)

                # Exibir estatísticas na primeira coluna
                with col1:
                    st.subheader(config['ui']['statistics_title'])
                    stats_df = create_statistics_dataframe(weighted_average_df, remover_outliers, config=config)
                    st.write(stats_df)

                # Exibir pesos relativos na segunda coluna
                with col2:
                    st.subheader(config['ui']['food_weights_subheader'])
                    pesos_df = pd.DataFrame(list(pesos_relativos.items()), columns=['Tipo de Alimento', 'Peso Relativo'])
                    st.write(pesos_df)

                # Adicionar data de geração e opção para download dos arquivos CSV
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
