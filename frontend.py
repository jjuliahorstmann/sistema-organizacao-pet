import streamlit as st
import pandas as pd
from collections import defaultdict
from datetime import time
from backend import AGENDAS, carregar_eventos, encontrar_horarios_pet_comuns, calcular_horarios_livres


def render_frontend():
    st.set_page_config(layout="wide", page_title="Analisador de Agendas")
    st.title("📅 Analisador de Agendas em Comum")
    st.info("Dica: Se os resultados parecerem desatualizados, limpe o cache no menu (☰) → 'Clear cache'.")

    membros_selecionados = st.multiselect("Escolha as agendas para analisar:", options=list(AGENDAS.keys()))
    col1, col2, col3 = st.columns(3) # é nessa parte que vamos criar o filtro de horário útil, com um "col3",
    #pra isso vamos ter que descobrir como que adiciona esse tipo de daodo (hora: minuto)
    #talvez adicionar um "st.radio()", e poder escolher entre "horário comercial: 7:30 - 18:00" e "horário flexível: 7:30 - 22:00"
    #assim evita de ficar colocando muitos horários quebrados ou de digitarem errado
    intervalo = col1.number_input("⏱️ Intervalo (minutos):", min_value=15, value=50, step=5)
    dias_para_analisar = col2.number_input("📅 Dias a analisar:", min_value=1, max_value=30, value=7)
    janela_de_analise = col3.radio(
    "Tipo de horário:",
    ["Horário comercial (7:30 - 18:00)", "Horário flexível (7:30 - 22:00)", "Personalizado"]
)

    if janela_de_analise == "Personalizado":
        col4, col5 = st.columns(2)
        horario_inicio = col4.time_input("🕓 Início:", value=time(7, 30))
        horario_fim = col5.time_input("🕕 Fim:", value=time(18, 0))
    else:
        if "comercial" in janela_de_analise.lower():
            horario_inicio, horario_fim = time(7, 30), time(18, 0)
        else:
            horario_inicio, horario_fim = time(7, 30), time(22, 0)

    if st.button("Analisar Agendas", type="primary"):
        if not membros_selecionados:
            st.warning("Por favor, selecione pelo menos uma agenda.")
    else:
        with st.spinner("Carregando e cruzando os dados das agendas..."):

            # 1️⃣ Carrega os eventos
            eventos_por_membro_raw = {
                sigla: carregar_eventos(AGENDAS[sigla], dias_para_analisar)
                for sigla in membros_selecionados
            }

            # 2️⃣ Função que recorta eventos para dentro da janela de análise
            from datetime import datetime, timedelta

            def ajustar_eventos_para_janela(eventos, horario_inicio, horario_fim, dias_para_analisar):
                eventos_ajustados = []
                hoje = datetime.now().date()
                data_final = hoje + timedelta(days=dias_para_analisar - 1)

                for ev in eventos:
                    ev_inicio = ev["inicio"]
                    ev_fim = ev["fim"]

                    # ignora eventos fora do período
                    if ev_fim.date() < hoje or ev_inicio.date() > data_final:
                        continue

                    # percorre cada dia dentro do evento
                    dia_atual = max(ev_inicio.date(), hoje)
                    dia_ultimo = min(ev_fim.date(), data_final)
                    while dia_atual <= dia_ultimo:
                        janela_inicio_dt = datetime.combine(dia_atual, horario_inicio)
                        janela_fim_dt = datetime.combine(dia_atual, horario_fim)

                        # recorte da interseção entre evento e janela
                        inicio_recortado = max(ev_inicio, janela_inicio_dt)
                        fim_recortado = min(ev_fim, janela_fim_dt)

                        if inicio_recortado < fim_recortado:
                            ev_copy = ev.copy()
                            ev_copy["inicio"] = inicio_recortado
                            ev_copy["fim"] = fim_recortado
                            eventos_ajustados.append(ev_copy)

                        dia_atual += timedelta(days=1)

                return eventos_ajustados

            # 3️⃣ Aplica o ajuste de janela
            eventos_por_membro = {
                m: ajustar_eventos_para_janela(evts, horario_inicio, horario_fim, dias_para_analisar)
                for m, evts in eventos_por_membro_raw.items()
            }
            eventos_todos = [evento for lista in eventos_por_membro.values() for evento in lista]

            # 4️⃣ Mostra os dados carregados (após o recorte)
            st.subheader("🕵️‍♀️ DADOS DE DEPURAÇÃO: Eventos Carregados (filtrados pela janela)")
            if eventos_todos:
                df_debug = pd.DataFrame(eventos_todos)
                df_debug["membro"] = [m for m, eventos in eventos_por_membro.items() for _ in eventos]
                df_debug = df_debug.sort_values(by="inicio").reset_index(drop=True)
                st.dataframe(df_debug[["membro", "inicio", "fim", "nome"]])
            else:
                st.error("Nenhum evento foi carregado dentro da janela selecionada.")

            # 5️⃣ Análise dos horários PET
            if len(membros_selecionados) > 1:
                st.subheader("Horários 'PET' em Comum")
                horarios_pet_comuns = encontrar_horarios_pet_comuns(
                    eventos_por_membro,
                    intervalo,
                    dias_para_analisar,
                    horario_inicio,
                    horario_fim
                )
                if horarios_pet_comuns:
                    pet_por_dia = defaultdict(list)
                    for h in horarios_pet_comuns:
                        if horario_inicio <= h.time() <= horario_fim:
                            pet_por_dia[h.date()].append(h.strftime("%H:%M"))
                    for dia, horarios in sorted(pet_por_dia.items()):
                        st.success(f"**{dia.strftime('%d/%m/%Y')}**: {', '.join(horarios)}")
                else:
                    st.info("Não foram encontrados horários onde todos tivessem um evento 'PET' simultaneamente.")
            else:
                st.info("Selecione pelo menos duas pessoas para comparar.")

            # 6️⃣ Cálculo de horários livres
            st.subheader("Outros horários livres")
            horarios_livres = calcular_horarios_livres(
                eventos_todos,
                intervalo,
                dias_para_analisar,
                horario_inicio,
                horario_fim
            )
            if horarios_livres:
                livres_por_dia = defaultdict(list)
                for h in horarios_livres:
                    if horario_inicio <= h.time() <= horario_fim:
                        livres_por_dia[h.date()].append(h.strftime("%H:%M"))
                dias_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
                for dia, horarios in sorted(livres_por_dia.items()):
                    nome_dia_semana = dias_semana[dia.weekday()]
                    with st.expander(f"**{dia.strftime('%d/%m/%Y')} - {nome_dia_semana}**"):
                        st.text(" | ".join(horarios))
            else:
                st.warning("Nenhum horário livre em comum foi encontrado.")