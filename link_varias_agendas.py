import streamlit as st
from ics import Calendar
import requests
from datetime import datetime, timedelta
import pandas as pd


# Dicionário com todas as agendas disponíveis
agendas_disponiveis = {
    "Na": "https://calendar.google.com/calendar/ical/natalia.rubirapita%40gmail.com/private-d6e1ae0f68fa812f4162190421d6e021/basic.ics",
    "So": "https://calendar.google.com/calendar/ical/sofiaaaze%40gmail.com/private-8677517340f477993ca163207c7e0d5e/basic.ics",
    "Ac": "https://calendar.google.com/calendar/ical/e6d8f080887484fc3d682ef695210627df5d203bc0b78f605779df9ef9f5bb98%40group.calendar.google.com/private-deb95354e9a7a6b88ae40ce4451aa11a/basic.ics",
    "Hc": "https://calendar.google.com/calendar/ical/0500442c50cd217b6cc295c9ca032d4e9126d03f81996f38b7ff92b969f68111%40group.calendar.google.com/private-3dd7bd09f3491bf3d181ef9608f1289c/basic.ics",
    "Ag": "https://calendar.google.com/calendar/ical/arianegonzaga1%40gmail.com/private-8a03d7076d204f94466e21584afcc4dc/basic.ics",
    "Em": "https://calendar.google.com/calendar/ical/eduardamanke%40gmail.com/private-22bc0ea8642f7ef3788530083924d45c/basic.ics",
    "Hs": "https://calendar.google.com/calendar/ical/4ac5787699da201ab1014427719ea0140ac174efc7b915c75a5ea1e00c6e9c78%40group.calendar.google.com/private-9aa3911adff242d6b4a164bbad4e7c19/basic.ics",
    "Vi": "https://calendar.google.com/calendar/ical/violetaglyra%40gmail.com/private-67ee80703c7c4dc3a95b5ca8a63f605a/basic.ics",
    "Yr": "https://calendar.google.com/calendar/ical/yanraimundo1%40gmail.com/private-d5d28fb4da4fea715729b849a422fa66/basic.ics"
    # Adicione mais agendas se quiser
}
st.title("📅 Analisador de Horários em Comum")

# Seleção de agendas
agendas_selecionadas = st.multiselect(
    "Escolha as agendas que quer analisar:",
    options=list(agendas_disponiveis.keys())
)

# Intervalo em minutos
intervalo = st.number_input("⏱ Intervalo dos blocos (minutos):", min_value=5, max_value=180, value=30, step=5)

# Quantos dias analisar
dias = st.number_input("📅 Quantos dias analisar:", min_value=1, max_value=30, value=7)

# Botão para executar análise
if st.button("Analisar"):
    if not agendas_selecionadas:
        st.warning("Selecione pelo menos uma agenda.")
    else:
        st.write("Agendas selecionadas:", agendas_selecionadas)
        # aqui você chama a função que processa os arquivos .ics

# Filtrar apenas agendas válidas
agendas_selecionadas = {}
for sigla in selecionadas:
    if sigla in agendas_disponiveis:
        agendas_selecionadas[sigla] = agendas_disponiveis[sigla]
    else:
        print(f"Atenção: a sigla '{sigla}' não existe e será ignorada.")

if not agendas_selecionadas:
    print("Nenhuma agenda válida selecionada. Encerrando.")
    exit()

print("\nAgendas selecionadas:", ", ".join(agendas_selecionadas.keys()))

# Função para baixar e ler .ics
def ler_agenda(url):
    r = requests.get(url)
    c = Calendar(r.text)
    eventos = []
    for e in c.events:
        inicio = e.begin.datetime.replace(tzinfo=None)  # remove timezone
        fim = e.end.datetime.replace(tzinfo=None)      # remove timezone
        eventos.append((inicio, fim, e.name))
    return eventos


# Baixar e juntar todos os eventos
todas_agendas = {}
for sigla, link in agendas_selecionadas.items():
    eventos = ler_agenda(link)
    todas_agendas[sigla] = eventos

# Determinar período de análise (ex.: próximo dia inteiro)
hoje = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
fim_do_dia = hoje.replace(hour=18)

# Criar timeline de 15 minutos
intervalo = timedelta(minutes=15)
horarios = []
t = hoje
while t < fim_do_dia:
    horarios.append(t)
    t += intervalo

# Verificar horários livres por agenda
livres_por_agenda = {}
for sigla, eventos in todas_agendas.items():
    livres = []
    for h in horarios:
        ocupado = False
        for inicio, fim, nome in eventos:
            if inicio <= h < fim:
                ocupado = True
                break
        if not ocupado:
            livres.append(h)
    livres_por_agenda[sigla] = livres

# Encontrar horários livres em comum
horarios_comuns = []
for h in horarios:
    if all(h in livres_por_agenda[sigla] for sigla in agendas_selecionadas):
        horarios_comuns.append(h)

if horarios_comuns:
    print("\nHorários livres em comum:")
    for h in horarios_comuns:
        print(h.strftime("%Y-%m-%d %H:%M"))
else:
    print("\nNão há horários livres em comum.")
    print("Eventos que estão impedindo cada agenda:")
    for sigla, eventos in todas_agendas.items():
        print(f"\nAgenda {sigla}:")
        for inicio, fim, nome in eventos:
            if inicio < fim_do_dia and fim > hoje:
                print(f"{inicio.strftime('%H:%M')} - {fim.strftime('%H:%M')} | {nome}")
