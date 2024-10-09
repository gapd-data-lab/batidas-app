import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import re
import io
import datetime

def load_and_process_data(uploaded_file):
    """
    Carrega e processa os dados do arquivo Excel.
    Remove outliers usando o método do Intervalo Interquartil (IQR).
    """
    # Ler o arquivo Excel, descartando as duas primeiras linhas (cabeçalhos) e a primeira coluna (vazia)
    df = pd.read_excel(uploaded_file, skiprows=2)
    df = df.iloc[:, 1:]

    # Corrigir possíveis variações de nome de coluna
    df.columns = df.columns.str.strip().str.upper()

    # Converter a coluna 'DIFERENÇA (%)' para numérica e remover valores ausentes
    if 'DIFERENÇA (%)' in df.columns:
        df['DIFERENÇA (%)'] = pd.to_numeric(df['DIFERENÇA (%)'], errors='coerce').dropna()
    else:
        st.error("Coluna 'DIFERENÇA (%)' não encontrada no arquivo Excel.")
        return None, None, None, None

    # Cálculo do IQR para identificação de outliers
    Q1 = df['DIFERENÇA (%)'].quantile(0.25)
    Q3 = df['DIFERENÇA (%)'].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    # Criar um DataFrame sem outliers
    df_no_outliers = df[(df['DIFERENÇA (%)'] >= lower_bound) & (df['DIFERENÇA (%)'] <= upper_bound)]

    return df, df_no_outliers, lower_bound, upper_bound

def filter_data(df, df_no_outliers, operadores_selecionados, alimentos_selecionados, dietas_selecionadas, start_date, end_date):
    """
    Filtra os dados com base nos operadores, alimentos selecionados, dietas selecionadas e no período de datas.
    """
    # Converter a coluna 'DATA' para datetime, se ainda não estiver
    df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')
    df_no_outliers = df_no_outliers.copy()
    df_no_outliers['DATA'] = pd.to_datetime(df_no_outliers['DATA'], errors='coerce')

    # Filtrar por período de datas
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)  # Ajustar o final do dia
    df = df[(df['DATA'] >= start_date) & (df['DATA'] <= end_date)]
    df_no_outliers = df_no_outliers[(df_no_outliers['DATA'] >= start_date) & (df_no_outliers['DATA'] <= end_date)]

    # Filtrar por operadores, se não for selecionado 'Todos'
    if 'Todos' not in operadores_selecionados:
        df = df[df['OPERADOR'].isin(operadores_selecionados)]
    
    # Filtrar por alimentos, se não for selecionado 'Todos'
    if 'Todos' not in alimentos_selecionados:
        df = df[df['ALIMENTO'].isin(alimentos_selecionados)]
    
    # Filtrar por dietas, se não for selecionado 'Todos'
    if 'Todos' not in dietas_selecionadas:
        df = df[df['NOME'].isin(dietas_selecionadas)]
    
    # Filtrar o DataFrame sem outliers para corresponder aos filtros aplicados
    df_no_outliers_filtered = df_no_outliers[df_no_outliers.index.isin(df.index)]

    return df, df_no_outliers_filtered

def calculate_statistics(df_operador, df_no_outliers):
    """
    Calcula estatísticas relevantes dos dados, incluindo médias, medianas e contagens de outliers.
    """
    # Cálculo de médias e medianas
    mean_diff_with_outliers = df_operador['DIFERENÇA (%)'].abs().mean()
    median_diff_with_outliers = df_operador['DIFERENÇA (%)'].abs().median()
    mean_diff_no_outliers = df_no_outliers['DIFERENÇA (%)'].abs().mean()
    median_diff_no_outliers = df_no_outliers['DIFERENÇA (%)'].abs().median()
    
    # Contagem de outliers removidos
    num_outliers = len(df_operador) - len(df_no_outliers)

    # Cálculo de faixas de diferença percentual
    df_operador_abs = df_operador['DIFERENÇA (%)'].abs()
    faixa_3_5 = df_operador_abs[(df_operador_abs > 3) & (df_operador_abs <= 5)].count()
    faixa_5_7 = df_operador_abs[(df_operador_abs > 5) & (df_operador_abs <= 7)].count()
    faixa_7_9 = df_operador_abs[(df_operador_abs > 7) & (df_operador_abs <= 9)].count()
    faixa_acima_9 = df_operador_abs[df_operador_abs > 9].count()

    return {
        'mean_with_outliers': mean_diff_with_outliers,
        'median_with_outliers': median_diff_with_outliers,
        'mean_no_outliers': mean_diff_no_outliers,
        'median_no_outliers': median_diff_no_outliers,
        'num_outliers': num_outliers,
        'faixa_3_5': faixa_3_5,
        'faixa_5_7': faixa_5_7,
        'faixa_7_9': faixa_7_9,
        'faixa_acima_9': faixa_acima_9
    }

def create_graph(df_no_outliers, stats, operadores_str, alimentos_str, dietas_str):
    """
    Cria o histograma com base nos dados selecionados pelo usuário.
    Implementa uma escala de cinza nos bins, colore o eixo X por faixas específicas,
    e destaca o eixo central (0) com uma linha vertical sólida.
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.subplots_adjust(bottom=0.15)

    # Criação do histograma com escala de cinza
    bins = np.arange(df_no_outliers['DIFERENÇA (%)'].min(), df_no_outliers['DIFERENÇA (%)'].max() + 1, 1)
    hist, bin_edges = np.histogram(df_no_outliers['DIFERENÇA (%)'], bins=bins)
    
    # Criar uma escala de cinza baseada na distância do zero
    max_distance = max(abs(bin_edges[0]), abs(bin_edges[-1]))
    colors = [mcolors.to_rgba('gray', alpha=abs(b)/max_distance) for b in bin_edges[:-1]]
    
    # Plotar o histograma com cores em escala de cinza
    ax.bar(bin_edges[:-1], hist, width=1, align='edge', color=colors, edgecolor='black')
    
    # Atualização do título para incluir informação sobre outliers
    ax.set_title(f'Histograma de Diferenças Percentuais (Outliers Removidos)\nOperadores: {operadores_str} - Alimentos: {alimentos_str} - Dietas: {dietas_str}')
    ax.set_xlabel('Diferença (%)')
    ax.set_ylabel('QTDE DE LOTES BATIDOS')
    ax.yaxis.get_major_locator().set_params(integer=True)
    ax.grid(True, linestyle='--', linewidth=0.7, which='both')
    ax.minorticks_on()
    ax.grid(True, which='minor', linestyle=':', linewidth=0.5)
    
    # Configurar os ticks do eixo X manualmente
    ax.set_xticks(bin_edges)
    ax.set_xticklabels([f"{x:.0f}" for x in bin_edges], fontsize=8)
    
    # Colorir os rótulos do eixo X baseado nas faixas especificadas
    for tick in ax.get_xticklabels():
        tick_value = float(tick.get_text())
        if tick_value <= -4:
            tick.set_color('red')
        elif -3 <= tick_value <= 3:
            tick.set_color('green')
        elif tick_value >= 4:
            tick.set_color('blue')
        else:
            tick.set_color('black')  # Para valores entre -4 e -3, e entre 3 e 4
        
        # Destacar o eixo central (0)
        if tick_value == 0:
            tick.set_color('darkgreen')
            tick.set_fontweight('bold')
            tick.set_fontsize(10)
    
    # Adicionar uma linha vertical sólida no eixo 0
    ax.axvline(x=0, color='darkgreen', linewidth=1.5, zorder=5)
    
    # Manter os rótulos sem rotação
    plt.setp(ax.get_xticklabels(), rotation=0, ha='center')
    return fig

def main():
    # Configuração da página Streamlit
    st.set_page_config(page_title="Análise de Dados - Histograma", layout="wide")

    # Divisão da interface em duas colunas
    col1, col2 = st.columns([1, 3])

    with col1:
        st.header("Configurações da Análise")
        # Upload do arquivo Excel
        uploaded_file = st.file_uploader("Escolha o arquivo Excel (.xlsx)", type=["xlsx"])
        
        if uploaded_file:
            # Carregar e processar os dados
            df, df_no_outliers, lower_bound, upper_bound = load_and_process_data(uploaded_file)

            if df is not None:
                # Preparar listas de seleção para operadores, alimentos e dietas
                operadores = sorted(df['OPERADOR'].unique().tolist())
                operadores.insert(0, 'Todos')
                alimentos = sorted(df['ALIMENTO'].unique().tolist())
                alimentos.insert(0, 'Todos')
                dietas = sorted(df['NOME'].unique().tolist())
                dietas.insert(0, 'Todos')

                # Widgets de seleção para o usuário
                min_date = df['DATA'].min().date()
                max_date = df['DATA'].max().date()
                try:
                    start_date, end_date = st.date_input('Selecione o Período de Datas:', [min_date, max_date])
                except ValueError:
                    st.warning("Por favor, selecione um intervalo de datas válido.")
                    st.stop()

                alimentos_selecionados = st.multiselect('Escolha os Alimentos:', alimentos, default=['Todos'])
                dietas_selecionadas = st.multiselect('Escolha as Dietas:', dietas, default=['Todos'])
                operadores_selecionados = st.multiselect('Escolha os Operadores:', operadores, default=['Todos'])

                # Checkbox para remover outliers do histograma de médias das diferenças percentuais
                remover_outliers = st.checkbox("Remover outliers do histograma")

                iniciar_analise = st.button("Gerar")

    with col2:
        if uploaded_file and iniciar_analise and df is not None:
            st.header("Resultados da Análise - confinamento SJudas")

            # Filtrar os dados com base nas seleções do usuário
            df_operador, df_no_outliers_filtered = filter_data(df, df_no_outliers, operadores_selecionados, alimentos_selecionados, dietas_selecionadas, start_date, end_date)

            if df_operador.empty:
                st.warning("Não há dados suficientes para gerar a análise.")
            else:
                # Calcular a média das diferenças percentuais para cada batida
                mean_diff_per_batida = df_operador.groupby('COD. BATIDA')['DIFERENÇA (%)'].mean().reset_index()

                # Remover outliers, se necessário
                if remover_outliers:
                    Q1 = mean_diff_per_batida['DIFERENÇA (%)'].quantile(0.25)
                    Q3 = mean_diff_per_batida['DIFERENÇA (%)'].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    mean_diff_filtered = mean_diff_per_batida[(mean_diff_per_batida['DIFERENÇA (%)'] >= lower_bound) & (mean_diff_per_batida['DIFERENÇA (%)'] <= upper_bound)]
                else:
                    mean_diff_filtered = mean_diff_per_batida

                # Gerar o histograma da média das diferenças percentuais com escala de cinza
                fig, ax = plt.subplots(figsize=(10, 6))
                bins = np.linspace(mean_diff_filtered['DIFERENÇA (%)'].min(), mean_diff_filtered['DIFERENÇA (%)'].max(), 20)
                hist, bin_edges = np.histogram(mean_diff_filtered['DIFERENÇA (%)'], bins=bins)

                # Definir cores baseadas na distância ao valor 0 (escala de cinza correta)
                max_distance = max(abs(bin_edges[0]), abs(bin_edges[-1]))
                colors = [mcolors.to_rgba('gray', alpha=(abs(b) / max_distance)) for b in bin_edges[:-1]]

                # Plotar o histograma com a escala de cinza corrigida
                ax.bar(bin_edges[:-1], hist, width=np.diff(bin_edges), align='edge', color=colors, edgecolor='black')
                ax.set_xlabel('Média da Diferença (%)')
                ax.set_ylabel('Frequência')
                ax.set_title('Histograma da Média da Diferença Percentual de Todas as Batidas')

                # Inserir o novo título do gráfico
                if remover_outliers:
                    ax.set_title('Distribuição da Média da Diferença Percentual das Batidas (Sem Outliers) - Confinamento SJudas', fontsize=14)
                else:
                    ax.set_title('Distribuição da Média da Diferença Percentual das Batidas (Com Outliers) - Confinamento SJudas', fontsize=14)

                # Adicionar uma linha vertical verde no valor 0 do eixo X
                ax.axvline(x=0, color='green', linestyle='-', linewidth=2, label='Centro (0)')
                
                # Configurar as grades principais e secundárias
                ax.grid(axis='y', linestyle='--', linewidth=0.7, which='major')
                ax.grid(axis='y', linestyle=':', linewidth=0.5, which='minor')
                ax.minorticks_on()  # Ativar os ticks menores para uma grade mais detalhada

                # Definir os ticks do eixo X, incluindo números ímpares
                min_bin, max_bin = int(np.floor(mean_diff_filtered['DIFERENÇA (%)'].min())), int(np.ceil(mean_diff_filtered['DIFERENÇA (%)'].max()))
                xticks = list(range(min_bin, max_bin + 1))  # Incluir todos os valores inteiros no intervalo

                # Aplicar os ticks ao eixo X
                ax.set_xticks(xticks)

                # Customizar os rótulos do eixo X
                for label in ax.get_xticklabels():
                    try:
                        tick_value = float(label.get_text().replace('−', '-'))  # Corrigir representação do sinal negativo
                        # Aplicar cor baseada no valor do tick
                        if tick_value <= -4:
                            label.set_color('red')
                        elif -3 <= tick_value <= 3:
                            label.set_color('green')
                        elif tick_value >= 4:
                            label.set_color('blue')

                        # Se o valor for ímpar, aumentar a fonte, caso contrário, diminuir a fonte
                        if int(tick_value) % 2 != 0:
                            label.set_fontsize(12)  # Fonte maior para números ímpares
                        else:
                            label.set_fontsize(8)   # Fonte menor para números pares
                    except ValueError:
                        # Caso haja um rótulo que não seja numérico, ignorar (ex. vazio)
                        continue

                st.pyplot(fig)

                # Calcular estatísticas principais
                num_batidas = len(mean_diff_per_batida)
                media_com_outliers = mean_diff_per_batida['DIFERENÇA (%)'].mean()
                mediana_com_outliers = mean_diff_per_batida['DIFERENÇA (%)'].median()
                num_batidas_sem_outliers = len(mean_diff_filtered)
                media_sem_outliers = mean_diff_filtered['DIFERENÇA (%)'].mean()
                mediana_sem_outliers = mean_diff_filtered['DIFERENÇA (%)'].median()

                # Contagem de batidas em diferentes faixas de diferença
                faixa_3_5 = mean_diff_per_batida['DIFERENÇA (%)'].abs().between(3, 5).sum()
                faixa_5_7 = mean_diff_per_batida['DIFERENÇA (%)'].abs().between(5, 7).sum()
                faixa_acima_7 = mean_diff_per_batida['DIFERENÇA (%)'].abs().gt(7).sum()

                # Percentual de batidas em cada faixa
                percentual_3_5 = (faixa_3_5 / num_batidas) * 100
                percentual_5_7 = (faixa_5_7 / num_batidas) * 100
                percentual_acima_7 = (faixa_acima_7 / num_batidas) * 100

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
                        num_batidas, 
                        f"{media_com_outliers:.2f}", 
                        f"{mediana_com_outliers:.2f}",
                        faixa_3_5,
                        faixa_5_7,
                        faixa_acima_7
                    ],
                    'Percentual (%)': [
                        '-', 
                        '-', 
                        '-',
                        f"{percentual_3_5:.2f}%",
                        f"{percentual_5_7:.2f}%",
                        f"{percentual_acima_7:.2f}%"
                    ],
                    'Sem Outliers': [
                        num_batidas_sem_outliers, 
                        f"{media_sem_outliers:.2f}", 
                        f"{mediana_sem_outliers:.2f}",
                        '-',  # Não calculado para sem outliers
                        '-',  # Não calculado para sem outliers
                        '-'   # Não calculado para sem outliers
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

                # Adicionando nota explicativa sobre outliers, se necessário
                if remover_outliers:
                    st.info(f"Nota: Outliers foram removidos do histograma.")

if __name__ == "__main__":
    main()