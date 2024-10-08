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

        # Tratamento dos dados
        # Certificar-se de que a coluna 'DIFERENÇA (%)' seja numérica e limpar valores ausentes
        df['DIFERENÇA (%)'] = pd.to_numeric(df['DIFERENÇA (%)'], errors='coerce').dropna()

        # Remoção de outliers usando o método IQR
        Q1 = df['DIFERENÇA (%)'].quantile(0.25)
        Q3 = df['DIFERENÇA (%)'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        df = df[(df['DIFERENÇA (%)'] >= lower_bound) & (df['DIFERENÇA (%)'] <= upper_bound)]

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
    if uploaded_file and iniciar_analise:
        st.header("Resultados da Análise")

        # Filtragem de Dados
        if 'Todos' not in operadores_selecionados:
            df_operador = df[df['OPERADOR'].isin(operadores_selecionados)]
        else:
            df_operador = df

        if 'Todos' not in alimentos_selecionados:
            df_operador = df_operador[df_operador['ALIMENTO'].isin(alimentos_selecionados)]

        # Verificação se há dados após a filtragem
        if df_operador.empty:
            st.warning("Não há dados suficientes para gerar a análise.")
        else:
            # Cálculo das Estatísticas das Diferenças Percentuais em Módulo
            mean_diff = df_operador['DIFERENÇA (%)'].abs().mean()
            median_diff = df_operador['DIFERENÇA (%)'].abs().median()

            # Mostrar algumas estatísticas básicas dos dados
            st.write("### Estatísticas das Diferenças Percentuais em Módulo")
            st.table({
                'Estatística': ['Média', 'Mediana'],
                'Valor': [f"{mean_diff:.2f}", f"{median_diff:.2f}"]
            })

            # Criação do Gráfico
            fig, ax = plt.subplots(figsize=(10, 6))
            fig.subplots_adjust(bottom=0.3)

            operadores_str = ', '.join([str(op) for op in operadores_selecionados if op != 'Todos']) if 'Todos' not in operadores_selecionados else 'Todos'
            alimentos_str = ', '.join([str(al) for al in alimentos_selecionados if al != 'Todos']) if 'Todos' not in alimentos_selecionados else 'Todos'

            if tipo_grafico == 'Boxplot':
                ax.boxplot(df_operador['DIFERENÇA (%)'], vert=False, showmeans=True, meanline=True)
                ax.set_title(f'Boxplot de Diferenças Percentuais em Módulo - Operadores: {operadores_str} - Alimentos: {alimentos_str}')
                ax.set_xlabel('Diferença (%)')
                ax.grid(True)

            elif tipo_grafico == 'Histograma':
                ax.hist(df_operador['DIFERENÇA (%)'], bins=15, edgecolor='black', alpha=0.7)
                ax.set_title(f'Histograma de Diferenças Percentuais em Módulo - Operadores: {operadores_str} - Alimentos: {alimentos_str}')
                ax.set_xlabel('Diferença (%)')
                ax.set_ylabel('Frequência')
                ax.grid(True)

            # Renderizar o Gráfico no Streamlit
            st.pyplot(fig)

            # Adicionar a funcionalidade de download
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png')
            st.download_button(label="Baixar Gráfico", data=buffer, file_name="grafico.png", mime="image/png")

if uploaded_file and 'DIFERENÇA (%)' not in df.columns:
    st.error("Coluna 'DIFERENÇA (%)' não encontrada no arquivo Excel.")