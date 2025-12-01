# Importação das bibliotecas
import streamlit as st
import pandas as pd
import time
import plotly.express as px
import plotly.graph_objects as go
import gc
import psutil
import os

# 🔄 COMPARTILHAR DADOS ENTRE PÁGINAS
@st.cache_data(show_spinner=False, ttl=None)
def carregar_dados():
    # Especificar tipos de dados para otimização de memória
    dtypes = {
        'DIREC': 'category',
        'MUNICÍPIO': 'category', 
        'ESCOLA': 'category',
        'INEP ESCOLA': 'string',
        'ETAPA_RESUMIDA': 'category',
        'SÉRIE': 'category',
        '1B_Notas Lancadas': 'float32', 
        '1B_Notas Nao Lancadas': 'float32', 
        '2B_Notas Lancadas': 'float32', 
        '2B_Notas Nao Lancadas': 'float32', 
        '3B_Notas Lancadas': 'float32', 
        '3B_Notas Nao Lancadas': 'float32', 
        '4B_Notas Lancadas': 'float32',
        '4B_Notas Nao Lancadas': 'float32'
    }
    
    df = pd.read_parquet('dados_tratados/df_escola.parquet')
    
    # normalizações simples
    df['INEP ESCOLA'] = df['INEP ESCOLA'].astype(str).str.strip()
    df['ESCOLA'] = df['ESCOLA'].astype(str).str.strip()
    # pré-criar a coluna formatada uma vez
    df['ESCOLA_FORMATADA'] = df['ESCOLA'] + " (cód. Inep: " + df['INEP ESCOLA'] + ")"

    gc.collect() # Forçar limpeza de memória após carregar os dados
    return df


# CONFIGURAÇÕES DA PÁGINA
st.set_page_config(page_title="Lançamento de Notas", 
                   layout="wide",
                   page_icon="📈")
st.cache_data.clear()

# Carregar os dados
df = carregar_dados()


# FILTROS
# Inicializar session state para filtros se não existir
if 'filtro_direc' not in st.session_state:
    st.session_state.filtro_direc = 'Todas'
if 'filtro_municipio' not in st.session_state:
    st.session_state.filtro_municipio = 'Todos'
if 'filtro_escola' not in st.session_state:
    st.session_state.filtro_escola = 'Todas'


# Sidebar com os filtros
st.sidebar.title("Filtros")

# 1. Escolher a DIREC
direc_options = ['Todas'] + sorted(df['DIREC'].dropna().unique().tolist())
selected_direc = st.sidebar.selectbox("Selecione a DIREC:",
                                      options=direc_options,
                                      index=direc_options.index(st.session_state.filtro_direc))

# Atualizar session state e resetar filtros dependentes se mudou
if selected_direc != st.session_state.filtro_direc:
    st.session_state.filtro_direc = selected_direc
    st.session_state.filtro_municipio = 'Todos'
    st.session_state.filtro_escola = 'Todas'

# 2. Escolher o Município (usando cache para opções)
def get_municipio_options(_df, direc):
    if direc != 'Todas':
        df_temp = _df[_df['DIREC'] == direc]
    else:
        df_temp = _df
    return ['Todos'] + sorted(df_temp['MUNICÍPIO'].dropna().unique().tolist())

municipio_options = get_municipio_options(df, selected_direc)
selected_municipio = st.sidebar.selectbox("Selecione o Município:",
                                          options=municipio_options,
                                          index=municipio_options.index(st.session_state.filtro_municipio))

# Atualizar session state e resetar filtro dependente se mudou
if selected_municipio != st.session_state.filtro_municipio:
    st.session_state.filtro_municipio = selected_municipio
    st.session_state.filtro_escola = 'Todas'

# 3. Escolher a Escola (usando cache para opções)
def get_escola_options(_df, direc, municipio):
    df_temp = _df
    if direc != 'Todas':
        df_temp = df_temp[df_temp['DIREC'] == direc]
    if municipio != 'Todos':
        df_temp = df_temp[df_temp['MUNICÍPIO'] == municipio]
    
    df_temp['ESCOLA_FORMATADA'] = (
        df_temp['ESCOLA'].astype(str) + " (cód. Inep: " + df_temp['INEP ESCOLA'].astype(str) + ")"
    )
    return ['Todas'] + sorted(df_temp['ESCOLA_FORMATADA'].dropna().unique().tolist())

escola_options = get_escola_options(df, selected_direc, selected_municipio)
selected_escola_formatada = st.sidebar.selectbox("Selecione a Escola:",
                                                 options=escola_options,
                                                 index=escola_options.index(st.session_state.filtro_escola))

# Atualizar session state
if selected_escola_formatada != st.session_state.filtro_escola:
    st.session_state.filtro_escola = selected_escola_formatada

# APLICAR TODOS OS FILTROS DE UMA VEZ (COM CACHE)
def aplicar_filtros(_df, direc, municipio, escola):
    df_filtrado = _df
    
    if direc != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['DIREC'] == direc]
    
    if municipio != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['MUNICÍPIO'] == municipio]
    
    # Criar coluna formatada para escolas (apenas se necessário)
    if escola != 'Todas' or 'ESCOLA_FORMATADA' not in df_filtrado.columns:
        df_filtrado['ESCOLA_FORMATADA'] = (
            df_filtrado['ESCOLA'].astype(str) + " (cód. Inep: " + df_filtrado['INEP ESCOLA'].astype(str) + ")"
        )
    
    if escola != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['ESCOLA_FORMATADA'] == escola]
    
    return df_filtrado

df_filtered = aplicar_filtros(df, selected_direc, selected_municipio, selected_escola_formatada)

gc.collect() # Forçar coleta de lixo para liberar memória

# Botão para limpar todos os filtros
def resetar_filtros():
    st.session_state.filtro_direc = 'Todas'
    st.session_state.filtro_municipio = 'Todos'
    st.session_state.filtro_escola = 'Todas'

if st.sidebar.button("🔄 Limpar Todos os Filtros"):
    resetar_filtros()
    st.rerun()


# CONFIGURAÇÕES DA PÁGINA

                                                    # 1. Lançamento de Notas
# Imagem do cabeçalho
st.image("images/logos.png", width=1700)

st.write("")

st.title("📈 Lançamento de Notas")

st.markdown("""
            Os dados apresentados nessa aplicação são dos estudantes dos **Anos Finais do Ensino Fundamental e do Ensino Médio**, somente para os **componentes curriculares que fazem parte da Base Nacional Comum Curricular (BNCC)**.
            """)

st.write("")

st.markdown("""
            **⏱️ Última atualização**:  dados extraídos do SIGEduc em 28/11/2025.
            """)

st.write("")

st.markdown("Utilize os filtros no menu lateral para selecionar DIREC, Município e Escola específicos.")


st.write("")

# Análise de Lançamento de Notas

# Total de registros de notas (lançadas + não lançadas)
total_registros = (df_filtered['1B_Notas Nao Lancadas'].sum()) + (df_filtered['1B_Notas Lancadas'].sum())

# NOTAS NÃO LANÇADAS
# Calcular os percentuais de notas não lançadas
perc_nao_1bim = ((df_filtered['1B_Notas Nao Lancadas'].sum()) / total_registros * 100).round(1)
perc_nao_2bim = ((df_filtered['2B_Notas Nao Lancadas'].sum()) / total_registros * 100).round(1)
perc_nao_3bim = ((df_filtered['3B_Notas Nao Lancadas'].sum()) / total_registros * 100).round(1)
perc_nao_4bim = ((df_filtered['4B_Notas Nao Lancadas'].sum()) / total_registros * 100).round(1)


# Mostrar métricas detalhadas de notas não lançadas
st.markdown("**❌ Notas Não Lançadas:**")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "1º Bimestre", 
        f"{(df_filtered['1B_Notas Nao Lancadas'].sum()):,}", 
        f"{perc_nao_1bim}% faltantes",
        delta_color="inverse"
    )

with col2:
    st.metric(
        "2º Bimestre", 
        f"{(df_filtered['2B_Notas Nao Lancadas'].sum()):,}", 
        f"{perc_nao_2bim}% faltantes",
        delta_color="inverse" 
    )

with col3:
    st.metric(
        "3º Bimestre", 
        f"{(df_filtered['3B_Notas Nao Lancadas'].sum()):,}", 
        f"{perc_nao_3bim}% faltantes",
        delta_color="inverse"
    )

# Criar o df_nan com os percentuais calculados de notas não lançadas
df_nan = pd.DataFrame({
    'Bimestre': ['1º Bimestre', '2º Bimestre', '3º Bimestre'],
    'Notas Faltantes': [
        (df_filtered['1B_Notas Nao Lancadas'].sum()), 
        (df_filtered['2B_Notas Nao Lancadas'].sum()), 
        (df_filtered['3B_Notas Nao Lancadas'].sum()),
    ],
    'Percentual': [perc_nao_1bim, perc_nao_2bim, perc_nao_3bim],  # Usando os percentuais já calculados
    'Total de Registros': total_registros  # Adicionando esta coluna
})



# Criar o gráfico com Plotly: Notas Não Lançadas
fig = px.bar(
    df_nan,
    x='Bimestre',
    y='Notas Faltantes',
    text='Notas Faltantes',
    title='❌ Quantidade de Notas Não Lançadas por Bimestre',
    color='Bimestre',
    color_discrete_sequence=['#ffcccc', '#ff6666', '#ff0000', '#cc0000', '#990000', '#660000']
)

# Ajustar margens para não cortar as barras
max_valor = df_nan['Notas Faltantes'].max()
fig.update_layout(
    xaxis_title='Bimestre',
    yaxis_title='Quantidade de Notas Faltantes',
    showlegend=False,
    height=500,  
    yaxis=dict(range=[0, max_valor * 1.15]),
    margin=dict(t=50, b=50, l=50, r=50)
)

fig.update_traces(
    textposition='auto',
    textfont_size=12
)

# Exibir o gráfico
st.plotly_chart(fig, use_container_width=True)


# NOTAS LANÇADAS
# Calcular os percentuais de notas lançadas
perc_1bim = ((df_filtered['1B_Notas Lancadas'].sum()) / total_registros * 100).round(1)
perc_2bim = ((df_filtered['2B_Notas Lancadas'].sum()) / total_registros * 100).round(1)
perc_3bim = ((df_filtered['3B_Notas Lancadas'].sum()) / total_registros * 100).round(1)
perc_4bim = ((df_filtered['4B_Notas Lancadas'].sum()) / total_registros * 100).round(1)

st.write("")

# Mostrar métricas detalhadas de notas não lançadas
st.markdown("**✅ Notas Lançadas:**")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "1º Bimestre", 
        f"{(df_filtered['1B_Notas Lancadas'].sum()):,}", 
        f"{perc_1bim}% lançadas",
    )

with col2:
    st.metric(
        "2º Bimestre", 
        f"{(df_filtered['2B_Notas Lancadas'].sum()):,}", 
        f"{perc_2bim}% lançadas",
    )

with col3:
    st.metric(
        "3º Bimestre", 
        f"{(df_filtered['3B_Notas Lancadas'].sum()):,}", 
        f"{perc_3bim}% lançadas",
    )


# Criar o df_lancamento com os percentuais calculados de notas lançadas
df_lancadas = pd.DataFrame({
    'Bimestre': ['1º Bimestre', '2º Bimestre', '3º Bimestre'],
    'Notas Lançadas': [
        (df_filtered['1B_Notas Lancadas'].sum()), 
        (df_filtered['2B_Notas Lancadas'].sum()), 
        (df_filtered['3B_Notas Lancadas'].sum()),
    ],
    'Percentual': [perc_1bim, perc_2bim, perc_3bim],  # Usando os percentuais já calculados
    'Total de Registros': total_registros  # Adicionando esta coluna
})

# Criar o gráfico com Plotly: Notas Lançadas
fig_lancadas = px.bar(
    df_lancadas,
    x='Bimestre',
    y='Notas Lançadas',
    text='Notas Lançadas',
    title='✅ Quantidade de Notas Lançadas por Bimestre',
    color='Bimestre',
    color_discrete_sequence=['#1b5e20', '#2e7d32', '#388e3c', '#4caf50', '#66bb6a', '#81c784', '#a5d6a7', '#c8e6c9', '#e8f5e8']  # Tons de verde
)

# Ajustar margens para não cortar as barras
max_valor_lancadas = df_lancadas['Notas Lançadas'].max()
fig_lancadas.update_layout(
    xaxis_title='Bimestre',
    yaxis_title='Quantidade de Notas Lançadas',
    showlegend=False,
    height=500,  
    yaxis=dict(range=[0, max_valor_lancadas * 1.15]),
    margin=dict(t=50, b=50, l=50, r=50)
)

fig_lancadas.update_traces(
    textposition='auto',
    textfont_size=12
)

# Exibir o gráfico de Notas Lançadas
st.plotly_chart(fig_lancadas, use_container_width=True)

st.write("")
st.write("")

# Percentual de Notas Lançadas e Não Lançadas por DIREC (para 1º e 2º bimestres)
st.markdown(
    "<p style='font-size:24px; font-weight:bold;'>Percentual de Notas Lançadas e Não Lançadas por DIREC</p>",
    unsafe_allow_html=True)

st.markdown("1️⃣ _1º Bimestre:_")

# Calcular totais por DIREC para o 1º bimestre
df_direc_1bim = df_filtered.groupby('DIREC').agg({
    '1B_Notas Lancadas': 'sum',
    '1B_Notas Nao Lancadas': 'sum'
}).round(0)

# Reformatar o DataFrame (tirar a DIREC como índice)
df_direc_1bim = df_direc_1bim.reset_index()

# Adicionar coluna de total de registros (soma das notas lançadas + não lançadas)
df_direc_1bim['Total_Registros'] = df_direc_1bim['1B_Notas Lancadas'] + df_direc_1bim['1B_Notas Nao Lancadas']

# Renomear as colunas para manter compatibilidade
df_direc_1bim = df_direc_1bim.rename(columns={
    '1B_Notas Lancadas': 'Lançadas',
    '1B_Notas Nao Lancadas': 'Não_Lançadas'
})

# Calcular percentuais
df_direc_1bim['%_Lançadas'] = (df_direc_1bim['Lançadas'] / df_direc_1bim['Total_Registros'] * 100).round(1)
df_direc_1bim['%_Não_Lançadas'] = (df_direc_1bim['Não_Lançadas'] / df_direc_1bim['Total_Registros'] * 100).round(1)

# Ordenar por nome da DIREC (ordem alfabética crescente)
df_direc_1bim = df_direc_1bim.sort_values('DIREC', ascending=True)

# Truncar nomes das DIRECs para 9 primeiros caracteres (apenas nº da DIREC)
df_direc_1bim['DIREC_Truncada'] = df_direc_1bim['DIREC'].str.slice(0, 9)

# Criar gráfico de barras empilhadas VERTICAIS
fig_direc_1bim = go.Figure()

# Barra de notas lançadas (verde)
fig_direc_1bim.add_trace(go.Bar(
    name='✅ Notas Lançadas',
    x=df_direc_1bim['DIREC_Truncada'],  # Eixo X com nomes truncados
    y=df_direc_1bim['%_Lançadas'],
    marker=dict(color='#2e7d32'),
    text=df_direc_1bim['%_Lançadas'].astype(str) + '%',
    textposition='inside',
    hovertemplate='<b>%{x}</b><br>Notas Lançadas: %{y}%<br>Total: ' + df_direc_1bim['Lançadas'].astype(str) + '<extra></extra>'
))

# Barra de notas não lançadas (vermelho)
fig_direc_1bim.add_trace(go.Bar(
    name='❌ Notas Não Lançadas',
    x=df_direc_1bim['DIREC_Truncada'],  # Eixo X com nomes truncados
    y=df_direc_1bim['%_Não_Lançadas'],
    marker=dict(color='#c62828'),
    text=df_direc_1bim['%_Não_Lançadas'].astype(str) + '%',
    textposition='inside',
    hovertemplate='<b>%{x}</b><br>Notas Não Lançadas: %{y}%<br>Total: ' + df_direc_1bim['Não_Lançadas'].astype(str) + '<extra></extra>'
))

# Configurar layout
fig_direc_1bim.update_layout(
    title='1º Bimestre: Percentual de Notas Lançadas vs Não Lançadas por DIREC',
    xaxis_title='DIREC',
    yaxis_title='Percentual (%)',
    barmode='stack',
    height=600,
    showlegend=True,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
    margin=dict(t=80, b=100, l=50, r=50)  # Aumentar margem inferior para caber labels
)

# Rodar labels do eixo X em 45 graus e ajustar
fig_direc_1bim.update_xaxes(
    tickangle=-45,
    tickmode='array',
    tickvals=df_direc_1bim['DIREC_Truncada'],
    ticktext=df_direc_1bim['DIREC_Truncada']
)

# Ajustar eixo Y para ir de 0% a 100%
fig_direc_1bim.update_yaxes(range=[0, 100])

# Exibir gráfico
st.plotly_chart(fig_direc_1bim, use_container_width=True)


# Mostrar tabela com dados detalhados e formatação
with st.expander("📋 Ver Dados Detalhados por DIREC"):
    # Criar DataFrame de exibição
    df_display = pd.DataFrame({
        'DIREC': df_direc_1bim['DIREC'],
        'Total de Registros': df_direc_1bim['Total_Registros'],
        'Notas Lançadas': df_direc_1bim['Lançadas'],
        'Notas Não Lançadas': df_direc_1bim['Não_Lançadas'],
        '% Lançadas': df_direc_1bim['%_Lançadas'].astype(str) + ' %',
        '% Não Lançadas': df_direc_1bim['%_Não_Lançadas'].astype(str) + ' %'
    })
    
    # Estilizar a tabela (opcional)
    st.dataframe(
        df_display,
        width='stretch',
        hide_index=True,
        column_config={
            'Total de Registros': st.column_config.NumberColumn(format='%d'),
            'Notas Lançadas': st.column_config.NumberColumn(format='%d'),
            'Notas Não Lançadas': st.column_config.NumberColumn(format='%d')
        })
    

st.write("")
st.markdown("2️⃣ _2º Bimestre:_")

# Calcular totais por DIREC para o 2º bimestre
df_direc_2bim = df_filtered.groupby('DIREC').agg({
    '2B_Notas Lancadas': 'sum',
    '2B_Notas Nao Lancadas': 'sum'
}).round(0)

# Reformatar o DataFrame (tirar a DIREC como índice)
df_direc_2bim = df_direc_2bim.reset_index()

# Adicionar coluna de total de registros (soma das notas lançadas + não lançadas)
df_direc_2bim['Total_Registros'] = df_direc_2bim['2B_Notas Lancadas'] + df_direc_2bim['2B_Notas Nao Lancadas']

# Renomear as colunas para manter compatibilidade
df_direc_2bim = df_direc_2bim.rename(columns={
    '2B_Notas Lancadas': 'Lançadas',
    '2B_Notas Nao Lancadas': 'Não_Lançadas'
})

# Calcular percentuais
df_direc_2bim['%_Lançadas'] = (df_direc_2bim['Lançadas'] / df_direc_2bim['Total_Registros'] * 100).round(1)
df_direc_2bim['%_Não_Lançadas'] = (df_direc_2bim['Não_Lançadas'] / df_direc_2bim['Total_Registros'] * 100).round(1)

# Ordenar por nome da DIREC (ordem alfabética crescente)
df_direc_2bim = df_direc_2bim.sort_values('DIREC', ascending=True)

# Truncar nomes das DIRECs para 9 primeiros caracteres (apenas nº da DIREC)
df_direc_2bim['DIREC_Truncada'] = df_direc_2bim['DIREC'].str.slice(0, 9)

# Criar gráfico de barras empilhadas VERTICAIS
fig_direc_2bim = go.Figure()

# Barra de notas lançadas (verde)
fig_direc_2bim.add_trace(go.Bar(
    name='✅ Notas Lançadas',
    x=df_direc_2bim['DIREC_Truncada'],  # Eixo X com nomes truncados
    y=df_direc_2bim['%_Lançadas'],
    marker=dict(color='#2e7d32'),
    text=df_direc_2bim['%_Lançadas'].astype(str) + '%',
    textposition='inside',
    hovertemplate='<b>%{x}</b><br>Notas Lançadas: %{y}%<br>Total: ' + df_direc_2bim['Lançadas'].astype(str) + '<extra></extra>'
))

# Barra de notas não lançadas (vermelho)
fig_direc_2bim.add_trace(go.Bar(
    name='❌ Notas Não Lançadas',
    x=df_direc_2bim['DIREC_Truncada'],  # Eixo X com nomes truncados
    y=df_direc_2bim['%_Não_Lançadas'],
    marker=dict(color='#c62828'),
    text=df_direc_2bim['%_Não_Lançadas'].astype(str) + '%',
    textposition='inside',
    hovertemplate='<b>%{x}</b><br>Notas Não Lançadas: %{y}%<br>Total: ' + df_direc_2bim['Não_Lançadas'].astype(str) + '<extra></extra>'
))

# Configurar layout
fig_direc_2bim.update_layout(
    title='2º Bimestre: Percentual de Notas Lançadas vs Não Lançadas por DIREC',
    xaxis_title='DIREC',
    yaxis_title='Percentual (%)',
    barmode='stack',
    height=600,
    showlegend=True,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
    margin=dict(t=80, b=100, l=50, r=50)  # Aumentar margem inferior para caber labels
)

# Rodar labels do eixo X em 45 graus e ajustar
fig_direc_2bim.update_xaxes(
    tickangle=-45,
    tickmode='array',
    tickvals=df_direc_2bim['DIREC_Truncada'],
    ticktext=df_direc_2bim['DIREC_Truncada']
)

# Ajustar eixo Y para ir de 0% a 100%
fig_direc_2bim.update_yaxes(range=[0, 100])

# Exibir gráfico
st.plotly_chart(fig_direc_2bim, use_container_width=True)


# Mostrar tabela com dados detalhados e formatação
with st.expander("📋 Ver Dados Detalhados por DIREC"):
    # Criar DataFrame de exibição
    df_display = pd.DataFrame({
        'DIREC': df_direc_2bim['DIREC'],
        'Total de Registros': df_direc_2bim['Total_Registros'],
        'Notas Lançadas': df_direc_2bim['Lançadas'],
        'Notas Não Lançadas': df_direc_2bim['Não_Lançadas'],
        '% Lançadas': df_direc_2bim['%_Lançadas'].astype(str) + ' %',
        '% Não Lançadas': df_direc_2bim['%_Não_Lançadas'].astype(str) + ' %'
    })
    
    # Estilizar a tabela (opcional)
    st.dataframe(
        df_display,
        width='stretch',
        hide_index=True,
        column_config={
            'Total de Registros': st.column_config.NumberColumn(format='%d'),
            'Notas Lançadas': st.column_config.NumberColumn(format='%d'),
            'Notas Não Lançadas': st.column_config.NumberColumn(format='%d')
        })


st.write("")
st.markdown("3️⃣ _3º Bimestre:_")

# Calcular totais por DIREC para o 3º bimestre
df_direc_3bim = df_filtered.groupby('DIREC').agg({
    '3B_Notas Lancadas': 'sum',
    '3B_Notas Nao Lancadas': 'sum'
}).round(0)

# Reformatar o DataFrame (tirar a DIREC como índice)
df_direc_3bim = df_direc_3bim.reset_index()

# Adicionar coluna de total de registros (soma das notas lançadas + não lançadas)
df_direc_3bim['Total_Registros'] = df_direc_3bim['3B_Notas Lancadas'] + df_direc_3bim['3B_Notas Nao Lancadas']

# Renomear as colunas para manter compatibilidade
df_direc_3bim = df_direc_3bim.rename(columns={
    '3B_Notas Lancadas': 'Lançadas',
    '3B_Notas Nao Lancadas': 'Não_Lançadas'
})

# Calcular percentuais
df_direc_3bim['%_Lançadas'] = (df_direc_3bim['Lançadas'] / df_direc_3bim['Total_Registros'] * 100).round(1)
df_direc_3bim['%_Não_Lançadas'] = (df_direc_3bim['Não_Lançadas'] / df_direc_3bim['Total_Registros'] * 100).round(1)

# Ordenar por nome da DIREC (ordem alfabética crescente)
df_direc_3bim = df_direc_3bim.sort_values('DIREC', ascending=True)

# Truncar nomes das DIRECs para 9 primeiros caracteres (apenas nº da DIREC)
df_direc_3bim['DIREC_Truncada'] = df_direc_3bim['DIREC'].str.slice(0, 9)

# Criar gráfico de barras empilhadas VERTICAIS
fig_direc_3bim = go.Figure()

# Barra de notas lançadas (verde)
fig_direc_3bim.add_trace(go.Bar(
    name='✅ Notas Lançadas',
    x=df_direc_3bim['DIREC_Truncada'],  # Eixo X com nomes truncados
    y=df_direc_3bim['%_Lançadas'],
    marker=dict(color='#2e7d32'),
    text=df_direc_3bim['%_Lançadas'].astype(str) + '%',
    textposition='inside',
    hovertemplate='<b>%{x}</b><br>Notas Lançadas: %{y}%<br>Total: ' + df_direc_3bim['Lançadas'].astype(str) + '<extra></extra>'
))

# Barra de notas não lançadas (vermelho)
fig_direc_3bim.add_trace(go.Bar(
    name='❌ Notas Não Lançadas',
    x=df_direc_3bim['DIREC_Truncada'],  # Eixo X com nomes truncados
    y=df_direc_3bim['%_Não_Lançadas'],
    marker=dict(color='#c62828'),
    text=df_direc_3bim['%_Não_Lançadas'].astype(str) + '%',
    textposition='inside',
    hovertemplate='<b>%{x}</b><br>Notas Não Lançadas: %{y}%<br>Total: ' + df_direc_3bim['Não_Lançadas'].astype(str) + '<extra></extra>'
))

# Configurar layout
fig_direc_3bim.update_layout(
    title='3º Bimestre: Percentual de Notas Lançadas vs Não Lançadas por DIREC',
    xaxis_title='DIREC',
    yaxis_title='Percentual (%)',
    barmode='stack',
    height=600,
    showlegend=True,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
    margin=dict(t=80, b=100, l=50, r=50)  # Aumentar margem inferior para caber labels
)

# Rodar labels do eixo X em 45 graus e ajustar
fig_direc_3bim.update_xaxes(
    tickangle=-45,
    tickmode='array',
    tickvals=df_direc_3bim['DIREC_Truncada'],
    ticktext=df_direc_3bim['DIREC_Truncada']
)

# Ajustar eixo Y para ir de 0% a 100%
fig_direc_3bim.update_yaxes(range=[0, 100])

# Exibir gráfico
st.plotly_chart(fig_direc_3bim, use_container_width=True)


# Mostrar tabela com dados detalhados e formatação
with st.expander("📋 Ver Dados Detalhados por DIREC"):
    # Criar DataFrame de exibição
    df_display = pd.DataFrame({
        'DIREC': df_direc_3bim['DIREC'],
        'Total de Registros': df_direc_3bim['Total_Registros'],
        'Notas Lançadas': df_direc_3bim['Lançadas'],
        'Notas Não Lançadas': df_direc_3bim['Não_Lançadas'],
        '% Lançadas': df_direc_3bim['%_Lançadas'].astype(str) + ' %',
        '% Não Lançadas': df_direc_3bim['%_Não_Lançadas'].astype(str) + ' %'
    })
    
    # Estilizar a tabela (opcional)
    st.dataframe(
        df_display,
        width='stretch',
        hide_index=True,
        column_config={
            'Total de Registros': st.column_config.NumberColumn(format='%d'),
            'Notas Lançadas': st.column_config.NumberColumn(format='%d'),
            'Notas Não Lançadas': st.column_config.NumberColumn(format='%d')
        })

st.write("")
st.write("")

# Escolas maiores percentuais de notas não lançadas
st.markdown(
    "<p style='font-size:24px; font-weight:bold;'>Escolas com maiores percentuais de notas não lançadas</p>",
    unsafe_allow_html=True)


# Calcular de forma incremental para evitar sobrecarga
try:
    # Primeiro: obter lista de escolas únicas
    escolas_unicas = df_filtered[['INEP ESCOLA', 'ESCOLA', 'DIREC', 'MUNICÍPIO']].drop_duplicates()
    
    # Inicializar lista para resultados
    resultados = []
    
    # Calcular para cada escola individualmente (mais lento mas seguro)
    for idx, escola in escolas_unicas.iterrows():
        inep = escola['INEP ESCOLA']
        
        # Filtrar dados apenas para esta escola
        df_escola_filtrada = df_filtered[df_filtered['INEP ESCOLA'] == inep]
        
        # Calcular totais baseados nas novas colunas
        total_1b = df_escola_filtrada['1B_Notas Lancadas'].sum() + df_escola_filtrada['1B_Notas Nao Lancadas'].sum()
        total_2b = df_escola_filtrada['2B_Notas Lancadas'].sum() + df_escola_filtrada['2B_Notas Nao Lancadas'].sum()
        total_3b = df_escola_filtrada['3B_Notas Lancadas'].sum() + df_escola_filtrada['3B_Notas Nao Lancadas'].sum()
        
        # Calcular percentuais de notas NÃO lançadas
        nao_lancadas_1b = df_escola_filtrada['1B_Notas Nao Lancadas'].sum()
        nao_lancadas_2b = df_escola_filtrada['2B_Notas Nao Lancadas'].sum()
        nao_lancadas_3b = df_escola_filtrada['3B_Notas Nao Lancadas'].sum()

        perc_1bim = (nao_lancadas_1b / total_1b * 100).round(1) if total_1b > 0 else 0
        perc_2bim = (nao_lancadas_2b / total_2b * 100).round(1) if total_2b > 0 else 0
        perc_3bim = (nao_lancadas_3b / total_3b * 100).round(1) if total_3b > 0 else 0


        # Formatar nome da escola
        escola_formatada = f"{escola['ESCOLA']} (cód. Inep: {inep})"
        
        resultados.append({
            'DIREC': escola['DIREC'],
            'Município': escola['MUNICÍPIO'],
            'Escola': escola_formatada,
            '% Notas Não Lançadas - 1º Bimestre': perc_1bim,
            '% Notas Não Lançadas - 2º Bimestre': perc_2bim,
            '% Notas Não Lançadas - 3º Bimestre': perc_3bim
        })
    
    # Converter para DataFrame
    df_tabela_final = pd.DataFrame(resultados)
    
    # Criar duas colunas para os controles
    col_ordenacao, col_paginacao = st.columns([3, 1])  # 3/4 para ordenação, 1/4 para paginação
    
    with col_ordenacao:
        # Ordenação interativa
        col_ordenacao = st.selectbox(
            "Ordenar por:",
            options=[
                '% Notas Não Lançadas - 1º Bimestre',
                '% Notas Não Lançadas - 2º Bimestre', 
                '% Notas Não Lançadas - 3º Bimestre'
            ],
            index=1
        )

    with col_paginacao:
        # Paginação
        itens_por_pagina = 10
        total_itens = len(df_tabela_final)
        total_paginas = max(1, (total_itens + itens_por_pagina - 1) // itens_por_pagina)
        
        # Seletor de página
        pagina_atual = st.number_input(
            f'Página (1 a {total_paginas})', 
            min_value=1, 
            max_value=total_paginas, 
            value=1
        )

    # Ordenar
    df_tabela_final = df_tabela_final.sort_values(col_ordenacao, ascending=False)
    
    # Calcular índices para paginação
    inicio_idx = (pagina_atual - 1) * itens_por_pagina
    fim_idx = min(inicio_idx + itens_por_pagina, total_itens)
    df_pagina_atual = df_tabela_final.iloc[inicio_idx:fim_idx]
    
    st.write(f"Mostrando escolas {inicio_idx + 1} a {fim_idx} de {total_itens}")
    
    # Mostrar tabela
    st.dataframe(
        df_pagina_atual,
        width='stretch',
        hide_index=True
    )

except Exception as e:
    st.error(f"Erro crítico: {e}")
    st.info("Tente usar filtros mais restritivos para reduzir a quantidade de dados.")


# Forçar limpeza completa
gc.collect()

