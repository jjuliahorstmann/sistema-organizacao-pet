import json
import pytz
import os
import re
from datetime import datetime, timedelta
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
def carregar_eventos(url: str, dias_a_frente: int) -> list:
    """Baixa e processa eventos de uma URL, expandindo eventos recorrentes."""
    inicio_periodo = datetime.now(FUSO_HORARIO_LOCAL)
    fim_periodo = inicio_periodo + timedelta(days=dias_a_frente)
    eventos_formatados = []

    try:
        lista_eventos_brutos = events(url, start=inicio_periodo, end=fim_periodo)

        for evento in lista_eventos_brutos:
            inicio = evento.start.astimezone(FUSO_HORARIO_LOCAL).replace(tzinfo=None)
            fim = evento.end.astimezone(FUSO_HORARIO_LOCAL).replace(tzinfo=None)
            eventos_formatados.append({
                "inicio": inicio,
                "fim": fim,
                "nome": evento.summary
            })
        return eventos_formatados

    except Exception as e:
        st.error(f"Falha ao carregar a agenda da URL. Erro: {e}")
        return []


def encontrar_horarios_pet_comuns(eventos_por_membro: dict, intervalo_min: int, dias: int) -> list:
    """
    Encontra blocos de tempo onde TODOS os membros têm algum evento 'PET',
    ignorando horários que coincidam com eventos reservados (constantes.json).
    """
    if len(eventos_por_membro) < 1:
        return []

    CONSTANTES = carregar_constantes()
    inicio_periodo = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    fim_periodo = inicio_periodo + timedelta(days=dias)
    horarios_comuns = []
    tempo_atual = inicio_periodo

    while tempo_atual < fim_periodo:
        if 8 <= tempo_atual.hour < 22:
            todos_ocupados_com_pet = True
            reservado_no_horario = False

            for _, eventos in eventos_por_membro.items():
                # Verifica se algum evento reservado ocorre neste horário
                for e in eventos:
                    if e["inicio"] <= tempo_atual < e["fim"]:
                        if eh_evento_reservado(e.get("nome", ""), CONSTANTES):
                            reservado_no_horario = True
                            break
                if reservado_no_horario:
                    break

                # Verifica se há um evento PET neste horário
                if not any(
                    e['nome'] and e['nome'].strip().upper().startswith("PET")
                    and e['inicio'] <= tempo_atual < e['fim']
                    for e in eventos
                ):
                    todos_ocupados_com_pet = False
                    break

            # Adiciona horário comum apenas se todos estão em PET e não há evento reservado
            if todos_ocupados_com_pet and not reservado_no_horario:
                horarios_comuns.append(tempo_atual)

        tempo_atual += timedelta(minutes=intervalo_min)

    return horarios_comuns


def calcular_horarios_livres(eventos_todos: list, intervalo_min: int, dias: int) -> list:
    """
    Calcula os horários livres com base em uma lista de todos os eventos.
    Agora também considera como 'ocupado' qualquer evento que tenha nome
    reservado conforme definido em constantes.json.
    """
    CONSTANTES = carregar_constantes()

    inicio_periodo = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    fim_periodo = inicio_periodo + timedelta(days=dias)
    horarios_livres = []
    tempo_atual = inicio_periodo

    while tempo_atual < fim_periodo:
        if 8 <= tempo_atual.hour < 22:
            ocupado = False
            for e in eventos_todos:
                if e["inicio"] <= tempo_atual < e["fim"]:
                    if eh_evento_reservado(e.get("nome", ""), CONSTANTES):
                        ocupado = True
                        break
                    else:
                        ocupado = True
                        break
            if not ocupado:
                horarios_livres.append(tempo_atual)
        tempo_atual += timedelta(minutes=intervalo_min)
    return horarios_livres