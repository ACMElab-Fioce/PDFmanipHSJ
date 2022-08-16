from csv import excel
from gettext import find
import PyPDF2 
from datetime import datetime
import re
#import pandas as pd
import os
#......................................................

#Converte meu arquivo PDF em binário

REFERENCIAS_POSSIVEIS = ["RESIDENCIA","OUTROS"] #adicionar caso vejam alguma outra referencia
DESTINOS_POSSIVEIS = ["Residência","Transferência interna", "Mudança de leito", "Óbito", "Mudança de enfermaria", "Outro hospital"] #adicionar caso vejam alguma outra referencia
CLINICAS_POSSIVEIS = ["ANEXO (COVID-19)", "ANEXO NÃO COVID", "ANEXO-HOSPITAL DIA(NÃO COVID)", "UTI","UNIDADE A","UNIDADE B","UNIDADE C","UNIDADE D","UNIDADE E","UNIDADE F"]
def retirarCaracteresErradosIniciais(string):
    if(string[0] == ' ' or string[0] == '\n'):
        return string[1:]
    else:
        return string

def qualClinica(string):
    clinica_vetorizada = []
    clinica_vetorizada = [clinica for clinica in CLINICAS_POSSIVEIS if(clinica in string)]
    try:
        return clinica_vetorizada[0]
    except:
        return ""

def qualDestino(string):
    destino_vetorizado = []
    destino_vetorizado = [destino for destino in DESTINOS_POSSIVEIS if(destino in string)]
    try:
        return destino_vetorizado[0]
    except:
        return ""

def qualEnfermaria(string):
    tres_primeiros = string[:3]
    try:
        int(tres_primeiros)
        return tres_primeiros
    except:
        if(tres_primeiros == "UTI"):
            return tres_primeiros
        else:
            return "(COVID 19)"

def validaData(data, formato):
    # checking if format matches the date
    res = True
 
    # using try-except to check for truth value
    try:
        res = bool(datetime.strptime(data, formato))
    except ValueError:
        res = False
    
    return res

class Internacao():
    def __init__(self, caminho = r"./", tipo_raspagem = 1, caminho_arquivo = None):
        os.chdir(caminho)
        pdf_file = open(r"218010_Internacao.pdf", "rb")
        self.dados_pdf = PyPDF2.PdfFileReader(pdf_file)
    def getNumberOfPages(self):
        return self.dados_pdf.getNumPages()
    def getTextByPage(self, page):
        page -= 1
        try:
            page = self.dados_pdf.pages[page]
            dados = page.extract_text()
            return dados
        except:
            return "Erro, pagina deve ser maior ou igual a 1"
    def getNumProntuario(self):
        dados = self.getTextByPage(1)
        hifen = dados.find("-", 48)
        return retirarCaracteresErradosIniciais(dados[48:hifen-1]),hifen-1, dados[48]
    def getNomeCompleto(self):
        dados = self.getTextByPage(1)
        hifen = dados.find("-", 48)
        sexo = dados.find("Sexo", hifen)
        return retirarCaracteresErradosIniciais(dados[hifen+2:sexo]),sexo
    def getSexo(self):
        dados = self.getTextByPage(1)
        sexo = dados.find("Sexo: ")
        idade = dados.find(" Idade")
        return retirarCaracteresErradosIniciais(dados[sexo+6:idade]),idade
    def getDtNasc(self):
        dados = self.getTextByPage(1)
        idade = dados.find(" Idade: ")
        return retirarCaracteresErradosIniciais(dados[idade+8:idade+18]),idade+18
    def getIdadeEmAnos(self):
        dados = self.getTextByPage(1)
        idade = dados.find(" Idade: ")
        anos = dados.find(" ano(s)")
        return retirarCaracteresErradosIniciais(dados[idade+21:anos]),anos
    def getDataInternacao(self):
        dados = self.getTextByPage(1)
        str_data = dados.find("Profissional")
        return retirarCaracteresErradosIniciais(dados[str_data+12:str_data+22]),str_data+22
    def getReferenciaInternacao(self):
        dados = self.getTextByPage(1)
        fim_DtInternacao = self.getDataInternacao()[1]
        for exemplo in REFERENCIAS_POSSIVEIS:
            referencia = dados.find(exemplo,fim_DtInternacao,fim_DtInternacao+15)
            if(referencia != -1):
                return retirarCaracteresErradosIniciais(exemplo),referencia+len(exemplo)
        return "OUTROS",-1 #se o erro acontecer, significa que ha outro exemplo que nao consta no vetor REFERENCIAS_POSSIVEIS, necessita atualiza-lo
    def getProfissionalQueInternou(self):
        dados = self.getTextByPage(1)
        referencia = self.getReferenciaInternacao()[1]
        nome_profissional = dados.find("LEITOS",referencia)
        return retirarCaracteresErradosIniciais(dados[referencia:nome_profissional]),nome_profissional
    def getNumeroMovimentacoes(self):
        dados = self.getTextByPage(1)
        referencia = self.getProfissionalQueInternou()[1]
        inicio_movimentacao = dados.find("AltaDestino",referencia)+11
        final_movimentacao = dados.find("ADMISSÃODataClínica",inicio_movimentacao)+11
        contador = 0
        for destino in DESTINOS_POSSIVEIS:
            contador += dados.count(destino,inicio_movimentacao,final_movimentacao)
        return contador
    def getNumeroAdmissoes(self):
        dados = self.getTextByPage(1)
        inicio_movimentacao = dados.find("PrincipalProfissional")+21
        final_movimentacao = dados.find("EXAMES SOLICITADOS E REALIZADOS")
        contador = 0
        for clinica in CLINICAS_POSSIVEIS:
            contador += dados.count(clinica,inicio_movimentacao,final_movimentacao)
        return contador
    def getInfosMovimentacoes(self):
        dados = self.getTextByPage(1)
        infos = []
        referencia = self.getProfissionalQueInternou()[1]
        referencia = dados.find("AltaDestino",referencia)+12
        for i in range(self.getNumeroMovimentacoes()):
            inicio_ultima_dt_internacao = referencia
            nome_clinica = qualClinica(dados[inicio_ultima_dt_internacao+16:inicio_ultima_dt_internacao+46])
            inicio_ultima_clinica = dados.find(nome_clinica,inicio_ultima_dt_internacao)
            inicio_ultima_enfermaria = inicio_ultima_clinica+len(nome_clinica)
            nome_enfermaria = qualEnfermaria(dados[inicio_ultima_enfermaria:])
            inicio_ultima_leito = inicio_ultima_enfermaria+len(nome_enfermaria)
            inicio_ultima_dt_alta = dados.find("/",inicio_ultima_clinica)-2
            nome_destino = qualDestino(dados[inicio_ultima_dt_alta+16:inicio_ultima_dt_alta+38])
            inicio_ultima_destino = dados.find(nome_destino,inicio_ultima_dt_alta)
            infos.append({"dt_internacao":retirarCaracteresErradosIniciais(dados[inicio_ultima_dt_internacao:inicio_ultima_clinica]),"clinica":nome_clinica,"enfermaria":nome_enfermaria,"leito":dados[inicio_ultima_leito:inicio_ultima_dt_alta],"dt_alta":dados[inicio_ultima_dt_alta:inicio_ultima_destino],"destino":nome_destino})
            referencia = inicio_ultima_destino+len(nome_destino)

    def getInfosAdmissoes(self):
        dados = self.getTextByPage(1)
        infos = []
        referencia = dados.find("PrincipalProfissional")+21
        #print(dados[referencia:])
        n_admissoes = self.getNumeroAdmissoes()
        for i in range(n_admissoes):
            inicio_ultima_dt_admissao = referencia
            nome_clinica = qualClinica(dados[inicio_ultima_dt_admissao+16:inicio_ultima_dt_admissao+46])
            inicio_ultima_clinica = dados.find(nome_clinica,inicio_ultima_dt_admissao)
            inicio_ultima_queixa_e_profissional = inicio_ultima_clinica+len(nome_clinica)
            print(inicio_ultima_queixa_e_profissional)
            #nao foi possivel separar a queixa do nome do profissional pois nao identifiquei padrao para separa-los
            if(i != n_admissoes-1):
                proxima_data = dados.find("/",inicio_ultima_queixa_e_profissional)-2
            else:
                proxima_data = dados.find("\n",inicio_ultima_queixa_e_profissional)-1
            string_queixa = dados[inicio_ultima_queixa_e_profissional:proxima_data]
            infos.append({"dt_admissao":retirarCaracteresErradosIniciais(dados[inicio_ultima_dt_admissao:inicio_ultima_clinica]),"clinica":nome_clinica,"queixa_e_profissional":string_queixa})
            referencia = inicio_ultima_queixa_e_profissional+len(string_queixa)

    def getPaginaFimPrescricoes(self):
        pagina_fim_prescricao = 0
        for i in range(self.getNumberOfPages()):
            dados = self.getTextByPage(i)
            fim_prescricoes = dados.find("PRESCRIÇÕES\nNúmero")
            if(fim_prescricoes != -1):
                pagina_fim_prescricao = i
                return pagina_fim_prescricao
        return pagina_fim_prescricao
    def getExamesSolicitados(self): #FUNCIONOU, MAS ESTÁ PEGANDO NOME DO PROFISSIONAL TAMBÉM -> CONFERIR SE NECESSÁRIO CONSERTAR
        pagina_fim_prescricao = self.getPaginaFimPrescricoes()
        contador = 0
        dados = self.getTextByPage(1)
        inicio_prescricoes = dados.find("Exame\nQuantidade")
        str_exames = ''
        str_exames += dados[inicio_prescricoes+len("Exame\nQuantidade"):]

        for page in range(1,pagina_fim_prescricao):
            dados = self.getTextByPage(page+1)
            if page+1 != pagina_fim_prescricao:
                
                str_exames += dados
            else:
                fim_prescricoes = dados.find("PRESCRIÇÕES\nNúmero")
                str_exames += dados[:fim_prescricoes]
            #print(dados)
            #contador += dados.count("\n",inicio_prescricoes)
        lista_exames = str_exames.split('\n')
        exames = {}
        for index_info in range(len(lista_exames)):
            if lista_exames[index_info].isnumeric():
                exames[lista_exames[index_info-1]] = lista_exames[index_info]
       
        return exames

#PRECISA FINALIZAR ESTE METODO PORQUE NAO ESTOU LOCALIZANDO O FIM DAS PRESCRICOES E ESTOU CONTANDO COM OS \N DO RODAPE # resolvido
#print(dir(dados_pdf))
#.............................................................................

    def getPaginaFimEvolucao (self):
        pagina_fim_evolucao = 0
        for i in range(self.getNumberOfPages()):
            dados = self.getTextByPage(i)
            fim_evolucao = dados.find("IMPRIMIR TODAS ASEVOLUÇÕES")
            if(fim_evolucao != -1):
                pagina_fim_evolucao = i
                return pagina_fim_evolucao
        return pagina_fim_evolucao

    def getPaginaInicioEvolucao (self):
        pagina_inicio_evolucao = 0
        for i in range(self.getNumberOfPages()):
            dados = self.getTextByPage(i)
            inicio_evolucao = dados.find("EVOLUÇÃO\nData")
            if(inicio_evolucao != -1):
                pagina_inicio_evolucao = i
                return pagina_inicio_evolucao
        return pagina_inicio_evolucao
        
    def getEvolucao(self):
        pagina_fim_evolucao = self.getPaginaFimEvolucao()
        contador = 0
        dados = self.getTextByPage(self.getPaginaInicioEvolucao())
        inicio_evolucao = dados.find("EVOLUÇÃO\nData")
        str_evolucao = ''
        str_evolucao += dados[inicio_evolucao+len("EVOLUÇÃO\nData"):]

        for page in range(1,pagina_fim_evolucao):
            dados = self.getTextByPage(page+1)
            if page+1 != pagina_fim_evolucao:
                
                str_evolucao += dados
            else:
                fim_evolucao = dados.find("IMPRIMIR TODAS ASEVOLUÇÕES")
                str_evolucao += dados[:fim_evolucao]
        lista_evolucao = str_evolucao.split('\n')

        dic_evolucao = {}
        temp_key = ''
        for index_info_evolucao in range(len(lista_evolucao)):
            if validaData(lista_evolucao[index_info_evolucao].rstrip('-'),"%d/%m/%Y"):
                temp_key = lista_evolucao[index_info_evolucao]+lista_evolucao[index_info_evolucao+1]
                dic_evolucao[temp_key] = []
            else:
                if temp_key != '':
                    dic_evolucao[temp_key].append(lista_evolucao[index_info_evolucao])
        return dic_evolucao

        

teste = Internacao()
#print(teste.getTextByPage(2))
#print(teste.getNumProntuario())
print(teste.getExamesSolicitados())
#print(teste.getEvolucao())


# #......................................................
# #Pegando o texto extraído das páginas do arquivo PDF
# pagina1 = dados_pdf.getPage()
# texto_pagina1 = pagina1.extractText()
# texto_pagina1 = re.sub("\n", ";", texto_pagina1)

# pagina2 = dados_pdf.getPage(1)
# texto_pagina2 = pagina2.extractText()
# texto_pagina2 = re.sub("\n", ";", texto_pagina2)

# pagina3 = dados_pdf.getPage(2)
# texto_pagina3 = pagina3.extractText()
# texto_pagina3 = re.sub("\n", ";", texto_pagina3)

# #pagina4 = dados_pdf.getPage(3)
# #texto_pagina4 = pagina4.extractText()
# #texto_pagina4 = re.sub("\n", " ", texto_pagina4)


# #.....................................................
# #Armazenando em um arquivo excel
# df = pd.DataFrame({"dados_pagina1": [texto_pagina1], "dados_pagina2": [texto_pagina2], "dados_pagina3": [texto_pagina3]})
# df.to_csv("Output.csv", sep=";", index=False)
# #print(df)





