import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re

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

        operador_selecionado = st.selectbox('Escolha o Operador:', operadores)
        alimento_selecionado = st.selectbox('Escolha o Alimento:', alimentos)
        tipo_grafico = st.selectbox('Escolha o Tipo de Gráfico:', ['Boxplot', 'Histograma'])

        # Filtragem de Dados
        if operador_selecionado != 'Todos':
            df_operador = df[df['OPERADOR'] == operador_selecionado]
        else:
            df_operador = df

        if alimento_selecionado != 'Todos':
            df_operador = df_operador[df_operador['ALIMENTO'] == alimento_selecionado]

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
            st.write(f"**Com Outliers**: Média: {mean_with_outliers:.2f}, Mediana: {median_with_outliers:.2f}, Número de pontos: {total_points_with_outliers}")
            st.write(f"**Sem Outliers**: Média: {mean_no_outliers:.2f}, Mediana: {median_no_outliers:.2f}, Número de pontos: {total_points_no_outliers}")

            # Criação do Gráfico
            if st.button("Gerar Gráfico"):
                fig, ax = plt.subplots(figsize=(10, 6))
                fig.subplots_adjust(bottom=0.3)  # Adiciona margem inferior para evitar sobreposição da legenda

                # Texto da legenda em formato de tabela com tabulação corrigida
                legenda_texto = (
                    f"{'Estatística':<25}{'Com Outliers':<15}{'Sem Outliers':<15}\n"
                    f"{'-'*55}\n"
                    f"{'Média':<25}{mean_with_outliers:<15.2f}{mean_no_outliers:<15.2f}\n"
                    f"{'Mediana':<25}{median_with_outliers:<15.2f}{median_no_outliers:<15.2f}\n"
                    f"{'Total de pontos':<25}{total_points_with_outliers:<15}{total_points_no_outliers:<15}\n"
                    f"{'Outliers removidos':<25}{'':<15}{num_outliers:<15}"
                )
                
                if tipo_grafico == 'Boxplot':
                    ax.boxplot(df_operador_no_outliers, vert=False, showmeans=True, meanline=True)
                    ax.set_title(f'Boxplot de "{found_column}" - Operador: {operador_selecionado} - Alimento: {alimento_selecionado}')
                    ax.set_xlabel(found_column)
                    ax.grid(True)

                    # Adicionando a legenda
                    plt.figtext(0.1, 0.01, legenda_texto, ha='left', fontsize=10, family='monospace', bbox={"facecolor": "white", "alpha": 0.5, "pad": 5})

                elif tipo_grafico == 'Histograma':
                    ax.hist(df_operador_no_outliers, bins=15, edgecolor='black', alpha=0.7)
                    ax.set_title(f'Histograma de "{found_column}" - Operador: {operador_selecionado} - Alimento: {alimento_selecionado}')
                    ax.set_xlabel(found_column)
                    ax.set_ylabel('Frequência')
                    ax.grid(True)

                    # Adicionando a legenda
                    plt.figtext(0.1, 0.01, legenda_texto, ha='left', fontsize=10, family='monospace', bbox={"facecolor": "white", "alpha": 0.5, "pad": 5})

                # Renderizar o Gráfico no Streamlit
                st.pyplot(fig)

    else:
        st.error("Coluna 'DIFERENÇA (% MÓDULO)' não encontrada no arquivo Excel.")