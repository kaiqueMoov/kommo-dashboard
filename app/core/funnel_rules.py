import unicodedata


def normalize_text(value: str | None) -> str:
    if not value:
        return ""

    value = unicodedata.normalize("NFD", str(value))
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    return value.strip().lower()


FUNNELS = {
    "CPA": {
        "pipeline_aliases": [
            "cpa",
            "trafego pago",
            "lead novo trafego pago",
        ],
        "stages": [
            "Etapa de leads de entrada",
            "Solicitações",
            "Lead Novo Tráfego Pago",
            "Liguei",
            "Mensagem Enviada",
            "Respondeu a Primeira Mensagem",
            "SQL",
            "Orçamento Enviado",
            "Em Negociação",
            "Aguardando Documentos",
            "Subir Ficha",
            "Em Análise",
            "Aprovado Para Contratação",
            "Venda ganha",
        ],
    },
    "FS": {
        "pipeline_aliases": [
            "fs",
            "funil seguros",
            "seguro auto",
        ],
        "stages": [
            "Etapa de leads de entrada",
            "Novo Lead",
            "Mensagem Enviada",
            "Respondeu a Primeira Mensagem",
            "Cálculo Enviado",
            "Cálculo Respondido",
            "Proposta Gerada",
            "Aguardando Vistoria",
            "Em Processo de Emissão",
            "Indicação Vida",
            "Venda ganha",
        ],
    },
    "SEGURO_SAUDE": {
        "pipeline_aliases": [
            "funil seguro saude",
            "seguro saude",
            "saude",
            "saúde",
        ],
        "stages": [
            "Etapa de leads de entrada",
            "Novo Lead Cadastrado",
            "Renovações",
            "Responderam Sim",
            "Sair da Lista",
            "Outras Respostas do Disparo",
            "Mensagem Enviada",
            "Respondeu com Dados",
            "Cotação Enviada",
            "Respondeu Cotação",
            "Aguardando Documentação",
            "Análise Operadora",
            "Aguardando Pagamento",
            "Renovação Concluída",
            "Venda ganha",
        ],
    },
    "SEGURO_VIDA": {
        "pipeline_aliases": [
            "funil seguro de vida",
            "seguro de vida",
            "vida",
        ],
        "stages": [
            "Etapa de leads de entrada",
            "Prospecção",
            "Mensagem Enviada",
            "Respondeu a Primeira Mensagem",
            "Cálculo Enviado",
            "Em Andamento",
            "Proposta Gerada",
            "Em Análise Seguradora",
            "Proposta Recusada",
            "Venda ganha",
        ],
    },
}


def detect_funnel_type(pipeline_name: str | None) -> str:
    normalized_pipeline = normalize_text(pipeline_name)

    for funnel_key, config in FUNNELS.items():
        for alias in config["pipeline_aliases"]:
            if normalize_text(alias) in normalized_pipeline:
                return funnel_key

    return "OUTROS"


def get_stage_order(funnel_type: str, status_name: str | None) -> int:
    if funnel_type not in FUNNELS:
        return 999

    normalized_status = normalize_text(status_name)

    for index, stage in enumerate(FUNNELS[funnel_type]["stages"], start=1):
        if normalize_text(stage) == normalized_status:
            return index

    return 999