PIPELINE_LABELS = {
    0: "Sem pipeline",
    # Exemplo:
    # 1234567: "Assinatura",
    # 2345678: "Seguros",
}

STATUS_LABELS = {
    0: "Sem status",
    # Exemplo:
    # 11111111: "Novo lead",
    # 22222222: "Respondeu 1ª mensagem",
    # 33333333: "SQL",
    # 44444444: "Ganho",
    # 55555555: "Perdido",
}


def get_pipeline_label(pipeline_id: int | None) -> str:
    if not pipeline_id:
        return "Sem pipeline"
    return PIPELINE_LABELS.get(pipeline_id, f"Pipeline {pipeline_id}")


def get_status_label(status_id: int | None) -> str:
    if not status_id:
        return "Sem status"
    return STATUS_LABELS.get(status_id, f"Status {status_id}")