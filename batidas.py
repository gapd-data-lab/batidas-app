import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
import io

# Configuração inicial da página
st.set_page_config(page_title="Análise de Dados - Boxplot e Histograma", layout="wide")

# Layout em colunas
col1, col2 = st.columns([1, 3])

# Coluna para o upload do arquivo e seleção dos parâmetros
with col1:
    st.header("Configurações da Análise")

    # Carregar o arquivo XLSX
    uploaded_file = st.file_uploader("Escolha o arquivo Excel (.xlsx)", type=["xlsx"])
    
    if uploaded_file:
        # Ler o arquivo Excel, descartando as duas primeiras linhas e a primeira coluna
        df = pd.read_excel(uploaded_file, skiprows=2)  # `skiprows=2` ignora as duas primeiras linhas
        df = df.iloc[:, 1:]  # Remove a primeira coluna que está vazia

        # Função para encontrar a coluna de interesse
        def find_column_flexible(df, target_column):
            target_words = re.findall(r'\w+', target_column.lower())
            for col in df.columns:
                col_words = re.findall(r'\w+', col.lower())
                if all(word in col_words for word in target_words):
                    return col
            return None

        found_column = find_column_flexible(df, "DIFERENÇA (% MÓDULO)")

        if found_column:
            # Limpeza dos Dados
            df_clean = df[found_column].dropna()
            df_clean = pd.to_numeric(df_clean, errors='coerce').dropna()

            # Criação de Listas para Seleção
            operadores = df['OPERADOR'].unique().tolist() + ['Todos']
            alimentos = df['ALIMENTO'].unique().tolist() + ['Todos']

            operadores_selecionados = st.multiselect('Escolha os Operadores:', operadores, default=['Todos'])
            alimentos_selecionados = st.multiselect('Escolha os Alimentos:', alimentos, default=['Todos'])
            tipo_grafico = st.selectbox('Escolha o Tipo de Gráfico:', ['Boxplot', 'Histograma'])

            # Botão para iniciar a análise
            iniciar_analise = st.button("Iniciar Análise")

# Coluna para exibir os gráficos e resultados
with col2:
    if uploaded_file and found_column and iniciar_analise:
        st.header("Resultados da Análise")

        # Filtragem de Dados
        if 'Todos' not in operadores_selecionados:
            df_operador = df[df['OPERADOR'].isin(operadores_selecionados)]
        else:
            df_operador = df

        if 'Todos' not in alimentos_selecionados:
            df_operador = df_operador[df_operador['ALIMENTO'].isin(alimentos_selecionados)]

        df_operador_clean = df_operador[found_column].dropna()
        df_operador_clean = pd.to_numeric(df_operador_clean, errors='coerce').dropna()

        # Identificação e Remoção de Outliers
        Q1 = df_operador_clean.quantile(0.25)
        Q3 = df_operador_clean.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        df_operador_no_outliers = df_operador_clean[(df_operador_clean >= lower_bound) & (df_operador_clean <= upper_bound)]

        # Cálculo das Estatísticas
        mean_with_outliers = df_operador_clean.mean()
        median_with_outliers = df_operador_clean.median()
        mean_no_outliers = df_operador_no_outliers.mean()
        median_no_outliers = df_operador_no_outliers.median()
        num_outliers = len(df_operador_clean) - len(df_operador_no_outliers)
        total_points_with_outliers = len(df_operador_clean)
        total_points_no_outliers = len(df_operador_no_outliers)

        # Verificação se há dados após a filtragem
        if len(df_operador_no_outliers) == 0:
            st.warning("Não há dados suficientes após a filtragem para gerar o gráfico.")
        else:
            # Mostrar algumas estatísticas básicas dos dados antes e depois da remoção dos outliers
            st.write("### Estatísticas dos Dados")
            st.table({
                'Estatística': ['Média', 'Mediana', 'Total de Pontos', 'Outliers Removidos'],
                'Com Outliers': [f"{mean_with_outliers:.2f}", f"{median_with_outliers:.2f}", total_points_with_outliers, '-'],
                'Sem Outliers': [f"{mean_no_outliers:.2f}", f"{median_no_outliers:.2f}", total_points_no_outliers, num_outliers]
            })

            # Criação do Gráfico
            fig, ax = plt.subplots(figsize=(10, 6))
            fig.subplots_adjust(bottom=0.3)

            operadores_str = ', '.join([str(op) for op in operadores_selecionados if op != 'Todos']) if 'Todos' not in operadores_selecionados else 'Todos'
            alimentos_str = ', '.join([str(al) for al in alimentos_selecionados if al != 'Todos']) if 'Todos' not in alimentos_selecionados else 'Todos'

            if tipo_grafico == 'Boxplot':
                ax.boxplot(df_operador_no_outliers, vert=False, showmeans=True, meanline=True)
                ax.set_title(f'Boxplot de "{found_column}" - Operadores: {operadores_str} - Alimentos: {alimentos_str}')
                ax.set_xlabel(found_column)
                ax.grid(True)

            elif tipo_grafico == 'Histograma':
                ax.hist(df_operador_no_outliers, bins=15, edgecolor='black', alpha=0.7)
                ax.set_title(f'Histograma de "{found_column}" - Operadores: {operadores_str} - Alimentos: {alimentos_str}')
                ax.set_xlabel(found_column)
                ax.set_ylabel('Frequência')
                ax.grid(True)

            # Renderizar o Gráfico no Streamlit
            st.pyplot(fig)

            # Adicionar a funcionalidade de download
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png')
            st.download_button(label="Baixar Gráfico", data=buffer, file_name="grafico.png", mime="image/png")

if uploaded_file and not found_column:
    st.error("Coluna 'DIFERENÇA (% MÓDULO)' não encontrada no arquivo Excel.")