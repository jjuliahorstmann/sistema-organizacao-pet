import json
import pytz
from datetime import datetime, timedelta
from icalevents.icalevents import events
import streamlit as st

# Configurações globais
FUSO_HORARIO_LOCAL = pytz.timezone('America/Sao_Paulo')

def carregar_agendas(arquivo_json: str = "agendas.json") -> dict:
    
   # Carrega o arquivo agendas.json do mesmo diretório do backend.py.
   # Retorna um dicionário com as siglas e URLs das agendas.
    
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
    """Encontra blocos de tempo onde TODOS os membros têm algum evento 'PET'."""
    if len(eventos_por_membro) < 1:
        return []
    inicio_periodo = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    fim_periodo = inicio_periodo + timedelta(days=dias)
    horarios_comuns = []
    tempo_atual = inicio_periodo

    while tempo_atual < fim_periodo:
        if 8 <= tempo_atual.hour < 22:
            todos_ocupados_com_pet = True
            for _, eventos in eventos_por_membro.items():
                if not any(
                    e['nome'] and e['nome'].strip().upper().startswith("PET")
                    and e['inicio'] <= tempo_atual < e['fim']
                    for e in eventos
                ):
                    todos_ocupados_com_pet = False
                    break
            if todos_ocupados_com_pet:
                horarios_comuns.append(tempo_atual)
        tempo_atual += timedelta(minutes=intervalo_min)
    return horarios_comuns


def calcular_horarios_livres(eventos_todos: list, intervalo_min: int, dias: int) -> list:
    """Calcula os horários livres com base em uma lista de todos os eventos."""
    inicio_periodo = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    fim_periodo = inicio_periodo + timedelta(days=dias)
    horarios_livres = []
    tempo_atual = inicio_periodo

    while tempo_atual < fim_periodo:
        if 8 <= tempo_atual.hour < 22:
            if not any(e["inicio"] <= tempo_atual < e["fim"] for e in eventos_todos):
                horarios_livres.append(tempo_atual)
        tempo_atual += timedelta(minutes=intervalo_min)
    return horarios_livres

def quebra_evento(evento, nome)