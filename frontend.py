import streamlit as st
import pandas as pd
from collections import defaultdict
from datetime import time
from backend import AGENDAS, carregar_eventos, encontrar_horarios_pet_comuns, calcular_horarios_livres
import streamlit as st


def render_frontend():
    st.set_page_config(
        page_title="Sincronizador PET",
        page_icon="loguinho-azul.png",
        layout="wide"
    )
    st.image("pet_logo.png", width=90)
    st.title("📅 Sincronizador de agendas PET 💙")
    st.info("Dica: Se os resultados parecerem desatualizados, limpe o cache no menu (☰) → 'Clear cache'.")

    membros_selecionados = st.multiselect("Escolha as agendas para analisar:", options=list(AGENDAS.keys()))
    col1, col2, = st.columns(2) 
    intervalo = col1.number_input("⏱️ Intervalo (minutos):", min_value=15, value=50, step=5)
    dias_para_analisar = col2.number_input("📅 Dias a analisar:", min_value=1, max_value=30, value=7)

    if st.button("Analisar Agendas", type="primary"):
        if not membros_selecionados:
            st.warning("Por favor, selecione pelo menos uma agenda.")
        else:
            with st.spinner("Carregando e cruzando os dados das agendas..."):
                eventos_por_membro = {sigla: carregar_eventos(AGENDAS[sigla], dias_para_analisar)
                                      for sigla in membros_selecionados}
                eventos_todos = [evento for lista in eventos_por_membro.values() for evento in lista]

                if len(membros_selecionados) > 1:
                    st.subheader("Horários 'PET' em Comum")
                    horarios_pet_comuns = encontrar_horarios_pet_comuns(eventos_por_membro, intervalo, dias_para_analisar)
                    if horarios_pet_comuns:
                        pet_por_dia = defaultdict(list)
                        for h in horarios_pet_comuns:
                            pet_por_dia[h.date()].append(h.strftime("%H:%M"))
                        for dia, horarios in sorted(pet_por_dia.items()):
                            st.success(f"**{dia.strftime('%d/%m/%Y')}**: {', '.join(horarios)}")
                    else:
                        st.info("Não foram encontrados horários onde todos tivessem um evento 'PET' simultaneamente.")
                else:
                    st.info("Selecione pelo menos duas pessoas para comparar.")

                st.subheader("Outros horários livres")
                horarios_livres = calcular_horarios_livres(eventos_todos, intervalo, dias_para_analisar)
                if horarios_livres:
                    livres_por_dia = defaultdict(list)
                    for h in horarios_livres:
                        livres_por_dia[h.date()].append(h.strftime("%H:%M"))
                    dias_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
                    for dia, horarios in sorted(livres_por_dia.items()):
                        nome_dia_semana = dias_semana[dia.weekday()]
                        with st.expander(f"**{dia.strftime('%d/%m/%Y')} - {nome_dia_semana}**"):
                            st.text(" | ".join(horarios))
                else:
                    st.warning("Nenhum horário livre em comum foi encontrado.")
                
                st.subheader("🕵️‍♀️ DADOS DE DEPURAÇÃO: Eventos Carregados")
                if eventos_todos:
                    df_debug = pd.DataFrame(eventos_todos)
                    df_debug['membro'] = [m for m, eventos in eventos_por_membro.items() for _ in eventos]
                    df_debug = df_debug.sort_values(by="inicio").reset_index(drop=True)
                    st.dataframe(df_debug[['membro', 'inicio', 'fim', 'nome']])
                else:
                    st.error("Nenhum evento foi carregado para o período selecionado.")