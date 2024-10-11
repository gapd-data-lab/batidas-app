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

def load_and_process_data(uploaded_file):
    """
    Carrega e processa os dados do arquivo Excel.

    - Lê os dados do arquivo Excel, pulando as duas primeiras linhas, que podem conter metadados irrelevantes.
    - Remove a primeira coluna, que foi considerada irrelevante.
    - Verifica a presença da coluna 'DIFERENÇA (%)' e converte-a para valores numéricos.
    - Converte a coluna 'DATA' para o formato datetime para facilitar filtros posteriores.
    """
    df = pd.read_excel(uploaded_file, skiprows=2)
    df = df.iloc[:, 1:]  # Remover a primeira coluna irrelevante
    
    if 'DIFERENÇA (%)' not in df.columns:
        st.error("Coluna 'DIFERENÇA (%)' não encontrada no arquivo Excel.")
        return None

    df['DIFERENÇA (%)'] = pd.to_numeric(df['DIFERENÇA (%)'], errors='coerce')
    df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')
    
    return df

def calculate_weighted_average_with_weights(df, pesos_relativos):
    """
    Calcula a média ponderada das diferenças percentuais absolutas para cada batida,
    considerando os pesos definidos para cada tipo de alimento.

    - Acessa explicitamente as colunas 'PREVISTO (KG)', 'REALIZADO (KG)', e 'DIFERENÇA (%)' a partir de suas respectivas posições originais na planilha.
    - Agrupa os dados por 'COD. BATIDA' para calcular separadamente cada batida.
    - Converte as colunas relevantes para valores numéricos.
    - Calcula a diferença percentual absoluta para cada linha.
    - Ajusta o peso relativo pelo tipo de alimento e calcula a contribuição ponderada.
    - Calcula a média ponderada dividindo a soma das contribuições pelo total planejado para cada batida.

    Retorna um DataFrame com as médias ponderadas das diferenças percentuais absolutas para cada batida.
    """
    # Acessar explicitamente as colunas M, N e P
    df['PREVISTO (KG)'] = pd.to_numeric(df.iloc[:, 12], errors='coerce')  # Coluna M
    df['REALIZADO (KG)'] = pd.to_numeric(df.iloc[:, 13], errors='coerce')  # Coluna N
    df['DIFERENÇA (%)'] = pd.to_numeric(df.iloc[:, 14], errors='coerce')  # Coluna P
    df['DIFERENÇA (%) ABS'] = df['DIFERENÇA (%)'].abs()

    # Agrupar por 'COD. BATIDA' e calcular a média ponderada para cada batida
    weighted_averages = []
    for batida, group in df.groupby('COD. BATIDA'):
        # Ajustar a quantidade planejada com o peso relativo do tipo de alimento
        group['PESO RELATIVO'] = group['TIPO'].map(pesos_relativos)  # Atribuir o peso relativo baseado no tipo
        group['PESO AJUSTADO'] = group['PREVISTO (KG)'] * group['PESO RELATIVO']
        
        # Calcular a contribuição ponderada de cada ingrediente ajustada pelo peso relativo
        group['CONTRIBUIÇÃO'] = group['PESO AJUSTADO'] * (group['DIFERENÇA (%) ABS'] / 100)
        
        # Calcular a média ponderada para a batida atual
        total_planned_quantity = group['PESO AJUSTADO'].sum()
        weighted_average = (group['CONTRIBUIÇÃO'].sum() / total_planned_quantity) * 100 if total_planned_quantity > 0 else 0
        
        weighted_averages.append({'COD. BATIDA': batida, 'MÉDIA PONDERADA (%)': weighted_average})
    
    return pd.DataFrame(weighted_averages)

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

def create_histogram(df, title, start_date, end_date, remove_outliers=False):
    """
    Cria o histograma com base nos dados fornecidos e adiciona informações no rodapé.
    """
    fig, ax = plt.subplots(figsize=(12, 8))  # Aumentado a altura para acomodar o rodapé
    
    if remove_outliers:
        df = remove_outliers_from_df(df, 'MÉDIA PONDERADA (%)')
    
    # Calcular os limites para o eixo X
    data = df['MÉDIA PONDERADA (%)']
    data = data[data >= 0]  # Considerar apenas valores positivos
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
    
    # Criar o histograma
    n, bins, patches = ax.hist(data, bins=n_bins, range=(lower_bound, upper_bound), edgecolor='black')
    
    # Colorir as barras com escala de cores
    for patch, bin_value in zip(patches, bins[:-1]):
        if bin_value >= 3:
            color_intensity = min((bin_value - 3) / (upper_bound - 3), 1)  # Intensidade baseada na distância do valor 3
            patch.set_facecolor((1, 0, 0, color_intensity))  # Escala de vermelho
        else:
            color_intensity = min((3 - bin_value) / 3, 1)  # Intensidade baseada na proximidade do valor 0
            patch.set_facecolor((0, 1, 0, color_intensity))  # Escala de verde
    
    ax.set_xlabel('Média Ponderada da Diferença (%)')
    ax.set_ylabel('Frequência')
    ax.set_title(title)
    
    # Adicionar linha vertical no valor 3 com estilo tracejado
    # Adicionar linha de tolerância máxima
    ax.axvline(x=3, color='green', linestyle='--', linewidth=2, label='Tolerância Máxima (3%)')

    # Ajustar a posição e o estilo da legenda utilizando os mesmos parâmetros da tabela de pesos
    ax.legend(
        loc='upper right',
        fontsize=8,
        frameon=True,
        facecolor='lightgrey',
        edgecolor='black',
        fancybox=True,
        framealpha=0.5,
        bbox_to_anchor=(0.955, 0.95),  # Ajustando a posição para corresponder aos parâmetros da tabela de pesos
        bbox_transform=ax.transAxes
    )

    # Configurar grid
    ax.grid(axis='y', linestyle='--', linewidth=0.7)
    ax.set_axisbelow(True)  # Colocar o grid atrás das barras
    
    # Configurar ticks inteiros no eixo X
    ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=20, prune='both'))
    
    # Função para formatar os rótulos como inteiros
    def format_fn(tick_val, tick_pos):
        return int(tick_val)
    
    ax.xaxis.set_major_formatter(FuncFormatter(format_fn))
    
    # Adicionar informações sobre dados fora dos limites
    total_count = len(data)
    inside_count = ((data >= lower_bound) & (data <= upper_bound)).sum()
    outside_count = total_count - inside_count
    outside_percent = (outside_count / total_count) * 100
    
    ax.text(0.01, 0.99, f"Dados fora dos limites: {outside_count} ({outside_percent:.2f}%)",
            transform=ax.transAxes, verticalalignment='top', fontsize=10)
    
    # Configurar o fuso horário de Brasília
    brasilia_tz = pytz.timezone('America/Sao_Paulo')
    
    # Obter a data e hora atual em Brasília
    now_brasilia = datetime.datetime.now(brasilia_tz)
    
    # Adicionar informações no rodapé
    plt.figtext(0.5, 0.01, f"Período analisado: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}", 
                ha="center", fontsize=10)
    plt.figtext(0.01, 0.01, f"Total de batidas: {len(df)}", fontsize=10)
    plt.figtext(0.99, 0.01, f"Gerado em: {now_brasilia.strftime('%d/%m/%Y %H:%M')} (Horário de Brasília)", 
                ha="right", fontsize=10)
    
    # Ajustar o layout para acomodar o rodapé
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.1)
    
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
    # Configuração básica do Streamlit
    st.set_page_config(page_title="Análise de Dados - Histograma", layout="wide")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.header("Configurações da Análise")
        uploaded_file = st.file_uploader("Escolha o arquivo Excel (.xlsx)", type=["xlsx"])
        
        if uploaded_file:
            df = load_and_process_data(uploaded_file)
            
            if df is not None:
                # Coletar valores únicos dos campos relevantes para o filtro
                operadores = ['Todos'] + sorted(df['OPERADOR'].unique().tolist())
                alimentos = ['Todos'] + sorted(df['ALIMENTO'].unique().tolist())
                dietas = ['Todos'] + sorted(df['NOME'].unique().tolist())
                
                # Novos pesos relativos para tipos de alimentos
                st.subheader("Pesos Relativos dos Tipos de Alimento")
                tipos_alimentos = df['TIPO'].unique().tolist()
                pesos_relativos = {}
                
                # Slider para definir os pesos relativos de cada tipo de alimento
                for tipo in tipos_alimentos:
                    peso = st.slider(f"Peso para tipo de alimento '{tipo}':", min_value=0.0, max_value=10.0, value=1.0, step=0.1)
                    pesos_relativos[tipo] = peso

                # Filtros de data, alimentos, dietas e operadores
                min_date = df['DATA'].min().date()
                max_date = df['DATA'].max().date()
                start_date, end_date = st.date_input('Selecione o Período de Datas:', [min_date, max_date])
                
                alimentos_selecionados = st.multiselect('Escolha os Alimentos:', alimentos, default=['Todos'])
                dietas_selecionadas = st.multiselect('Escolha as Dietas:', dietas, default=['Todos'])
                operadores_selecionados = st.multiselect('Escolha os Operadores:', operadores, default=['Todos'])
                
                # Opção para remover outliers
                remover_outliers = st.checkbox("Remover outliers do histograma", help="Remover valores extremos que podem distorcer a análise.")
                
                # Botão para iniciar a análise
                iniciar_analise = st.button("Gerar")
    
    with col2:
        if uploaded_file and iniciar_analise and df is not None:
            st.header("Resultados da Análise - Confinamento")
            
            # Filtrar os dados de acordo com as seleções feitas pelo usuário
            df_filtered = filter_data(df, operadores_selecionados, alimentos_selecionados, dietas_selecionadas, start_date, end_date)
            
            if df_filtered.empty:
                st.warning("Não há dados suficientes para gerar a análise.")
            else:
                # Aplicar pesos relativos ao dataframe antes do cálculo da média ponderada
                df_filtered['PESO RELATIVO'] = df_filtered['TIPO'].map(pesos_relativos)
                df_filtered['PESO AJUSTADO'] = df_filtered['PREVISTO (KG)'] * df_filtered['PESO RELATIVO']
                
                # Calcular a média ponderada das diferenças percentuais considerando os pesos relativos
                weighted_average_df = calculate_weighted_average_with_weights(df_filtered, pesos_relativos)

                # Criar e exibir o histograma usando as médias ponderadas por batida
                fig = create_histogram(weighted_average_df, 
                                       f"Distribuição da Média Ponderada da Diferença Percentual ({'Sem' if remover_outliers else 'Com'} Outliers) - Confinamento",
                                       start_date,
                                       end_date,
                                       remover_outliers)
                
                # Ajustar o layout do gráfico para aumentar a área livre
                fig.subplots_adjust(right=0.95)
                
                # Adicionar pesos relativos no lado direito da área livre do gráfico, com alinhamento à direita e fundo acinzentado
                pesos_text = "Pesos relativos dos tipos de alimento:\n"
                pesos_text += "\n".join([f"{tipo:>20}: {peso:>4.1f}" for tipo, peso in pesos_relativos.items()])
                fig.text(0.9, 0.85, pesos_text, ha='right', fontsize=8, va='top', linespacing=1.5,
                        bbox=dict(facecolor='lightgrey', alpha=0.5, boxstyle='round,pad=0.5'))  # Adicionado fundo acinzentado

                
                st.pyplot(fig)
                
                # Adicionar opção para salvar o histograma
                st.markdown(save_histogram_as_image(fig), unsafe_allow_html=True)

                # Criação e exibição da tabela de estatísticas
                st.write("### Estatísticas Principais das Diferenças Percentuais")
                # Criar o DataFrame sem outliers
                weighted_average_df_no_outliers = remove_outliers_from_df(weighted_average_df, 'MÉDIA PONDERADA (%)')
                
                # Atualização do stats_data para incluir os dados com e sem outliers
                stats_data = {
                    'Estatística': [
                        'Número de Batidas', 
                        'Média (%)', 
                        'Mediana (%)',
                        'Diferença entre 3% e 5%',
                        'Diferença entre 5% e 7%',
                        'Diferença acima de 7%'
                    ],
                    'Com Outliers': [
                        len(weighted_average_df),
                        f"{weighted_average_df['MÉDIA PONDERADA (%)'].mean():.2f}",
                        f"{weighted_average_df['MÉDIA PONDERADA (%)'].median():.2f}",
                        ((weighted_average_df['MÉDIA PONDERADA (%)'] >= 3) & (weighted_average_df['MÉDIA PONDERADA (%)'] < 5)).sum(),
                        ((weighted_average_df['MÉDIA PONDERADA (%)'] >= 5) & (weighted_average_df['MÉDIA PONDERADA (%)'] < 7)).sum(),
                        (weighted_average_df['MÉDIA PONDERADA (%)'] >= 7).sum()
                    ],
                    'Sem Outliers': [
                        len(weighted_average_df_no_outliers),
                        f"{weighted_average_df_no_outliers['MÉDIA PONDERADA (%)'].mean():.2f}",
                        f"{weighted_average_df_no_outliers['MÉDIA PONDERADA (%)'].median():.2f}",
                        ((weighted_average_df_no_outliers['MÉDIA PONDERADA (%)'] >= 3) & (weighted_average_df_no_outliers['MÉDIA PONDERADA (%)'] < 5)).sum(),
                        ((weighted_average_df_no_outliers['MÉDIA PONDERADA (%)'] >= 5) & (weighted_average_df_no_outliers['MÉDIA PONDERADA (%)'] < 7)).sum(),
                        (weighted_average_df_no_outliers['MÉDIA PONDERADA (%)'] >= 7).sum()
                    ]
                }

                stats_df = pd.DataFrame(stats_data)
                st.write(stats_df)

                # Adicionar a tabela dos pesos relativos ao lado da tabela de estatísticas
                st.write("### Pesos Relativos dos Tipos de Alimento")
                pesos_df = pd.DataFrame(list(pesos_relativos.items()), columns=['Tipo de Alimento', 'Peso Relativo'])
                st.write(pesos_df)

                # Adicionar data de geração do relatório
                data_geracao = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                stats_df['Data de Geração'] = data_geracao
                pesos_df['Data de Geração'] = data_geracao

                # Concatenar dados das estatísticas e pesos relativos para o download
                combined_df = pd.concat([stats_df, pesos_df], ignore_index=True, sort=False)

                # Adicionar opção para salvar as estatísticas como CSV
                st.markdown(save_statistics_as_csv(combined_df), unsafe_allow_html=True)

                if remover_outliers:
                    st.info("Nota: Outliers foram removidos do histograma. Isso significa que valores extremamente altos, que podem distorcer a análise, foram excluídos para fornecer uma visão mais representativa dos dados.")

if __name__ == "__main__":
    main()