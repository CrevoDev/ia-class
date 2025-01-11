class DocumentDTO:
    def __init__(self, link, numero_cnj, instancia, sistema, tribunal, tipo_documento, ha_liminar, tutela_antecipada, audiencia_designada, notificacao_extrajudicial, oficio, prazo_tutela_antecipada, tipo_audiencia, data_audiencia, hora_audiencia):
        self.link = link
        self.numero_cnj = numero_cnj
        self.instancia = instancia
        self.sistema = sistema
        self.tribunal = tribunal
        self.tipo_documento = tipo_documento
        self.ha_liminar = ha_liminar
        self.tutela_antecipada = tutela_antecipada
        self.audiencia_designada = audiencia_designada
        self.notificacao_extrajudicial = notificacao_extrajudicial
        self.oficio = oficio
        self.prazo_tutela_antecipada = prazo_tutela_antecipada
        self.tipo_audiencia = tipo_audiencia
        self.data_audiencia = data_audiencia
        self.hora_audiencia = hora_audiencia