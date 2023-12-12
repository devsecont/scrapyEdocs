from datetime import datetime, timedelta

dias_semana = ['domingo', 'segunda-feira', 'terça-feira', 'quarta-feira', 'quinta-feira', 'sexta-feira', 'sábado']


def getResumoCustodiaProcesso(response):
	descricao_processo = response.css('span.mdc-typography--body1::text').get()
	custodia = response.css('span.mdc-typography--body2::text')[1].get()
	return descricao_processo, custodia


def getUltimoTramiteProcesso(response):
	infos_internas = response.xpath('./span')
	divTramite = infos_internas[1]
	nomesTramite = divTramite.xpath('./span')[1]
	autorNome = nomesTramite.css('.mdc-typography--body2::text')[0].get()
	autorLocal = nomesTramite.css('.mdc-typography--caption::text')[0].get()

	divDataTramite = infos_internas[0]
	dataText = divDataTramite.css('.mdc-typography--caption::text')[0].get()
	hoje = datetime.now().strftime('%d/%m/%Y')
	if any(substring in dataText.lower() for substring in ['hoje', 'segundos', 'minutos', 'horas']):
		dataText = hoje
	elif any(substring in dataText.lower() for substring in ['ontem']):
		dataText = (datetime.now() + timedelta(days=-1)).strftime('%d/%m/%Y')
	elif any(substring in dataText.lower() for substring in dias_semana):
		aux_dias_semana = ''
		for d in dias_semana:
			if d in dataText.lower():
				aux_dias_semana = d
		dias_retroativo = (datetime.now() + timedelta(days=dias_semana.index(aux_dias_semana) * -1)).strftime(
			'%d/%m/%Y')
		dataText = dias_retroativo

	else:
		dataText = dataText[0:11].lower()

	data_tramite = dataText
	autor = f'{autorNome} - {autorLocal}'
	return data_tramite, autor


def getAutuacaoProcesso(response):
	autuacao = response.css('.mdc-typography--body1::text')[0].get()[0:11]
	return autuacao


def getAutadoPorProcesso(response):
	divAutuadoPor = response.xpath('./span')[0]
	nomesAutuadoPor = divAutuadoPor.xpath('./span')[0]
	autorNome = nomesAutuadoPor.css('.mdc-typography--body2::text')[0].get()
	autorLocal = nomesAutuadoPor.css('.mdc-typography--caption::text')[0].get()
	return f'{autorNome} - {autorLocal}'


def getClasseDocumentalProcesso(response):
	clss = response.css('.scd-classe-documental-termo-completo')[0].css('.mdc-typography--body2::text')
	cd_1 = clss[1].get() if len(clss) >= 2 else ''
	cd_2 = clss[2].get() if len(clss) >= 3 else ''
	cd_3 = clss[3].get() if len(clss) >= 4 else ''
	cd_4 = clss[4].get() if len(clss) >= 5 else ''
	cd_5 = clss[5].get() if len(clss) >= 6 else ''
	return cd_1, \
		cd_2, \
		cd_3, \
		cd_4, \
		cd_5


def getProtocoloSigefes(response):
	protocolo = response.css('.mdc-typography--body2::text').get()
	return protocolo


def getEncerrrado(response):
	encerrado = True if len(response.css('.scd-tag--processo-encerrado')) > 0 else False
	return encerrado


def getDadosProcesso(response, num_processo: str):
	detalhes = response.css('.scd-layout-grid__inner--compacto')[0].css('.mdc-layout-grid__cell')

	'''
		Mapeamento de Informações
		0: Resumo e Custodia
		1: Nada (Seta Card)
		2: Ultimo Trâmite
		3: Autuação
		4: Autuado Por
		5: Classe Documental
		6: Protocolo SIGEFES
		7: Encerrado
	'''

	descricao_processo = ''
	custodia = ''
	dataUltimoTramite = ''
	ultimoTramite = ''
	autuacao = ''
	autuadoPor = ''
	classDoc_1 = ''
	classDoc_2 = ''
	classDoc_3 = ''
	classDoc_4 = ''
	classDoc_5 = ''
	protocoloSigefes = ''

	for indice in range(len(detalhes)):
		if indice == 0:
			descricao_processo, custodia = getResumoCustodiaProcesso(detalhes[indice])
			encerrado = getEncerrrado(detalhes[indice])
		elif indice == 2:
			dataUltimoTramite, ultimoTramite = getUltimoTramiteProcesso(detalhes[indice])
		elif indice == (3 if len(detalhes) == 7 else 4):
			autuacao = getAutuacaoProcesso(detalhes[indice])
		elif indice == (4 if len(detalhes) == 7 else 5):
			autuadoPor = getAutadoPorProcesso(detalhes[indice])
		elif indice == (5 if len(detalhes) == 7 else 6):
			classDoc_1, classDoc_2, classDoc_3, classDoc_4, classDoc_5 = getClasseDocumentalProcesso(detalhes[indice])
		elif indice == (6 if len(detalhes) == 7 else 7):
			protocoloSigefes = getProtocoloSigefes(detalhes[indice])

	return {'protocolo' : num_processo,
			'resumo'    : descricao_processo.replace('\n', '').replace('\r', '').replace("'", "''"),
			'custodia'  : custodia.replace('\n', '').replace('\r', '').replace("'", "''"),
			'data_ultimo_tramite': dataUltimoTramite.replace('\n', '').replace('\r', ''),
			'ultimo_tramite'     : ultimoTramite.replace('\n', '').replace('\r', '').replace("'", "''"),
			'data_autuacao'      : autuacao.replace('\n', '').replace('\r', ''),
			'autuado_por'        : autuadoPor.replace('\n', '').replace('\r', '').replace("'", "''"),
			'classe_documental_1': classDoc_1.replace('\n', '').replace('\r', ''),
			'classe_documental_2': classDoc_2.replace('\n', '').replace('\r', ''),
			'classe_documental_3': classDoc_3.replace('\n', '').replace('\r', ''),
			'classe_documental_4': classDoc_4.replace('\n', '').replace('\r', ''),
			'classe_documental_5': classDoc_5.replace('\n', '').replace('\r', ''),
			'protocolo_sigefes'  : f"'{protocoloSigefes}'".replace('\n', '').replace('\r', ''),
			'encerrado': encerrado}


def getAtosProcesso(response, num_processo: str):
	card_ato = response.css('#card-atos')
	rows_atos = card_ato.css('td')
	atos = []
	for td in rows_atos:
		tipo = td.xpath('./span/span/text()')[0].get().strip()

		data = td.css('span.scd-span-inline::text')[3].get().strip().replace('em', '').replace('\n', '').replace('\r', '')[0:10].strip()

		textos_realizados = td.xpath('./div/span/span/span/text()')
		nomes_realizados = []
		for n in textos_realizados:
			nomes_realizados.append(n.get())
		realizado_por = ' '.join(nomes_realizados).strip()

		if tipo in ['Despacho', 'Avocamento', 'Ajuste de Custódia']:
			para_textos = td.xpath('./div/span/span/text()')
			nomes_para = []
			for n in para_textos:
				nomes_para.append(n.get())
			para = ' '.join(nomes_para).strip()
		else:
			para = ''

		if tipo == 'Autuação':
			local = td.xpath('./div/span/span/text()')[0].get().strip()
		else:
			local = ''

		atos.append({'processo_protocolo': num_processo, 'tipo': tipo, 'data': data, 'realizado_por': realizado_por.replace("'", "''"), 'para': para.replace("'", "''"), 'local': local})
	return atos
