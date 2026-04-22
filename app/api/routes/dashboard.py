from datetime import datetime
import unicodedata

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.funnel_rules import detect_funnel_type, get_stage_order
from app.core.kommo_labels import get_pipeline_label, get_status_label
from app.integrations.kommo_client import KommoClient
from app.models.lead import Lead
from app.models.user import User

router = APIRouter()

EXCLUDED_SELLER_NAMES = {
    "pedro lunardini",
    "moov",
    "joao",
    "daniela santos",
    "gabriela macena",
}


def normalize_person_name(value: str | None) -> str:
    if not value:
        return ""

    value = unicodedata.normalize("NFD", str(value))
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    return value.strip().lower()


def get_excluded_user_ids(db: Session) -> list[int]:
    users = db.query(User.id, User.name).all()
    excluded_ids: list[int] = []

    for user_id, user_name in users:
        if normalize_person_name(user_name) in EXCLUDED_SELLER_NAMES:
            excluded_ids.append(user_id)

    return excluded_ids


def apply_global_exclusions(query, db: Session):
    excluded_ids = get_excluded_user_ids(db)

    if excluded_ids:
        query = query.filter(
            or_(
                Lead.responsible_user_id.is_(None),
                ~Lead.responsible_user_id.in_(excluded_ids),
            )
        )

    return query


def parse_date_param(value: str | None) -> datetime | None:
    if not value:
        return None

    value = value.strip()

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        if len(value) == 10:
            return datetime.strptime(value, "%Y-%m-%d")
        raise


def apply_date_filters(query, start: str | None, end: str | None):
    start_dt = parse_date_param(start)
    end_dt = parse_date_param(end)

    if start_dt:
        query = query.filter(Lead.created_at_kommo >= start_dt)

    if end_dt:
        query = query.filter(Lead.created_at_kommo < end_dt)

    return query


def apply_seller_filters(query, seller_ids: list[int] | None):
    if seller_ids:
        query = query.filter(Lead.responsible_user_id.in_(seller_ids))
    return query


def apply_campaign_filters(query, campaign_names: list[str] | None):
    if campaign_names:
        query = query.filter(Lead.campaign_name.in_(campaign_names))
    return query


def apply_car_filters(query, car_names: list[str] | None):
    if car_names:
        query = query.filter(Lead.car_name.in_(car_names))
    return query


def apply_finalized_filter(query, lead_finalizado: bool | None):
    if lead_finalizado is True:
        query = query.filter(Lead.is_finalized.is_(True))
    elif lead_finalizado is False:
        query = query.filter(Lead.is_finalized.is_(False))
    return query


def apply_search_filter(query, search: str | None):
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Lead.name.ilike(term),
                Lead.campaign_name.ilike(term),
                Lead.car_name.ilike(term),
                Lead.lead_source.ilike(term),
            )
        )
    return query


def apply_all_filters(
    query,
    start: str | None,
    end: str | None,
    seller_ids: list[int] | None,
    campaign_names: list[str] | None,
    car_names: list[str] | None,
    search: str | None,
    lead_finalizado: bool | None = None,
):
    query = apply_date_filters(query, start, end)
    query = apply_seller_filters(query, seller_ids)
    query = apply_campaign_filters(query, campaign_names)
    query = apply_car_filters(query, car_names)
    query = apply_finalized_filter(query, lead_finalizado)
    query = apply_search_filter(query, search)
    return query


@router.get("/summary")
def dashboard_summary(
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
    seller_ids: list[int] | None = Query(default=None),
    campaign_names: list[str] | None = Query(default=None),
    car_names: list[str] | None = Query(default=None),
    search: str | None = Query(default=None),
    lead_finalizado: bool | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(Lead)
    query = apply_global_exclusions(query, db)
    query = apply_all_filters(
        query,
        start,
        end,
        seller_ids,
        campaign_names,
        car_names,
        search,
        lead_finalizado,
    )

    total_leads = query.count()
    replied_count = query.filter(Lead.replied_first_message.is_(True)).count()
    sql_count = query.filter(Lead.sql_at.isnot(None)).count()
    won_count = query.filter(Lead.won_at.isnot(None)).count()
    lost_count = query.filter(Lead.lost_at.isnot(None)).count()
    finalized_count = query.filter(Lead.is_finalized.is_(True)).count()

    return {
        "total_leads": total_leads,
        "replied_first_message": replied_count,
        "sql_count": sql_count,
        "won_count": won_count,
        "lost_count": lost_count,
        "finalized_count": finalized_count,
    }


@router.get("/campaigns")
def dashboard_campaigns(
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
    seller_ids: list[int] | None = Query(default=None),
    campaign_names: list[str] | None = Query(default=None),
    car_names: list[str] | None = Query(default=None),
    search: str | None = Query(default=None),
    lead_finalizado: bool | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(
        Lead.campaign_name.label("campaign_name"),
        func.count(Lead.id).label("total_leads"),
        func.sum(case((Lead.replied_first_message.is_(True), 1), else_=0)).label("replied_first_message"),
        func.sum(case((Lead.sql_at.isnot(None), 1), else_=0)).label("sql_count"),
        func.sum(case((Lead.won_at.isnot(None), 1), else_=0)).label("won_count"),
        func.sum(case((Lead.lost_at.isnot(None), 1), else_=0)).label("lost_count"),
        func.sum(case((Lead.is_finalized.is_(True), 1), else_=0)).label("finalized_count"),
    )

    query = apply_global_exclusions(query, db)
    query = apply_all_filters(
        query,
        start,
        end,
        seller_ids,
        campaign_names,
        car_names,
        search,
        lead_finalizado,
    )

    results = (
        query.group_by(Lead.campaign_name)
        .order_by(func.count(Lead.id).desc())
        .all()
    )

    output = []

    for row in results:
        total = row.total_leads or 0
        replied = row.replied_first_message or 0
        sql_count = row.sql_count or 0
        won_count = row.won_count or 0
        lost_count = row.lost_count or 0
        finalized_count = row.finalized_count or 0

        output.append(
            {
                "campaign_name": row.campaign_name or "Sem campanha",
                "total_leads": total,
                "replied_first_message": replied,
                "sql_count": sql_count,
                "won_count": won_count,
                "lost_count": lost_count,
                "finalized_count": finalized_count,
                "reply_rate": round((replied / total) * 100, 2) if total else 0,
                "sql_rate": round((sql_count / total) * 100, 2) if total else 0,
                "won_rate": round((won_count / total) * 100, 2) if total else 0,
                "lost_rate": round((lost_count / total) * 100, 2) if total else 0,
            }
        )

    return output


@router.get("/cars")
def dashboard_cars(
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
    seller_ids: list[int] | None = Query(default=None),
    campaign_names: list[str] | None = Query(default=None),
    car_names: list[str] | None = Query(default=None),
    search: str | None = Query(default=None),
    lead_finalizado: bool | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(
        Lead.car_name.label("car_name"),
        func.count(Lead.id).label("total_leads"),
        func.sum(case((Lead.sql_at.isnot(None), 1), else_=0)).label("sql_count"),
        func.sum(case((Lead.won_at.isnot(None), 1), else_=0)).label("won_count"),
        func.sum(case((Lead.lost_at.isnot(None), 1), else_=0)).label("lost_count"),
    )

    query = apply_global_exclusions(query, db)
    query = apply_all_filters(
        query,
        start,
        end,
        seller_ids,
        campaign_names,
        car_names,
        search,
        lead_finalizado,
    )

    results = (
        query.group_by(Lead.car_name)
        .order_by(func.count(Lead.id).desc())
        .all()
    )

    output = []

    for row in results:
        total = row.total_leads or 0
        sql_count = row.sql_count or 0
        won_count = row.won_count or 0
        lost_count = row.lost_count or 0

        output.append(
            {
                "car_name": row.car_name or "Sem carro",
                "total_leads": total,
                "sql_count": sql_count,
                "won_count": won_count,
                "lost_count": lost_count,
                "sql_rate": round((sql_count / total) * 100, 2) if total else 0,
                "won_rate": round((won_count / total) * 100, 2) if total else 0,
                "lost_rate": round((lost_count / total) * 100, 2) if total else 0,
            }
        )

    return output


@router.get("/sources")
def dashboard_sources(
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
    seller_ids: list[int] | None = Query(default=None),
    campaign_names: list[str] | None = Query(default=None),
    car_names: list[str] | None = Query(default=None),
    search: str | None = Query(default=None),
    lead_finalizado: bool | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(
        Lead.lead_source.label("lead_source"),
        func.count(Lead.id).label("total_leads"),
    )

    query = apply_global_exclusions(query, db)
    query = apply_all_filters(
        query,
        start,
        end,
        seller_ids,
        campaign_names,
        car_names,
        search,
        lead_finalizado,
    )

    results = query.group_by(Lead.lead_source).order_by(func.count(Lead.id).desc()).all()

    return [
        {
            "lead_source": row.lead_source or "Sem origem",
            "total_leads": row.total_leads or 0,
        }
        for row in results
    ]


@router.get("/sellers")
def dashboard_sellers(
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
    seller_ids: list[int] | None = Query(default=None),
    campaign_names: list[str] | None = Query(default=None),
    car_names: list[str] | None = Query(default=None),
    search: str | None = Query(default=None),
    lead_finalizado: bool | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = (
        db.query(
            User.id.label("seller_id"),
            User.name.label("seller_name"),
            func.count(Lead.id).label("total_leads"),
            func.sum(case((Lead.replied_first_message.is_(True), 1), else_=0)).label("replied_first_message"),
            func.sum(case((Lead.sql_at.isnot(None), 1), else_=0)).label("sql_count"),
            func.sum(case((Lead.won_at.isnot(None), 1), else_=0)).label("won_count"),
            func.sum(case((Lead.lost_at.isnot(None), 1), else_=0)).label("lost_count"),
        )
        .select_from(Lead)
        .outerjoin(User, User.id == Lead.responsible_user_id)
    )

    query = apply_global_exclusions(query, db)
    query = apply_all_filters(
        query,
        start,
        end,
        seller_ids,
        campaign_names,
        car_names,
        search,
        lead_finalizado,
    )

    results = (
        query.group_by(User.id, User.name)
        .order_by(
            func.sum(case((Lead.won_at.isnot(None), 1), else_=0)).desc(),
            func.count(Lead.id).desc(),
        )
        .all()
    )

    output = []

    for row in results:
        total = row.total_leads or 0
        replied = row.replied_first_message or 0
        sql_count = row.sql_count or 0
        won_count = row.won_count or 0
        lost_count = row.lost_count or 0

        output.append(
            {
                "seller_id": row.seller_id,
                "seller_name": row.seller_name or "Sem responsável",
                "total_leads": total,
                "replied_first_message": replied,
                "sql_count": sql_count,
                "won_count": won_count,
                "lost_count": lost_count,
                "reply_rate": round((replied / total) * 100, 2) if total else 0,
                "sql_rate": round((sql_count / total) * 100, 2) if total else 0,
                "won_rate": round((won_count / total) * 100, 2) if total else 0,
                "lost_rate": round((lost_count / total) * 100, 2) if total else 0,
            }
        )

    return output


@router.get("/leads")
def dashboard_leads(
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
    seller_ids: list[int] | None = Query(default=None),
    campaign_names: list[str] | None = Query(default=None),
    car_names: list[str] | None = Query(default=None),
    search: str | None = Query(default=None),
    lead_finalizado: bool | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = (
        db.query(
            Lead.id.label("id"),
            Lead.name.label("lead_name"),
            User.name.label("seller_name"),
            Lead.kommo_pipeline_id.label("pipeline_id"),
            Lead.kommo_status_id.label("status_id"),
            Lead.campaign_name.label("campaign_name"),
            Lead.car_name.label("car_name"),
            Lead.lead_source.label("lead_source"),
            Lead.created_at_kommo.label("created_at_kommo"),
            Lead.is_finalized.label("is_finalized"),
        )
        .select_from(Lead)
        .outerjoin(User, User.id == Lead.responsible_user_id)
    )

    query = apply_global_exclusions(query, db)
    query = apply_all_filters(
        query,
        start,
        end,
        seller_ids,
        campaign_names,
        car_names,
        search,
        lead_finalizado,
    )

    results = query.order_by(Lead.created_at_kommo.desc().nullslast()).all()

    output = []

    for row in results:
        pipeline_name = get_pipeline_label(row.pipeline_id)
        status_name = get_status_label(row.status_id)
        funnel_type = detect_funnel_type(pipeline_name)
        stage_order = get_stage_order(funnel_type, status_name)

        output.append(
            {
                "id": row.id,
                "lead_name": row.lead_name,
                "seller_name": row.seller_name or "Sem responsável",
                "pipeline_id": row.pipeline_id,
                "pipeline_name": pipeline_name,
                "status_id": row.status_id,
                "status_name": status_name,
                "funnel_type": funnel_type,
                "stage_order": stage_order,
                "campaign_name": row.campaign_name or "Sem campanha",
                "car_name": row.car_name or "Sem carro",
                "lead_source": row.lead_source or "Sem origem",
                "created_at_kommo": row.created_at_kommo,
                "is_finalized": row.is_finalized,
            }
        )

    return output


@router.get("/metadata")
async def dashboard_metadata():
    client = KommoClient()

    pipelines_data = await client.get_pipelines()
    if "status_code" in pipelines_data:
        raise HTTPException(status_code=502, detail=pipelines_data)

    pipelines: dict[str, str] = {}
    statuses: dict[str, str] = {}

    for pipeline in pipelines_data.get("_embedded", {}).get("pipelines", []):
        pipeline_id = pipeline.get("id")
        pipeline_name = pipeline.get("name") or f"Pipeline {pipeline_id}"

        if not pipeline_id:
            continue

        pipelines[str(pipeline_id)] = pipeline_name

        statuses_data = await client.get_pipeline_statuses(pipeline_id)
        if "status_code" in statuses_data:
            continue

        for status in statuses_data.get("_embedded", {}).get("statuses", []):
            status_id = status.get("id")
            status_name = status.get("name") or f"Status {status_id}"

            if not status_id:
                continue

            statuses[f"{pipeline_id}:{status_id}"] = status_name

    return {
        "pipelines": pipelines,
        "statuses": statuses,
    }


@router.get("/lead/{lead_id}")
def dashboard_lead_detail(
    lead_id: int,
    db: Session = Depends(get_db),
):
    query = (
        db.query(
            Lead.id.label("id"),
            Lead.name.label("lead_name"),
            User.name.label("seller_name"),
            Lead.kommo_pipeline_id.label("pipeline_id"),
            Lead.kommo_status_id.label("status_id"),
            Lead.campaign_name.label("campaign_name"),
            Lead.car_name.label("car_name"),
            Lead.lead_source.label("lead_source"),
            Lead.created_at_kommo.label("created_at_kommo"),
            Lead.updated_at_kommo.label("updated_at_kommo"),
            Lead.sql_at.label("sql_at"),
            Lead.won_at.label("won_at"),
            Lead.lost_at.label("lost_at"),
            Lead.is_finalized.label("is_finalized"),
        )
        .select_from(Lead)
        .outerjoin(User, User.id == Lead.responsible_user_id)
        .filter(Lead.id == lead_id)
    )

    query = apply_global_exclusions(query, db)

    row = query.first()
    if not row:
        raise HTTPException(status_code=404, detail="Lead não encontrado")

    pipeline_name = get_pipeline_label(row.pipeline_id)
    status_name = get_status_label(row.status_id)
    funnel_type = detect_funnel_type(pipeline_name)
    stage_order = get_stage_order(funnel_type, status_name)

    timeline = []

    if row.created_at_kommo:
        timeline.append(
            {
                "label": "Lead criado",
                "date": row.created_at_kommo,
                "type": "created",
            }
        )

    if row.sql_at:
        timeline.append(
            {
                "label": "Lead chegou em SQL",
                "date": row.sql_at,
                "type": "sql",
            }
        )

    if row.won_at:
        timeline.append(
            {
                "label": "Venda ganha",
                "date": row.won_at,
                "type": "won",
            }
        )

    if row.lost_at:
        timeline.append(
            {
                "label": "Lead perdido",
                "date": row.lost_at,
                "type": "lost",
            }
        )

    if row.updated_at_kommo:
        timeline.append(
            {
                "label": "Última atualização",
                "date": row.updated_at_kommo,
                "type": "updated",
            }
        )

    timeline.sort(key=lambda item: item["date"] or datetime.min)

    return {
        "id": row.id,
        "lead_name": row.lead_name,
        "seller_name": row.seller_name or "Sem responsável",
        "pipeline_id": row.pipeline_id,
        "pipeline_name": pipeline_name,
        "status_id": row.status_id,
        "status_name": status_name,
        "funnel_type": funnel_type,
        "stage_order": stage_order,
        "campaign_name": row.campaign_name or "Sem campanha",
        "car_name": row.car_name or "Sem carro",
        "lead_source": row.lead_source or "Sem origem",
        "created_at_kommo": row.created_at_kommo,
        "updated_at_kommo": row.updated_at_kommo,
        "sql_at": row.sql_at,
        "won_at": row.won_at,
        "lost_at": row.lost_at,
        "is_finalized": row.is_finalized,
        "timeline": timeline,
    }