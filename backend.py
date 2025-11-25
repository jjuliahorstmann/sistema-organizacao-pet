import json
import pytz
import os
import re
from datetime import datetime, timedelta
from typing import *
from datetime import time
from icalevents.icalevents import events
import streamlit as st

# Obtem dados da autoridade certificadora
import ssl, certifi
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
ssl._create_default_https_context = ssl.create_default_context(cafile=certifi.where())

# Configurações globais
FUSO_HORARIO_LOCAL = pytz.timezone('America/Sao_Paulo')


# === NOVAS FUNÇÕES PARA CONSTANTES ===
def carregar_constantes(arquivo_json: str = "constantes.json") -> dict:
    """Carrega o arquivo constantes.json que contém os nomes reservados."""
    try:
        caminho_absoluto = os.path.join(os.path.dirname(__file__), arquivo_json)
        with open(caminho_absoluto, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("❌ Arquivo 'constantes.json' não encontrado.")
    except json.JSONDecodeError:
        st.error("⚠️ Erro ao ler o arquivo 'constantes.json' — formato inválido.")
    except Exception as e:
        st.error(f"Erro inesperado ao carregar o arquivo de constantes: {e}")
    return {"nomes_exatos": [], "nomes_iniciam_com": []}


def eh_evento_reservado(nome_evento: str, constantes: dict) -> bool:
    """Verifica se o nome do evento corresponde a um evento reservado (ocupado)."""
    if not nome_evento:
        return False
    nome_evento = nome_evento.strip()

    # Verifica correspondência exata
    if nome_evento in constantes["nomes_exatos"]:
        return True

    # Verifica se começa com algum dos prefixos definidos
    for inicio in constantes["nomes_iniciam_com"]:
        if nome_evento.startswith(inicio):
            return True

    return False


# === CARREGA AS AGENDAS ===
def carregar_agendas(arquivo_json: str = "agendas.json") -> dict:
    """
    Carrega o arquivo agendas.json do mesmo diretório do backend.py.
    Retorna um dicionário com as siglas e URLs das agendas.
    """
    try:
        caminho_absoluto = os.path.join(os.path.dirname(__file__), arquivo_json)
        with open(caminho_absoluto, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("❌ Arquivo 'agendas.json' não encontrado no repositório.")
    except json.JSONDecodeError:
        st.error("⚠️ Erro ao ler o arquivo 'agendas.json' — formato inválido.")
    except Exception as e:
        st.error(f"Erro inesperado ao carregar o arquivo de agendas: {e}")
    return {}


# === CARREGA AS AGENDAS ===
AGENDAS = carregar_agendas()


@st.cache_data(ttl=60) 
def carregar_eventos(url: str, dias_a_frente: int) -> List[dict]:
    """
    Baixa eventos da URL iCal, expande recorrências e retorna lista de dicts:
    {'inicio': datetime_naive, 'fim': datetime_naive, 'nome': summary}
    Todos os datetimes retornados são timezone-naive mas já convertidos para o fuso local.
    """
    inicio_periodo = datetime.now(FUSO_HORARIO_LOCAL)
    fim_periodo = inicio_periodo + timedelta(days=dias_a_frente)
    eventos_formatados: List[Dict[str, Any]] = []
    try:
        lista_eventos_brutos = events(url, start=inicio_periodo, end=fim_periodo)
        for evento in lista_eventos_brutos:
            # Converte para fuso local e remove tzinfo para facilitar comparações
            inicio = evento.start.astimezone(FUSO_HORARIO_LOCAL).replace(tzinfo=None)
            fim = evento.end.astimezone(FUSO_HORARIO_LOCAL).replace(tzinfo=None)
            eventos_formatados.append({"inicio": inicio, "fim": fim, "nome": evento.summary})
        return eventos_formatados
    except Exception as e:
        st.error(f"Falha ao carregar agenda ({url}). Erro: {e}")
        return []
def _merge_intervals(intervalos: List[Tuple[datetime, datetime]]) -> List[Tuple[datetime, datetime]]:
    """
    Recebe uma lista de tuplas (start, end) e retorna a lista mesclada (sem sobreposições),
    ordenada pelo início.
    """
    if not intervalos:
        return []
    sorted_intervals = sorted(intervalos, key=lambda x: x[0])
    merged = [sorted_intervals[0]]
    for current_start, current_end in sorted_intervals[1:]:
        last_start, last_end = merged[-1]
        if current_start <= last_end:
            # sobreposição ou contíguo -> estende
            merged[-1] = (last_start, max(last_end, current_end))
        else:
            merged.append((current_start, current_end))
    return merged

def _intersect_two_interval_sets(a: List[Tuple[datetime, datetime]], b: List[Tuple[datetime, datetime]]) -> List[Tuple[datetime, datetime]]:
    """
    Interseção entre dois conjuntos de intervalos (assume cada lista já mesclada e ordenada).
    Retorna uma lista de intervalos resultantes da interseção.
    """
    i = j = 0
    result = []
    while i < len(a) and j < len(b):
        start_a, end_a = a[i]
        start_b, end_b = b[j]
        start_max = max(start_a, start_b)
        end_min = min(end_a, end_b)
        if start_max < end_min:
            result.append((start_max, end_min))
        # Avança o ponteiro que termina primeiro
        if end_a < end_b:
            i += 1
        else:
            j += 1
    return result


def _intersect_interval_sets(sets: List[List[Tuple[datetime, datetime]]]) -> List[Tuple[datetime, datetime]]:
    """Interseção de múltiplos conjuntos de intervalos."""
    if not sets:
        return []
    intersected = sets[0]
    for s in sets[1:]:
        intersected = _intersect_two_interval_sets(intersected, s)
        if not intersected:
            break
    return intersected


def _clip_interval_to_day(interval: Tuple[datetime, datetime], inicio_dia: datetime, fim_dia: datetime) -> Tuple[datetime, datetime]:
    """Recorta um intervalo para que fique dentro do [inicio_dia, fim_dia]."""
    start, end = interval
    new_start = max(start, inicio_dia)
    new_end = min(end, fim_dia)
    return (new_start, new_end) if new_start < new_end else None

# -------------------------
# Função principal: encontrar blocos livres num dia
# -------------------------
def _encontrar_blocos_livres_pela_lista_de_ocupados(ocupados: List[Tuple[datetime, datetime]],
                                                    inicio_periodo: datetime,
                                                    fim_periodo: datetime,
                                                    duracao_min: int) -> List[datetime]:
    """
    Dado um conjunto de intervalos 'ocupados' (já mesclados), encontra os blocos livres
    entre inicio_periodo e fim_periodo cuja duração >= duracao_min.
    Retorna a lista dos horários de início desses blocos (datetime).
    """
    blocos_inicio: List[datetime] = []
    # Se não há ocupações, todo o período é livre
    if not ocupados:
        total_min = (fim_periodo - inicio_periodo).total_seconds() / 60
        if total_min >= duracao_min:
            blocos_inicio.append(inicio_periodo)
        return blocos_inicio

    # Certifica que os ocupados estão mesclados e dentro do período
    ocupados_mesclados = _merge_intervals(ocupados)

    cursor = inicio_periodo
    for start, end in ocupados_mesclados:
        # pula ocupações que terminam antes do cursor
        if end <= cursor:
            continue
        # se a ocupação começa depois do cursor há um gap
        if start > cursor:
            gap_min = (start - cursor).total_seconds() / 60
            if gap_min >= duracao_min:
                blocos_inicio.append(cursor)
        # avança cursor para o fim da ocupação atual
        cursor = max(cursor, end)
        if cursor >= fim_periodo:
            break

    # gap final entre cursor e fim_periodo
    if cursor < fim_periodo:
        gap_min = (fim_periodo - cursor).total_seconds() / 60
        if gap_min >= duracao_min:
            blocos_inicio.append(cursor)

    return blocos_inicio

# -------------------------
# Função: calcular_horarios_livres
# -------------------------
def calcular_horarios_livres(eventos_todos: List[dict], intervalo_min: int, dias: int) -> List[datetime]:
    """
    Versão corrigida e robusta:
    - Não fragmenta eventos: usa os inícios/fins reais retornados por carregar_eventos.
    - Mescla corretamente todos os intervalos ocupados do dia (sem duplicação).
    - Encontra blocos livres contínuos com duração >= intervalo_min.
    - Mostra depuração: eventos lidos e intervalos mesclados por dia.
    """
    CONSTANTES = carregar_constantes()
    horarios_livres: List[datetime] = []

    for dia_offset in range(dias):
        inicio_periodo = (datetime.now(FUSO_HORARIO_LOCAL)
                          .replace(hour=7, minute=30, second=0, microsecond=0)
                          + timedelta(days=dia_offset)).replace(tzinfo=None)
        fim_periodo = inicio_periodo.replace(hour=22, minute=0, second=0, microsecond=0)

        # 1) Filtra eventos que intersectam este dia
        eventos_dia = [e for e in eventos_todos if e["fim"] > inicio_periodo and e["inicio"] < fim_periodo]

        # Depuração: mostrar eventos lidos para este dia (útil para checar casos como 'Reunião ED')
        if eventos_dia:
            try:
                import pandas as _pd
                st.write(f"--- Depuração de eventos para {inicio_periodo.date()} ---")
                df_dbg = _pd.DataFrame([{
                    "membro": e.get("membro", ""),
                    "nome": e.get("nome", ""),
                    "inicio": e.get("inicio"),
                    "fim": e.get("fim"),
                    "duração_min": (e.get("fim") - e.get("inicio")).total_seconds() / 60.0
                } for e in eventos_dia])
                st.dataframe(df_dbg.sort_values("inicio").reset_index(drop=True))
            except Exception:
                for e in eventos_dia:
                    st.write(f"{e.get('nome','')} — {e.get('inicio')} -> {e.get('fim')}")

        # 2) Construir lista de intervalos ocupados (start, end) sem fragmentar.
        intervalos_crus: List[Tuple[datetime, datetime]] = []
        for e in eventos_dia:
            start = max(e["inicio"], inicio_periodo)
            end = min(e["fim"], fim_periodo)
            if start < end:
                intervalos_crus.append((start, end))

        # 3) Mesclar intervalos ocupados
        todos_ocupados_mesclados = _merge_intervals(intervalos_crus)

        # Depuração: mostrar intervalos mesclados
        if todos_ocupados_mesclados:
            try:
                rows = [{"inicio": s, "fim": e, "duração_min": (e - s).total_seconds() / 60.0}
                        for s, e in todos_ocupados_mesclados]
                import pandas as _pd
                st.write(f"Intervalos ocupados mesclados para {inicio_periodo.date()}:")
                st.dataframe(_pd.DataFrame(rows).sort_values("inicio").reset_index(drop=True))
            except Exception:
                for s, e in todos_ocupados_mesclados:
                    st.write(f"Ocupado: {s} -> {e} ({(e-s).total_seconds()/60:.0f} min)")

        # 4) Encontrar blocos livres entre inicio_periodo e fim_periodo com duração >= intervalo_min
        blocos = _encontrar_blocos_livres_pela_lista_de_ocupados(
            todos_ocupados_mesclados, inicio_periodo, fim_periodo, intervalo_min
        )
        horarios_livres.extend(blocos)

    return sorted(horarios_livres)
# -------------------------
# Função: encontrar_horarios_pet_comuns
# -------------------------
def encontrar_horarios_pet_comuns(eventos_por_membro: Dict[str, List[dict]], intervalo_min: int, dias: int) -> List[datetime]:
    """
    Encontra blocos em que TODOS os membros têm eventos 'PET' simultâneos por >= intervalo_min.
    - Mantém a regra: nome do evento começa com 'PET' (case-insensitive).
    - Ignora blocos que contenham eventos reservados (constantes.json).
    Retorna lista de datetimes (início de cada bloco comum).
    """
    CONSTANTES = carregar_constantes()
    horarios_finais: List[datetime] = []

    if not eventos_por_membro:
        return []

    membros = list(eventos_por_membro.keys())

    for dia_offset in range(dias):
        dia_base = (datetime.now(FUSO_HORARIO_LOCAL).replace(hour=0, minute=0, second=0, microsecond=0)
                    + timedelta(days=dia_offset)).replace(tzinfo=None)
        inicio_periodo = dia_base.replace(hour=7, minute=30, second=0, microsecond=0)
        fim_periodo = dia_base.replace(hour=22, minute=0, second=0, microsecond=0)

        # Para cada membro, construir lista de intervalos PET válidos (mesclados)
        conjuntos_pet_por_membro: List[List[Tuple[datetime, datetime]]] = []
        for sigla, eventos in eventos_por_membro.items():
            pet_intervals: List[Tuple[datetime, datetime]] = []
            for e in eventos:
                nome = (e.get("nome") or "").strip()
                if not nome:
                    continue
                # considerar 'PET' case-insensitive no começo
                if nome.upper().startswith("PET"):
                    # não considerar se for reservado explicitamente
                    if eh_evento_reservado(nome, CONSTANTES):
                        # pula eventos PET que são marcados como reservados
                        continue
                    # intersecta com janela do dia
                    start = max(e["inicio"], inicio_periodo)
                    end = min(e["fim"], fim_periodo)
                    if start < end:
                        pet_intervals.append((start, end))
            pet_intervals_merged = _merge_intervals(pet_intervals)
            conjuntos_pet_por_membro.append(pet_intervals_merged)

        # Se algum membro não tem PET naquele dia, não há interseção possível
        if any(len(s) == 0 for s in conjuntos_pet_por_membro):
            continue

        # Interseção entre todos os conjuntos PET
        intersecao = _intersect_interval_sets(conjuntos_pet_por_membro)

        # Dentro de cada intervalo de interseção, verificar se tem duração >= intervalo_min
        for start, end in intersecao:
            duracao = (end - start).total_seconds() / 60
            if duracao >= intervalo_min:
                # adiciona o início desse bloco
                horarios_finais.append(start)

    return sorted(horarios_finais)

# -------------------------
# Fim do arquivo
# -------------------------