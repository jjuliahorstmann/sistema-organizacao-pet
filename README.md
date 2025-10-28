# 📆📘 sistema-organizacao-pet
Este projeto tem como objetivo desenvolver um sistema voltado à organização de horários e reuniões do PET Engenharia de Produção, capaz de ler as agendas dos integrantes, identificar horários disponíveis em comum e exibir os resultados de maneira visual e intuitiva.
## 🧠 O que o sistema faz (resumo):

- Baixa eventos das agendas (ICS) e considera o fuso America/Sao_Paulo.
- Marca como ocupados eventos que batem com constantes.json.
- Encontra:
 Horários PET em comum (eventos que começam com “PET”) e Janelas livres dentro do horário comercial PET (08:00–22:00)

## 🚀 Começando
Estas instruções permitem colocar o projeto para rodar na sua máquina para desenvolvimento e testes.

✅ Pré-requisitos:
- Python 3.10+
- macOS / Windows / Linux
- Acesso às URLs ICS das agendas

## 📦 Instalar dependências:
 ```bash
pip install -r requirements.txt
```
## 🗂️ Arquivos necessários:
- agendas.json
- constantes.json

## ▶️ Como rodar:
No terminal, dentro da pasta do projeto rode:
```bash
streamlit run main.py
```
Caso dê algum erro de leitura, não reconheça o o comando streamlit ou o PATH esteja errado, use o seguinte comando:
```bash
python -m streamlit run main.py
```
## 🧯 Problemas comuns
- Erro de certificado ao baixar ICS:

    Para isso, atualize o certifi:
    ```bash
    pip install --upgrade certifi
    ```
- agendas.json ou constantes.json não encontrados:

    Verifique se estão no mesmo diretório do script e se o JSON é válido.

## 💡Alguns lembretes:
 - Se ao escrever os comandos no terminal aparecer algo pedindo email, apenas dar enter sem nada escrito

 - O cache recarrega a cada 1 minuto

- Lembre que para o código funcionar, é necessário instalar as dependências:

 ```bash 
 pip3 install:  
 ```
 - streamlit 
 - pytz 
 - pandas 
 - icalevents
 - e todas que estão no requirement.txt

- E rodar "streamlit run main.py" pro código funcionar, e abrir a interface gráfica.

- Sobre o pop-up do Pylance: Pode clicar No agora; é só sugestão de type checking. Não afeta a execução.