import pytz
from datetime import datetime, timedelta
from icalevents.icalevents import events
import streamlit as st

# Configurações globais
FUSO_HORARIO_LOCAL = pytz.timezone('America/Sao_Paulo')

AGENDAS = {
    "Ac": "https://calendar.google.com/calendar/ical/e6d8f080887484fc3d682ef695210627df5d203bc0b78f605779df9ef9f5bb98%40group.calendar.google.com/private-deb95354e9a7a6b88ae40ce4451aa11a/basic.ics",
    "Ag": "https://calendar.google.com/calendar/ical/arianegonzaga1%40gmail.com/private-8a03d7076d204f94466e21584afcc4dc/basic.ics",
    "Em": "https://calendar.google.com/calendar/ical/eduardamanke%40gmail.com/private-22bc0ea8642f7ef3788530083924d45c/basic.ics",
    "Hc": "https://calendar.google.com/calendar/ical/0500442c50cd217b6cc295c9ca032d4e9126d03f81996f38b7ff92b969f68111%40group.calendar.google.com/private-3dd7bd09f3491bf3d181ef9608f1289c/basic.ics",
    "Hs": "https://calendar.google.com/calendar/ical/helena.sta.sch%40gmail.com/private-bdba0cc5df7a18ec5dfee505e05ac38c/basic.ics",
    "Jh": "https://calendar.google.com/calendar/ical/4ac5787699da201ab1014427719ea0140ac174efc7b915c75a5ea1e00c6e9c78%40group.calendar.google.com/private-9aa3911adff242d6b4a164bbad4e7c19/basic.ics",
    "Lc": "https://calendar.google.com/calendar/ical/lauracosta.pet%40gmail.com/private-0297a23e347137c4d1f4a600cbfddc3c/basic.ics",
    "Ma": "https://calendar.google.com/calendar/ical/c096fc3ec6221a98105d88c53f53c4554b4cad8c663389758474d1f1835c8514%40group.calendar.google.com/private-888f3868a1035de3c010c943d1a67d02/basic.ics",
    "Na": "https://calendar.google.com/calendar/ical/natalia.rubirapita%40gmail.com/private-d6e1ae0f68fa812f4162190421d6e021/basic.ics",
    "Sn": "https://calendar.google.com/calendar/ical/arthur.sand.pet%40gmail.com/private-e27544fe0f57b0991e125ae3b7fa7d91/basic.ics",
    "So": "https://calendar.google.com/calendar/ical/sofiaaaze%40gmail.com/private-8677517340f477993ca163207c7e0d5e/basic.ics",
    "Vi": "https://calendar.google.com/calendar/ical/violetaglyra%40gmail.com/private-67ee80703c7c4dc3a95b5ca8a63f605a/basic.ics",
    "Yr": "https://calendar.google.com/calendar/ical/yanraimundo1%40gmail.com/private-d5d28fb4da4fea715729b849a422fa66/basic.ics"
}


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