# sistema-organizacao-pet
# sistema-organizacao-pet
# para rodar o código, tem que ter dado "pip install streamlit" no terminal do vscode
# para rodar o pacote, tem que rodar: streamlit run 1ajustes.py , sendo esse 1ajustes.py o meu arquivo em que estou escrevendo os primeiros ajustes ao código

# Também temos que baixar: 1ajustes.py (escrever esse comando no terminal)
# após isso, correr novamente: streamlit run 1ajustes.py

# Aqui começa os comentários de quando rodamos a parte do código que contém a lógica
# mudei o cache para a cada 1 minuto recarregar, e não a cada 5
# aqui é o "coração do código", a partir da linha 26
# essa função chamada carregar_eventos() é quem: baixa o arquivo de agenda (.ics) de cada pessoa (usando o link do Google Calendar); lê e “expande” os eventos dentro do período que você pediu (por exemplo, 7 dias); formata os dados (inicio, fim e nome do evento) para que o resto do código consiga comparar horários.

# def carregar_eventos(url: str, dias_a_frente: int) -> list:
# define a função que recebe:
# url: o link .ics do Google Calendar da pessoa; dias_a_frente: quantos dias pra frente você quer olhar (ex: 7 dias); -> list indica que ela devolve uma lista de eventos.

# inicio_periodo e fim_periodo é o que pega a data e hora atuais no fuso de São Paulo; calcula o final do período (ex: hoje + 7 dias); esse intervalo define o pedaço de agenda que vamos buscar.

# lista_eventos_brutos = events(url, start=inicio_periodo, end=fim_periodo): aqui entra a biblioteca icalevents, que faz todo o trabalho pesado:
# baixa o arquivo .ics da url; interpreta o calendário (incluindo eventos recorrentes, tipo “toda segunda às 10h”); devolve uma lista de objetos evento dentro do intervalo pedido.

# cria um dicionário simples:
# eventos_formatados.append({
   # "inicio": inicio,
   # "fim": fim,
   # "nome": evento.summary
# })
# cada evento vira um dicionário com três campos: inicio: quando começa; fim: quando termina nome: o título do evento (ex: “PET Reunião”).

# return eventos_formatados: depois de converter tudo, devolve a lista de eventos prontos.
# ex:[ {'inicio': 2025-10-20 14:00, 'fim': 2025-10-20 15:00, 'nome': 'PET reunião'},{'inicio': 2025-10-21 10:00, 'fim': 2025-10-21 11:00, 'nome': 'Aula'},]

# o bloco try / except: except Exception as e:
    # st.error(f"Falha ao carregar a agenda da URL. Erro: {e}")
    # return []

# para o código funcionar, é necessário instalar as dependencias:
# no terminal: pip3 install streamlit pytz pandas icalevents
# e rodar "streamlit run 1ajustes.py" pro código funcionar, e abrir a interface gráfica

# Sobre o pop-up do Pylance Pode clicar No agora; é só sugestão de type checking. Não afeta a execução.