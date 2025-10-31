import streamlit as st
import pandas as pd
from collections import defaultdict
from backend import AGENDAS, carregar_eventos, encontrar_horarios_pet_comuns, calcular_horarios_livres


def render_frontend():
    st.set_page_config(layout="wide", page_title="Analisador de Agendas")
    st.title("📅 Analisador de Agendas em Comum")
    st.info("Dica: Se os resultados parecerem desatualizados, limpe o cache no menu (☰) → 'Clear cache'.")

    membros_selecionados = st.multiselect("Escolha as agendas para analisar:", options=list(AGENDAS.keys()))
    col1, col2 = st.columns(2) # é nessa parte que vamos criar o filtro de horário útil, com um "col3",
    #pra isso vamos ter que descobrir como que adiciona esse tipo de daodo (hora: minuto)
    #talvez adicionar um "st.radio()", e poder escolher entre "horário comercial: 7:30 - 18:00" e "horário flexível: 7:30 - 22:00"
    #assim evita de ficar colocando muitos horários quebrados ou de digitarem errado
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

                st.subheader("🕵️‍♀️ DADOS DE DEPURAÇÃO: Eventos Carregados")
                if eventos_todos:
                    df_debug = pd.DataFrame(eventos_todos)
                    df_debug['membro'] = [m for m, eventos in eventos_por_membro.items() for _ in eventos]
                    df_debug = df_debug.sort_values(by="inicio").reset_index(drop=True)
                    st.dataframe(df_debug[['membro', 'inicio', 'fim', 'nome']])
                else:
                    st.error("Nenhum evento foi carregado para o período selecionado.")

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
                            st.text(" | ".join(horarios)) #usar o DataFrame do pandas aqui, fica mais bonito do que os horários separados por barra
                else:
                    st.warning("Nenhum horário livre em comum foi encontrado.")