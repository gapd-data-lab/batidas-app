import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.ticker import MaxNLocator, FuncFormatter
import datetime
import io
import base64

def load_and_process_data(uploaded_file):
    """
    Carrega e processa os dados do arquivo Excel.
    """
    df = pd.read_excel(uploaded_file, skiprows=2)
    df = df.iloc[:, 1:]
    df.columns = df.columns.str.strip().str.upper()
    
    if 'DIFERENÇA (%)' not in df.columns:
        st.error("Coluna 'DIFERENÇA (%)' não encontrada no arquivo Excel.")
        return None

    df['DIFERENÇA (%)'] = pd.to_numeric(df['DIFERENÇA (%)'], errors='coerce')
    df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')
    
    return df

def remove_outliers_from_df(df, column):
    """
    Remove outliers usando o método do Intervalo Interquartil (IQR).
    """
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]

def filter_data(df, operadores, alimentos, dietas, start_date, end_date):
    """
    Filtra os dados com base nos operadores, alimentos, dietas e período de datas.
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

def calculate_statistics(df):
    """
    Calcula estatísticas relevantes dos dados.
    """
    stats = {
        'num_batidas': len(df),
        'media': df['DIFERENÇA (%)'].mean(),
        'mediana': df['DIFERENÇA (%)'].median(),
        'faixa_3_5': df['DIFERENÇA (%)'].abs().between(3, 5).sum(),
        'faixa_5_7': df['DIFERENÇA (%)'].abs().between(5, 7).sum(),
        'faixa_acima_7': df['DIFERENÇA (%)'].abs().gt(7).sum()
    }
    stats['percentual_3_5'] = (stats['faixa_3_5'] / stats['num_batidas']) * 100
    stats['percentual_5_7'] = (stats['faixa_5_7'] / stats['num_batidas']) * 100
    stats['percentual_acima_7'] = (stats['faixa_acima_7'] / stats['num_batidas']) * 100
    
    return stats

def create_color_scale(values):
    """
    Cria uma escala de cores em tons de cinza baseada na distância do zero.
    """
    max_distance = max(abs(values))
    return [mcolors.to_rgba('gray', alpha=abs(v)/max_distance) for v in values]

def create_histogram(df, title, remove_outliers=False):
    """
    Cria o histograma com base nos dados fornecidos.
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    if remove_outliers:
        df = remove_outliers_from_df(df, 'DIFERENÇA (%)')
    
    # Calcular os limites para o eixo X
    data = df['DIFERENÇA (%)']
    q1, q3 = np.percentile(data, [25, 75])
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    # Ajustar os limites para o número inteiro mais próximo
    lower_bound = np.floor(lower_bound)
    upper_bound = np.ceil(upper_bound)
    
    # Usar bins adaptativos
    bin_width = 2 * iqr * (len(data) ** (-1/3))  # Regra de Freedman-Diaconis
    n_bins = int((upper_bound - lower_bound) / bin_width)
    n_bins = min(n_bins, 100)  # Limitar o número máximo de bins
    
    # Criar o histograma
    n, bins, patches = ax.hist(data, bins=n_bins, range=(lower_bound, upper_bound), edgecolor='black')
    
    # Colorir as barras
    colors = create_color_scale(bins[:-1])
    for patch, color in zip(patches, colors):
        patch.set_facecolor(color)
    
    ax.set_xlabel('Diferença (%)')
    ax.set_ylabel('Frequência')
    ax.set_title(title)
    
    # Adicionar linha vertical no zero
    ax.axvline(x=0, color='green', linestyle='-', linewidth=2, label='Centro (0)')
    
    # Configurar grid
    ax.grid(axis='y', linestyle='--', linewidth=0.7)
    ax.set_axisbelow(True)  # Colocar o grid atrás das barras
    
    # Configurar ticks inteiros no eixo X
    ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=20, prune='both'))
    
    # Função para formatar os rótulos como inteiros
    def format_fn(tick_val, tick_pos):
        return int(tick_val)
    
    ax.xaxis.set_major_formatter(FuncFormatter(format_fn))
    
    # Colorir e ajustar os rótulos do eixo X
    for label in ax.get_xticklabels():
        try:
            tick_value = int(float(label.get_text().replace('−', '-')))
            if tick_value <= -4:
                label.set_color('red')
            elif -3 <= tick_value <= 3:
                label.set_color('green')
            elif tick_value >= 4:
                label.set_color('blue')
            else:
                label.set_color('black')
            
            # Destacar o eixo central (0)
            if tick_value == 0:
                label.set_color('darkgreen')
                label.set_fontweight('bold')
                label.set_fontsize(10)
            else:
                # Ajustar o tamanho da fonte para números pares e ímpares
                label.set_fontsize(12 if tick_value % 2 != 0 else 8)
            
        except ValueError:
            continue
    
    # Adicionar informações sobre dados fora dos limites
    total_count = len(data)
    inside_count = ((data >= lower_bound) & (data <= upper_bound)).sum()
    outside_count = total_count - inside_count
    outside_percent = (outside_count / total_count) * 100
    
    ax.text(0.01, 0.99, f"Dados fora dos limites: {outside_count} ({outside_percent:.2f}%)",
            transform=ax.transAxes, verticalalignment='top', fontsize=10)
    
    # Ajustar o layout para evitar sobreposição de rótulos
    plt.tight_layout()
    
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
    st.set_page_config(page_title="Análise de Dados - Histograma", layout="wide")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.header("Configurações da Análise")
        uploaded_file = st.file_uploader("Escolha o arquivo Excel (.xlsx)", type=["xlsx"])
        
        if uploaded_file:
            df = load_and_process_data(uploaded_file)
            
            if df is not None:
                operadores = ['Todos'] + sorted(df['OPERADOR'].unique().tolist())
                alimentos = ['Todos'] + sorted(df['ALIMENTO'].unique().tolist())
                dietas = ['Todos'] + sorted(df['NOME'].unique().tolist())
                
                min_date = df['DATA'].min().date()
                max_date = df['DATA'].max().date()
                start_date, end_date = st.date_input('Selecione o Período de Datas:', [min_date, max_date])
                
                alimentos_selecionados = st.multiselect('Escolha os Alimentos:', alimentos, default=['Todos'])
                dietas_selecionadas = st.multiselect('Escolha as Dietas:', dietas, default=['Todos'])
                operadores_selecionados = st.multiselect('Escolha os Operadores:', operadores, default=['Todos'])
                
                remover_outliers = st.checkbox("Remover outliers do histograma")
                
                iniciar_analise = st.button("Gerar")
    
    with col2:
        if uploaded_file and iniciar_analise and df is not None:
            st.header("Resultados da Análise - confinamento")
            
            df_filtered = filter_data(df, operadores_selecionados, alimentos_selecionados, dietas_selecionadas, start_date, end_date)
            
            if df_filtered.empty:
                st.warning("Não há dados suficientes para gerar a análise.")
            else:
                mean_diff_per_batida = df_filtered.groupby('COD. BATIDA')['DIFERENÇA (%)'].mean().reset_index()
                
                fig = create_histogram(mean_diff_per_batida, 
                                       f"Distribuição da Média da Diferença Percentual das Batidas ({'Sem' if remover_outliers else 'Com'} Outliers) - Confinamento",
                                       remover_outliers)
                st.pyplot(fig)
                
                # Adicionar opção para salvar o histograma
                st.markdown(save_histogram_as_image(fig), unsafe_allow_html=True)
                
                stats_com_outliers = calculate_statistics(mean_diff_per_batida)
                stats_sem_outliers = calculate_statistics(remove_outliers_from_df(mean_diff_per_batida, 'DIFERENÇA (%)'))
                
                # Criar DataFrame para a tabela de estatísticas
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
                        stats_com_outliers['num_batidas'],
                        f"{stats_com_outliers['media']:.2f}",
                        f"{stats_com_outliers['mediana']:.2f}",
                        stats_com_outliers['faixa_3_5'],
                        stats_com_outliers['faixa_5_7'],
                        stats_com_outliers['faixa_acima_7']
                    ],
                    'Percentual (%)': [
                        '-',
                        '-',
                        '-',
                        f"{stats_com_outliers['percentual_3_5']:.2f}%",
                        f"{stats_com_outliers['percentual_5_7']:.2f}%",
                        f"{stats_com_outliers['percentual_acima_7']:.2f}%"
                    ],
                    'Sem Outliers': [
                        stats_sem_outliers['num_batidas'],
                        f"{stats_sem_outliers['media']:.2f}",
                        f"{stats_sem_outliers['mediana']:.2f}",
                        '-',
                        '-',
                        '-'
                    ]
                }
                stats_df = pd.DataFrame(stats_data)
                
                # Estilizar a tabela para melhor visualização
                styled_stats_df = stats_df.style.set_table_styles([
                    {'selector': 'th', 'props': [('font-size', '14px'), ('text-align', 'center')]},
                    {'selector': 'td', 'props': [('font-size', '12px'), ('text-align', 'right'), ('padding', '8px')]},
                    {'selector': 'caption', 'props': [('caption-side', 'bottom')]},
                ]).set_properties(**{'width': '200px'}, subset=['Estatística']).set_properties(
                    **{'width': '150px'}, subset=['Com Outliers', 'Sem Outliers', 'Percentual (%)']
                )
                
                # Exibir a tabela de estatísticas estilizada
                st.write("### Estatísticas Principais das Diferenças Percentuais")
                st.write(styled_stats_df.to_html(), unsafe_allow_html=True)
                
                # Adicionar opção para salvar as estatísticas
                st.markdown(save_statistics_as_csv(stats_df), unsafe_allow_html=True)
                
                if remover_outliers:
                    st.info(f"Nota: Outliers foram removidos do histograma.")

if __name__ == "__main__":
    main()

# programa escrito com auxilio das LLM OpenAi GTP 4o e Anthropic Claude 3.5 sonnet
# data: 09 de outubro de 2024