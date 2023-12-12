import math
import time
import mysql.connector
from scrapy import Request, Spider
from scrapy_splash import SplashRequest
import pandas as pd
import base64
from datetime import date
from datetime import datetime
from sqlalchemy import create_engine

from ExtracaoEdocs.processos_informacoes import getDadosProcesso, getAtosProcesso


class ExtracaoEdocsSpider(Spider):
	start_time = None
	end_time = None
	name = "ExtracaoEdocs"
	starting_url = "https://e-docs.es.gov.br/Internal"
	# Lembrar da Tag de Encerrados, pois sem ela o script irá pegar todos os documentos, encerrados e em andamento
	# termo_pesquisa = '?TermoBusca=&IdCaixa=&IdClasse=&Ordenacao=desc&localAutuacaoId=&localAutuacaoLabel=&localizacaoAtualId=ffa40cea-b653-4d93-b784-02b9cc981b6b&localizacaoAtualLabel=GOVES+-+DER+-+GEFIN+-+GERENCIA+DE+FINANCAS%2C+ORCA.+E+ARRECADACAO+-+GEFIN&autuadorId=&autuadorLabel=&localTramitacaoId=&localTramitacaoLabel=&tramitadoPorId=&tramitadoPorLabel=&interessadoId=&interessadoLabel=&NomeClasse=&dataAutuacaoIniLabel=&dataAutuacaoFimLabel=&dataTramiteIniLabel=&dataTramiteFimLabel=&UltimoAtoTipo=0&SinalizacaoId=&SituacaoEmAndamento=true&SituacaoEncerrado=true'
	cookies_dict = {}
	lua_login_script = '''
    function main(splash, args)
        splash:init_cookies(splash.args.cookies)
        assert(splash:go(args.url))
        assert(splash:wait(splash.args.wait))
        splash:set_viewport_full()
        local login_acesso_cidadao_btn = splash:select('body > div > div > div > div > div > input')
        login_acesso_cidadao_btn:click()
        local cpf_input = splash:select('input[id=login]')
        cpf_input:send_text("18461304764")
        assert(splash:wait(0.2))
        local password_input = splash:select('input[id=senha]')
        password_input:send_text("Sintel@025")
        assert(splash:wait(0.2))
        local enter_button = splash:select('input[id=entrar]')
        enter_button:click()
        assert(splash:wait(2))
        return {
            html=splash:html(),
            url=splash:url(),
            png=splash:png(),
            cookies=splash:get_cookies(),
        }
        end
    '''
	df = []
	df_atos = []
	total_processos = 0
	total_paginas = 0
	dbconnection = None
	dbcursor = None

	def start_requests(self):
		if self.att_sql == '1':
			self.dbconnection = mysql.connector.connect(
				host="127.0.0.1",
				user="dev",
				password="Dev_Secont_159",
				database="extracao_edocs"
			)
			self.dbcursor = self.dbconnection.cursor()
			self.dbcursor.execute("DELETE FROM processos")
			self.dbcursor.execute("DELETE FROM atos")
			self.dbconnection.commit()

		self.start_time = time.time()
		print("Script Iniciado")
		yield SplashRequest(url=self.starting_url, callback=self.goToPesquisa, endpoint='execute', args={
			'width'     : 1000,
			'wait'      : 0.5,
			'lua_source': self.lua_login_script
		})

	def goToPesquisa(self, response):
		self.cookies_dict = {cookie['name']: cookie['value'] for cookie in response.data['cookies']}
		# print(f"\n\n\n\n\nCookies: \n{cookies_dict}\n\n\n\n\n")

		imgdata = base64.b64decode(response.data['png'])
		filename = 'after_login.png'
		with open(filename, 'wb') as f:
			f.write(imgdata)

		url = f'https://e-docs.es.gov.br/processo/Todos{self.termo_pesquisa}'
		print("URL:", url)
		yield Request(url=url, cookies=self.cookies_dict, callback=self.processos)

	def processos(self, response):
		paginas_results = response.css('span.paging-results::text').get()
		self.total_processos = int(paginas_results.split('de')[::-1][0].strip())
		self.total_paginas = math.ceil(self.total_processos / 25)

		# Caso nao tenha termo de pesquisa, trocar pag&page= para ?page=
		processos_urls = [f'https://e-docs.es.gov.br/processo/Todos{self.termo_pesquisa}&page={p}' for p in
						  range(1, self.total_paginas+1)]
		# print(processos_urls)
		# print(f'\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n{processos_urls}\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n')

		for url in processos_urls:
			yield Request(url=url, cookies=self.cookies_dict, callback=self.pages_url)

	def pages_url(self, response):
		processos = response.css('.scd-action-linha-processo')
		for processo in processos:
			url = processo.css('div::attr(href)').get()
			yield Request(f"https://e-docs.es.gov.br{url}", cookies=self.cookies_dict, callback=self.getProcessosInfo)
		pass

	def getProcessosInfo(self, response):
		num_processo = response.url.split('/')[::-1][0]
		if self.att_sql != '1':
			self.df.append(getDadosProcesso(response, num_processo))
			self.df_atos += getAtosProcesso(response, num_processo)

		if self.att_sql == '1':
			dados_processo = getDadosProcesso(response, num_processo)
			insert_processo_sql = f'''
				INSERT INTO processos 
				(
				protocolo,
				resumo,
				custodia,
				data_ultimo_tramite,
				ultimo_tramite,
				data_autuacao,
				autuado_por,
				classe_documental_1,
				classe_documental_2,
				classe_documental_3,
				classe_documental_4,
				classe_documental_5,
				protocolo_sigefes,
				encerrado
				)
				VALUES (
				'{dados_processo['protocolo']}',
				'{dados_processo['resumo']}',
				'{dados_processo['custodia']}',
				'{dados_processo['data_ultimo_tramite']}',
				'{dados_processo['ultimo_tramite']}',
				'{dados_processo['data_autuacao']}',
				'{dados_processo['autuado_por']}',
				'{dados_processo['classe_documental_1']}',
				'{dados_processo['classe_documental_2']}',
				'{dados_processo['classe_documental_3']}',
				'{dados_processo['classe_documental_4']}',
				'{dados_processo['classe_documental_5']}',
				{dados_processo['protocolo_sigefes']},
				'{1 if dados_processo['encerrado'] else 0}'
				)
			'''
			self.dbcursor.execute(insert_processo_sql)
			atos_processo = getAtosProcesso(response, num_processo)
			for row in atos_processo:
				insert_ato_sql = f'''
				INSERT INTO atos (processo_protocolo, tipo, data, realizado_por, para, local) VALUES (
				'{row['processo_protocolo']}',
				'{row['tipo']}',
				'{row['data']}',
				'{row['realizado_por']}',
				'{row['para']}',
				'{row['local']}'
				)
				'''
				self.dbcursor.execute(insert_ato_sql)
			self.dbconnection.commit()

	def close(self, reason):

		self.end_time = time.time()
		final_df = pd.DataFrame(self.df)
		hoje = datetime.now().strftime('%Y-%m-%d')
		if self.att_sql != '1':
			final_df.to_csv(f'./dados/{self.nome_arquivo}_{hoje}.csv', sep=';', encoding='utf-8-sig', index=False)
		print(f'Total de processos no DF: {len(final_df)}')
		elapsed_time = self.end_time - self.start_time
		print(f'Finalizado em {elapsed_time} segundos'
			  f'\nTotal de processos: {self.total_processos}'
			  f'\nTotal Paginas: {self.total_paginas}\n')