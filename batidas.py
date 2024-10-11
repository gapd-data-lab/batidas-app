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

def read_config(config_file='config.yaml'):
    """
    Lê o arquivo de configuração YAML e retorna um dicionário com as configurações.
    
    Args:
    config_file (str): Caminho para o arquivo de configuração. Padrão é 'config.yaml'.
    
    Returns:
    dict: Dicionário contendo todas as configurações do arquivo YAML.
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
    Carrega e processa os dados do arquivo Excel.

    Args:
    uploaded_file: O arquivo Excel carregado pelo usuário.

    Returns:
    DataFrame: O DataFrame processado ou None se houver um erro.
    """
    try:
        # Usar as configurações para ler o arquivo Excel
        df = pd.read_excel(uploaded_file, skiprows=config['analysis']['skip_rows'])
        
        # Remover a primeira coluna se especificado na configuração
        if config['analysis']['remove_first_column']:
            df = df.iloc[:, 1:]

        # Verificar se as colunas necessárias estão presentes
        required_columns = list(config['excel_columns'].values())
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Colunas ausentes no arquivo: {', '.join(missing_columns)}")

        # Converter colunas para os tipos apropriados
        df[config['excel_columns']['date']] = pd.to_datetime(df[config['excel_columns']['date']], errors='coerce')
        
        return df

    except Exception as e:
        st.error(f"Erro ao carregar ou processar o arquivo: {str(e)}")
        return None

def find_correct_columns(df, config):
    """
    Encontra os índices corretos das colunas necessárias no DataFrame.
    
    Args:
    df (DataFrame): O DataFrame contendo os dados.
    config (dict): O dicionário de configuração.

    Returns:
    dict: Um dicionário com os índices corretos das colunas.
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
    try:
        # Criar uma cópia do DataFrame para evitar SettingWithCopyWarning
        df = df.copy()
        
        # Converter colunas para numérico, permitindo números com casas decimais
        df['PREVISTO (KG)'] = pd.to_numeric(df[config['excel_columns']['previsto']], errors='coerce')
        df['REALIZADO (KG)'] = pd.to_numeric(df[config['excel_columns']['realizado']], errors='coerce')
        df['DIFERENÇA (%)'] = pd.to_numeric(df[config['excel_columns']['diferenca_percentual']], errors='coerce')
        df['DIFERENÇA (%) ABS'] = df['DIFERENÇA (%)'].abs()

        df['PESO RELATIVO'] = df[config['excel_columns']['tipo']].map(pesos_relativos)
        df['PESO AJUSTADO'] = df['PREVISTO (KG)'] * df['PESO RELATIVO']
        df['CONTRIBUIÇÃO'] = df['PESO AJUSTADO'] * (df['DIFERENÇA (%) ABS'] / 100)

        grouped = df.groupby(config['excel_columns']['cod_batida'])
        total_planned_quantity = grouped['PESO AJUSTADO'].sum()
        total_contribution = grouped['CONTRIBUIÇÃO'].sum()
        weighted_average = (total_contribution / total_planned_quantity) * 100
        
        weighted_averages = pd.DataFrame({
            config['excel_columns']['cod_batida']: total_planned_quantity.index,
            'MÉDIA PONDERADA (%)': weighted_average.fillna(0)
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
    Cria um DataFrame com as estatísticas principais das diferenças percentuais.

    Args:
    weighted_average_df (DataFrame): DataFrame contendo as médias ponderadas.
    remove_outliers (bool): Se True, remove outliers antes de calcular as estatísticas.

    Returns:
    DataFrame: DataFrame contendo as estatísticas principais.
    """
    # Criar uma cópia do DataFrame para não modificar o original
    df = weighted_average_df.copy()

    if remove_outliers:
        df = remove_outliers_from_df(df, 'MÉDIA PONDERADA (%)')

    # Calcular as estatísticas
    stats_data = {
        'Estatística': [
            'Número de Batidas', 
            'Média (%)', 
            'Mediana (%)',
            'Diferença entre 3% e 5%',
            'Diferença entre 5% e 7%',
            'Diferença acima de 7%'
        ],
        'Valor': [
            len(df),
            f"{df['MÉDIA PONDERADA (%)'].mean():.2f}",
            f"{df['MÉDIA PONDERADA (%)'].median():.2f}",
            ((df['MÉDIA PONDERADA (%)'] >= 3) & (df['MÉDIA PONDERADA (%)'] < 5)).sum(),
            ((df['MÉDIA PONDERADA (%)'] >= 5) & (df['MÉDIA PONDERADA (%)'] < 7)).sum(),
            (df['MÉDIA PONDERADA (%)'] >= 7).sum()
        ]
    }

    return pd.DataFrame(stats_data)

def remove_outliers_from_df(df, column):
    """
    Remove outliers dos dados, considerando apenas valores extremamente altos como outliers.

    - Calcula o primeiro e terceiro quartis (Q1 e Q3) e o intervalo interquartil (IQR).
    - Define o limite superior para identificar valores extremamente altos como outliers.
    - Retorna o DataFrame sem os valores que estão acima desse limite.
    """
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    upper_bound = Q3 + 1.5 * IQR
    return df[df[column] <= upper_bound]

def filter_data(df, operadores, alimentos, dietas, start_date, end_date):
    """
    Filtra os dados com base nos operadores, alimentos, dietas e período de datas.

    - Converte as datas de início e fim para o formato datetime.
    - Filtra o DataFrame para incluir apenas as linhas dentro do intervalo de datas selecionado.
    - Aplica filtros adicionais com base nos operadores, alimentos e dietas selecionados.
    
    Retorna o DataFrame filtrado de acordo com os critérios definidos.
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
    """
    q1, q3 = np.percentile(data, [25, 75])
    iqr = q3 - q1
    lower_bound = 0  # Limite inferior definido como 0 para valores positivos
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
    Colore as barras do histograma com uma escala de cores baseada nos valores dos bins.
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
    Cria o histograma com base nos dados fornecidos e adiciona informações no rodapé e pesos relativos.
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
    
    ax.set_xlabel('Média Ponderada da Diferença (%)')
    ax.set_ylabel('Frequência')
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
    Salva o histograma como uma imagem PNG e retorna um link para download.
    """
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)
    b64 = base64.b64encode(buf.getvalue()).decode()
    href = f'<a href="data:image/png;base64,{b64}" download="histograma.png">Download do Histograma (PNG)</a>'
    return href

def save_statistics_as_csv(stats_df):
    """
    Salva as estatísticas como um arquivo CSV e retorna um link para download.
    """
    csv = stats_df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="estatisticas.csv">Download das Estatísticas (CSV)</a>'
    return href

def main():
    # Carregar configurações
    config = read_config()

    # Configuração da página Streamlit
    st.set_page_config(page_title=config['ui']['page_title'], layout="wide")
    
    st.title(config['ui']['page_title'])

    # Criar duas colunas principais
    col1, col2 = st.columns([1, 3])  # Proporção de 1:3 entre as colunas

    with col1:
        st.header("Configurações da Análise")
        
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
                operadores_selecionados = st.multiselect(
                    config['ui']['multiselect']['operator_label'],
                    operadores,
                    default=['Todos']
                )

                # Seleção de alimentos
                alimentos = ['Todos'] + sorted(df[config['excel_columns']['alimento']].unique().tolist())
                alimentos_selecionados = st.multiselect(
                    config['ui']['multiselect']['food_label'],
                    alimentos,
                    default=['Todos']
                )

                # Seleção de dietas
                dietas = ['Todos'] + sorted(df[config['excel_columns']['nome']].unique().tolist())
                dietas_selecionadas = st.multiselect(
                    config['ui']['multiselect']['diet_label'],
                    dietas,
                    default=['Todos']
                )

                # Configuração de pesos relativos
                st.subheader(config['ui']['food_weights_subheader'])
                tipos_alimentos = df[config['excel_columns']['tipo']].unique().tolist()
                pesos_relativos = {}
                for tipo in tipos_alimentos:
                    peso = st.slider(
                        f"Peso para tipo de alimento '{tipo}':", 
                        min_value=0.0, 
                        max_value=10.0, 
                        value=config['analysis']['default_weight'], 
                        step=0.1
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
            st.header("Resultados da Análise")
            
            # Filtrar os dados
            df_filtered = filter_data(df, operadores_selecionados, alimentos_selecionados, dietas_selecionadas, start_date, end_date)
            
            if df_filtered.empty:
                st.warning("Não há dados suficientes para gerar a análise.")
            else:
                # Calcular a média ponderada
                weighted_average_df = calculate_weighted_average_with_weights(df_filtered, pesos_relativos, config)
                
                if weighted_average_df is not None:
                    # Criar e exibir o histograma
                    fig = create_histogram(weighted_average_df, start_date, end_date, remover_outliers, pesos_relativos)
                    st.pyplot(fig)
                    
                    # Adicionar opção para salvar o histograma
                    st.markdown(save_histogram_as_image(fig), unsafe_allow_html=True)

                    # Exibir estatísticas
                    st.subheader("Estatísticas Principais das Diferenças Percentuais")
                    stats_df = create_statistics_dataframe(weighted_average_df, remover_outliers)
                    st.write(stats_df)

                    # Exibir pesos relativos
                    st.subheader("Pesos Relativos dos Tipos de Alimento")
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