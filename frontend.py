import streamlit as st
import pandas as pd
from datetime import time
from collections import defaultdict
from backend import AGENDAS, carregar_eventos, encontrar_horarios_pet_comuns, calcular_horarios_livres


def render_frontend():
    st.set_page_config(layout="wide", page_title="Analisador de Agendas")
    st.title("📅 Analisador de Agendas em Comum")

    # Seleção de membros
    membros = st.multiselect("Escolha as agendas para analisar:", list(AGENDAS.keys()))
    if not membros:
        st.info("Selecione pelo menos uma agenda para começar.")
        return

    # Configurações principais
    dias = st.number_input("📅 Quantos dias analisar:", 1, 30, 7)
    janela = st.number_input("⏳ Janela de análise (minutos):", 5, 240, 60, 5)

    # Filtro de horários com slider
    hora_inicio, hora_fim = st.slider(
        "🕒 Intervalo de horários:",
        min_value=time(7, 30),
        max_value=time(22, 0),
        value=(time(8, 0), time(22, 0)),
        step=300  # 5 minutos
    )

    if st.button("🔍 Analisar"):
        st.info("Carregando dados...")

        # Carrega e junta eventos
        eventos_por_membro = {
            m: carregar_eventos(AGENDAS[m], dias) for m in membros
        }
        todos_eventos = [e for lista in eventos_por_membro.values() for e in lista]

        if not todos_eventos:
            st.error("Nenhum evento encontrado.")
            return

        df = pd.DataFrame(todos_eventos)
        df["membro"] = [m for m, evts in eventos_por_membro.items() for _ in evts]
        df = df.sort_values("inicio")

        # Mostra eventos carregados
        st.subheader("📋 Eventos carregados")
        st.dataframe(df[["membro", "inicio", "fim", "nome"]])

        # Filtra pelo intervalo de horário
        df = df[(df["inicio"].dt.time >= hora_inicio) & (df["fim"].dt.time <= hora_fim)]
        if df.empty:
            st.warning("Nenhum evento dentro do intervalo selecionado.")
            return

        # Horários PET em comum
        if len(membros) > 1:
            st.subheader("🤝 Horários PET em comum")
            comuns = encontrar_horarios_pet_comuns(eventos_por_membro, janela, dias)
            if comuns:
                por_dia = defaultdict(list)
                for h in comuns:
                    if hora_inicio <= h.time() <= hora_fim:
                        por_dia[h.date()].append(h.strftime("%H:%M"))
                if por_dia:
                    for d, h in sorted(por_dia.items()):
                        st.success(f"**{d.strftime('%d/%m/%Y')}**: {', '.join(h)}")
                else:
                    st.info("Nenhum horário em comum dentro do intervalo.")
            else:
                st.info("Nenhum horário em comum encontrado.")
        else:
            st.info("Selecione pelo menos duas pessoas para comparar.")

        # Horários livres
        st.subheader("🕰️ Horários livres em comum")
        livres = calcular_horarios_livres(todos_eventos, janela, dias)
        if livres:
            por_dia = defaultdict(list)
            for h in livres:
                if hora_inicio <= h.time() <= hora_fim:
                    por_dia[h.date()].append(h.strftime("%H:%M"))
            for d, h in sorted(por_dia.items()):
                with st.expander(f"{d.strftime('%d/%m/%Y')}"):
                    st.text(" | ".join(h))
        else:
            st.warning("Nenhum horário livre dentro do intervalo.")
