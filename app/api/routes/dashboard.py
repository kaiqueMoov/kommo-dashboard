from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.lead import Lead
from app.models.user import User

router = APIRouter()


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
):
    query = apply_date_filters(query, start, end)
    query = apply_seller_filters(query, seller_ids)
    query = apply_campaign_filters(query, campaign_names)
    query = apply_car_filters(query, car_names)
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
    db: Session = Depends(get_db),
):
    query = db.query(Lead)
    query = apply_all_filters(query, start, end, seller_ids, campaign_names, car_names, search)

    total_leads = query.count()
    replied_count = query.filter(Lead.replied_first_message.is_(True)).count()
    sql_count = query.filter(Lead.sql_at.isnot(None)).count()
    won_count = query.filter(Lead.won_at.isnot(None)).count()
    lost_count = query.filter(Lead.lost_at.isnot(None)).count()

    return {
        "total_leads": total_leads,
        "replied_first_message": replied_count,
        "sql_count": sql_count,
        "won_count": won_count,
        "lost_count": lost_count,
    }

@router.get("/campaigns")
def dashboard_campaigns(
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
    seller_ids: list[int] | None = Query(default=None),
    campaign_names: list[str] | None = Query(default=None),
    car_names: list[str] | None = Query(default=None),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(
        Lead.campaign_name.label("campaign_name"),
        func.count(Lead.id).label("total_leads"),
        func.sum(case((Lead.replied_first_message.is_(True), 1), else_=0)).label("replied_first_message"),
        func.sum(case((Lead.sql_at.isnot(None), 1), else_=0)).label("sql_count"),
        func.sum(case((Lead.won_at.isnot(None), 1), else_=0)).label("won_count"),
        func.sum(case((Lead.lost_at.isnot(None), 1), else_=0)).label("lost_count"),
    )

    query = apply_all_filters(query, start, end, seller_ids, campaign_names, car_names, search)

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

        output.append(
            {
                "campaign_name": row.campaign_name or "Sem campanha",
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


@router.get("/cars")
def dashboard_cars(
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
    seller_ids: list[int] | None = Query(default=None),
    campaign_names: list[str] | None = Query(default=None),
    car_names: list[str] | None = Query(default=None),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(
        Lead.car_name.label("car_name"),
        func.count(Lead.id).label("total_leads"),
    )

    query = apply_all_filters(query, start, end, seller_ids, campaign_names, car_names, search)

    results = query.group_by(Lead.car_name).order_by(func.count(Lead.id).desc()).all()

    return [
        {
            "car_name": row.car_name or "Sem carro",
            "total_leads": row.total_leads or 0,
        }
        for row in results
    ]


@router.get("/sources")
def dashboard_sources(
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
    seller_ids: list[int] | None = Query(default=None),
    campaign_names: list[str] | None = Query(default=None),
    car_names: list[str] | None = Query(default=None),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(
        Lead.lead_source.label("lead_source"),
        func.count(Lead.id).label("total_leads"),
    )

    query = apply_all_filters(query, start, end, seller_ids, campaign_names, car_names, search)

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
    db: Session = Depends(get_db),
):
    query = (
        db.query(
            User.id.label("seller_id"),
            User.name.label("seller_name"),
            func.count(Lead.id).label("total_leads"),
            func.sum(case((Lead.sql_at.isnot(None), 1), else_=0)).label("sql_count"),
            func.sum(case((Lead.won_at.isnot(None), 1), else_=0)).label("won_count"),
            func.sum(case((Lead.lost_at.isnot(None), 1), else_=0)).label("lost_count"),
        )
        .outerjoin(User, User.id == Lead.responsible_user_id)
    )

    query = apply_all_filters(query, start, end, seller_ids, campaign_names, car_names, search)

    results = query.group_by(User.id, User.name).order_by(func.count(Lead.id).desc()).all()

    return [
        {
            "seller_id": row.seller_id,
            "seller_name": row.seller_name or "Sem responsável",
            "total_leads": row.total_leads or 0,
            "sql_count": row.sql_count or 0,
            "won_count": row.won_count or 0,
            "lost_count": row.lost_count or 0,
        }
        for row in results
    ]


@router.get("/leads")
def dashboard_leads(
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
    seller_ids: list[int] | None = Query(default=None),
    campaign_names: list[str] | None = Query(default=None),
    car_names: list[str] | None = Query(default=None),
    search: str | None = Query(default=None),
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
        )
        .outerjoin(User, User.id == Lead.responsible_user_id)
    )

    query = apply_all_filters(query, start, end, seller_ids, campaign_names, car_names, search)

    results = query.order_by(Lead.created_at_kommo.desc().nullslast()).all()

    return [
        {
            "id": row.id,
            "lead_name": row.lead_name,
            "seller_name": row.seller_name or "Sem responsável",
            "pipeline_id": row.pipeline_id,
            "status_id": row.status_id,
            "campaign_name": row.campaign_name or "Sem campanha",
            "car_name": row.car_name or "Sem carro",
            "lead_source": row.lead_source or "Sem origem",
            "created_at_kommo": row.created_at_kommo,
        }
        for row in results
    ]