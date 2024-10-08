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

def filter_data(df, df_no_outliers, operadores_selecionados, alimentos_selecionados, start_date, end_date):
    """
    Filtra os dados com base nos operadores, alimentos selecionados e no período de datas.
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

def create_graph(df_no_outliers, stats, operadores_str, alimentos_str):
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
    ax.set_title(f'Histograma de Diferenças Percentuais (Outliers Removidos)\nOperadores: {operadores_str} - Alimentos: {alimentos_str}')
    ax.set_xlabel('Diferença (%)')
    ax.set_ylabel('QTDE DE LOTES BATIDOS')
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
    """
    Função principal que coordena o fluxo do programa e a interface do usuário.
    """
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
                # Preparar listas de seleção para operadores e alimentos
                operadores = sorted(df['OPERADOR'].unique().tolist())
                operadores.insert(0, 'Todos')
                alimentos = sorted(df['ALIMENTO'].unique().tolist())
                alimentos.insert(0, 'Todos')

                # Widgets de seleção para o usuário
                operadores_selecionados = st.multiselect('Escolha os Operadores:', operadores, default=['Todos'])
                alimentos_selecionados = st.multiselect('Escolha os Alimentos:', alimentos, default=['Todos'])

                # Widget de seleção de período de datas
                min_date = df['DATA'].min().date()
                max_date = df['DATA'].max().date()
                try:
                    start_date, end_date = st.date_input('Selecione o Período de Datas:', [min_date, max_date])
                except ValueError:
                    st.warning("Por favor, selecione um intervalo de datas válido.")
                    st.stop()

                iniciar_analise = st.button("Gerar")

    with col2:
        if uploaded_file and iniciar_analise and df is not None:
            st.header("Resultados da Análise - confinamento SJudas")

            # Filtrar os dados com base nas seleções do usuário
            df_operador, df_no_outliers_filtered = filter_data(df, df_no_outliers, operadores_selecionados, alimentos_selecionados, start_date, end_date)

            if df_operador.empty:
                st.warning("Não há dados suficientes para gerar a análise.")
            else:
                if df_no_outliers_filtered.empty:
                    st.warning("Não há dados suficientes sem outliers para gerar a análise.")
                else:
                    stats = calculate_statistics(df_operador, df_no_outliers_filtered)

                    operadores_str = ', '.join([str(op) for op in operadores_selecionados if op != 'Todos']) if 'Todos' not in operadores_selecionados else 'Todos'
                    alimentos_str = ', '.join([str(al) for al in alimentos_selecionados if al != 'Todos']) if 'Todos' not in alimentos_selecionados else 'Todos'

                    fig = create_graph(df_no_outliers_filtered, stats, operadores_str, alimentos_str)
                    
                    st.pyplot(fig)

                    # Adicionando nota explicativa sobre outliers
                    st.info(f"Nota: O histograma acima não inclui outliers. Foram removidos {stats['num_outliers']} outliers para esta análise.")

                    buffer = io.BytesIO()
                    fig.savefig(buffer, format='png')
                    st.download_button(label="Baixar Gráfico", data=buffer, file_name="grafico.png", mime="image/png")

                    st.write("### Estatísticas das Diferenças Percentuais em Módulo")
                    
                    # Criando o DataFrame com os dados da tabela
                    df_stats = pd.DataFrame({
                        'Estatística': [
                            'Média (Com Outliers - valor em %)', 
                            'Mediana (Com Outliers -  valor em %)', 
                            'Média (Sem Outliers - valor em %)', 
                            'Mediana (Sem Outliers - valor em %)', 
                            'Outliers Removidos', 
                            'Diferença > 3% e <= 5%', 
                            'Diferença > 5% e <= 7%', 
                            'Diferença > 7% e <= 9%', 
                            'Diferença > 9%', 
                            'Total de Pontos'
                        ],
                        'Valor': [
                            f"{stats['mean_with_outliers']:.2f}",
                            f"{stats['median_with_outliers']:.2f}",
                            f"{stats['mean_no_outliers']:.2f}",
                            f"{stats['median_no_outliers']:.2f}",
                            f"{stats['num_outliers']}",
                            f"{stats['faixa_3_5']}",
                            f"{stats['faixa_5_7']}",
                            f"{stats['faixa_7_9']}",
                            f"{stats['faixa_acima_9']}",
                            f"{len(df_operador)}"
                        ],
                        'Percentual (%)': [
                            '',
                            '',
                            '',
                            '',
                            '',
                            f"{(stats['faixa_3_5'] / len(df_operador)) * 100:.2f}",
                            f"{(stats['faixa_5_7'] / len(df_operador)) * 100:.2f}",
                            f"{(stats['faixa_7_9'] / len(df_operador)) * 100:.2f}",
                            f"{(stats['faixa_acima_9'] / len(df_operador)) * 100:.2f}",
                            "100.00"
                        ]
                    })

                    # Aplicando o estilo CSS para alinhar as colunas à direita
                    st.markdown(
                        df_stats.style.set_properties(**{'text-align': 'left'}, subset=['Estatística'])
                                .set_properties(**{'text-align': 'right'}, subset=['Valor', 'Percentual (%)'])
                                .to_html(), unsafe_allow_html=True
                    )

if __name__ == "__main__":
    main()