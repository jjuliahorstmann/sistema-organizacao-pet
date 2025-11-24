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

def montar_tabela_compacta(horarios_pet: list, horarios_livres: list, duracao_min: int, dias: int):
    """
    Monta um DataFrame compacto (linhas = intervalos encontrados; colunas = dias da semana)
    contendo apenas os horários úteis (PET e Livre).
    """
    # Organiza por dia
    pet_por_dia = defaultdict(set)    # date -> set(interval_str)
    livre_por_dia = defaultdict(set)  # date -> set(interval_str)

    for h in horarios_pet:
        data = h.date()
        pet_por_dia[data].add(format_interval(h, duracao_min))

    for h in horarios_livres:
        data = h.date()
        livre_por_dia[data].add(format_interval(h, duracao_min))

    # Construir lista de dias (colunas) no período
    hoje = datetime.now().date()
    dias_lista = [hoje + timedelta(days=i) for i in range(dias)]
    # Cabeçalhos legíveis: "Seg 24/11"
    nomes_dias = []
    for d in dias_lista:
        nome_sem = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"][d.weekday()]
        nomes_dias.append(f"{nome_sem} {d.strftime('%d/%m')}")

    # Reunir todos os intervalos únicos (como strings) encontrados na semana
    todos_intervalos = set()
    for d in dias_lista:
        todos_intervalos.update(pet_por_dia.get(d, set()))
        todos_intervalos.update(livre_por_dia.get(d, set()))

    if not todos_intervalos:
        return None  # nada para mostrar

    # Ordena os intervalos pelos horários de início (HH:MM)
    def key_interval(s):
        # s é 'HH:MM – HH:MM'
        start = s.split("–")[0].strip()
        h, m = start.split(":")
        return int(h) * 60 + int(m)
    intervalos_ordenados = sorted(todos_intervalos, key=key_interval)

    # Monta DataFrame: index = intervalos, columns = dias
    df = pd.DataFrame(index=intervalos_ordenados, columns=nomes_dias)
    df = df.fillna("")  # células vazias por padrão

    # Preenche com 'PET' ou 'Livre' — PET tem prioridade caso haja sobreposição
    for idx in intervalos_ordenados:
        # descobrir datetime de início por dia se necessário (não preciso guardar o datetime real aqui)
        for col_i, d in enumerate(dias_lista):
            col_name = nomes_dias[col_i]
            if idx in pet_por_dia.get(d, set()):
                df.at[idx, col_name] = "PET"
            elif idx in livre_por_dia.get(d, set()):
                df.at[idx, col_name] = "Livre"
            else:
                df.at[idx, col_name] = ""

    return df

def color_cells(val):
    """Retorna estilo CSS para a célula com base no valor."""
    if val == "PET":
        return "background-color: #cfe9ff; color: #0b3d91; font-weight: 600;"  # azul claro
    if val == "Livre":
        return "background-color: #d6f5d6; color: #1a6d1a; font-weight: 600;"  # verde claro
    return ""


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

            # Horários PET (apenas se houver mais de 1 membro; caso 1, ainda faz sentido?)
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

            # Monta tabela compacta apenas com os horários encontrados
            st.subheader("📆 Tabela Semanal Compacta (apenas horários úteis)")
            tabela = montar_tabela_compacta(horarios_pet_comuns, horarios_livres, intervalo, dias_para_analisar)
            if tabela is None:
                st.info("Nenhum horário útil (PET ou Livre) foi encontrado no período selecionado.")
            else:
                # Aplica estilo condicional
                try:
                    styled = tabela.style.applymap(color_cells)
                    st.dataframe(styled, use_container_width=True)
                except Exception:
                    # fallback simples se styler não for compatível no ambiente
                    st.dataframe(tabela.fillna(""), use_container_width=True)

            # Dados de depuração (opcional)
            st.subheader("🕵️‍♀️ DADOS DE DEPURAÇÃO: Eventos Carregados")
            if eventos_todos:
                df_debug = pd.DataFrame(eventos_todos)
                # tentar atribuir membro a cada linha (approximação)
                membros_map = []
                for m, evs in eventos_por_membro.items():
                    membros_map.extend([m] * len(evs))
                # se tamanhos diferentes, preenche com vazio
                if len(membros_map) < len(df_debug):
                    membros_map.extend([""] * (len(df_debug) - len(membros_map)))
                df_debug['membro'] = membros_map[:len(df_debug)]
                df_debug = df_debug.sort_values(by="inicio").reset_index(drop=True)
                st.dataframe(df_debug[['membro', 'inicio', 'fim', 'nome']], use_container_width=True)
            else:
                st.error("Nenhum evento foi carregado para o período selecionado.")

if __name__ == "__main__":
    render_frontend()
