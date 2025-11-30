import streamlit as st
import pandas as pd
from collections import defaultdict
from datetime import datetime, timedelta
from backend import AGENDAS, carregar_eventos, encontrar_horarios_pet_comuns, calcular_horarios_livres

st.set_page_config(page_title="Sincronizador PET", page_icon="pet_logo.png", layout="wide")

def format_interval(start_dt: datetime, dur_min: int) -> str:
    """Retorna string no formato 'HH:MM – HH:MM'"""
    end_dt = start_dt + timedelta(minutes=dur_min)
    return f"{start_dt.strftime('%H:%M')} – {end_dt.strftime('%H:%M')}"

def color_cards_html(text: str, background: str, color: str) -> str:
    """Gera HTML estilizado para cards de horário"""
    return f'<div style="background-color:{background}; color:{color}; font-weight:600; padding:6px; margin:3px 0; border-radius:5px;">{text}</div>'

def render_frontend():

    st.image("pet_logo.png", width=90)
    st.title("📅 Sincronizador de agendas PET 💙")
    st.info("Dica: Se os resultados parecerem desatualizados, limpe o cache no menu (☰) → 'Clear cache'.")

    membros_selecionados = st.multiselect("Escolha as agendas para analisar:", options=list(AGENDAS.keys()))
    col1, col2 = st.columns(2)
    intervalo = col1.number_input("⏱️ Duração da Reunião (minutos):", min_value=15, value=50, step=5)
    dias_para_analisar = col2.number_input("📅 Dias a analisar:", min_value=1, max_value=30, value=7)

    if st.button("Analisar Agendas", type="primary"):
        if not membros_selecionados:
            st.warning("Por favor, selecione pelo menos uma agenda.")
            return

        with st.spinner("Carregando e cruzando os dados das agendas..."):
            eventos_por_membro = {sigla: carregar_eventos(AGENDAS[sigla], dias_para_analisar)
                                  for sigla in membros_selecionados}
            eventos_todos = [evento for lista in eventos_por_membro.values() for evento in lista]

            # Horários PET (apenas se houver mais de 1 membro)
            if len(membros_selecionados) > 1:
                st.subheader("Horários 'PET' em Comum")
                horarios_pet_comuns = encontrar_horarios_pet_comuns(eventos_por_membro, intervalo, dias_para_analisar)
                if horarios_pet_comuns:
                    st.success(f"{len(horarios_pet_comuns)} horários PET em comum encontrados.")
                else:
                    st.info("Não foram encontrados horários PET comuns.")
            else:
                horarios_pet_comuns = []
                st.info("Selecione pelo menos duas pessoas para comparar PET em comum.")

            # Horários livres
            st.subheader("Outros horários livres")
            horarios_livres = calcular_horarios_livres(eventos_todos, intervalo, dias_para_analisar)
            if horarios_livres:
                st.success(f"{len(horarios_livres)} blocos livres encontrados.")
            else:
                st.warning("Nenhum horário livre em comum foi encontrado.")

            # Visualização em CARDS por dia
            st.subheader("📆 Horários úteis por dia (PET e Livres)")

            if not horarios_pet_comuns and not horarios_livres:
                st.info("Nenhum horário útil (PET ou Livre) foi encontrado no período selecionado.")
            else:
                hoje = datetime.now().date()
                nomes_semana = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

                for i in range(dias_para_analisar):
                    dia = hoje + timedelta(days=i)
                    nome_dia = f"{nomes_semana[dia.weekday()]} {dia.strftime('%d/%m')}"

                    # Filtra horários daquele dia para PET e Livre
                    pet_do_dia = [format_interval(h, intervalo) for h in horarios_pet_comuns if h.date() == dia]
                    livre_do_dia = [format_interval(h, intervalo) for h in horarios_livres if h.date() == dia]

                    with st.container():
                        st.markdown(f"### 📅 {nome_dia}")

                        if pet_do_dia:
                            st.markdown("**🔵 Horários PET:**")
                            for intervalo_str in pet_do_dia:
                                st.markdown(
                                    color_cards_html(intervalo_str, "#cfe9ff", "#0b3d91"),
                                    unsafe_allow_html=True
                                )
                        else:
                            st.markdown("_Nenhum horário PET disponível_")

                        if livre_do_dia:
                            st.markdown("**🟢 Horários Livres:**")
                            for intervalo_str in livre_do_dia:
                                st.markdown(
                                    color_cards_html(intervalo_str, "#d6f5d6", "#1a6d1a"),
                                    unsafe_allow_html=True
                                )
                        else:
                            st.markdown("_Nenhum horário livre disponível_")

            # Dados de depuração (opcional)
            st.subheader("🕵️‍♀️ DADOS DE DEPURAÇÃO: Eventos Carregados")
            if eventos_todos:
                df_debug = pd.DataFrame(eventos_todos)
                # tentar atribuir membro a cada linha (aproximação)
                membros_map = []
                for m, evs in eventos_por_membro.items():
                    membros_map.extend([m] * len(evs))
                if len(membros_map) < len(df_debug):
                    membros_map.extend([""] * (len(df_debug) - len(membros_map)))
                df_debug['membro'] = membros_map[:len(df_debug)]
                df_debug = df_debug.sort_values(by="inicio").reset_index(drop=True)
                st.dataframe(df_debug[['membro', 'inicio', 'fim', 'nome']], use_container_width=True)
            else:
                st.error("Nenhum evento foi carregado para o período selecionado.")

if __name__ == "__main__":
    render_frontend()
