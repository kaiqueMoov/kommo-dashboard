import re
from datetime import datetime
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.lead_rules import LOST_STATUS_IDS, SQL_STATUS_IDS, WON_STATUS_IDS
from app.integrations.kommo_client import KommoClient
from app.models.lead import Lead
from app.models.user import User

router = APIRouter()


def get_custom_field_value(custom_fields: list[dict] | None, *field_names: str) -> str | None:
    if not custom_fields:
        return None

    normalized_names = [name.strip().lower() for name in field_names]

    for field in custom_fields:
        current_name = (field.get("field_name") or field.get("name") or "").strip().lower()
        if current_name in normalized_names:
            values = field.get("values", [])
            if values:
                first = values[0]
                if isinstance(first, dict):
                    return first.get("value")
                return str(first)
    return None


def get_tag_names(item: dict) -> list[str]:
    tags = item.get("_embedded", {}).get("tags", []) or []
    return [str(tag.get("name", "")).strip() for tag in tags if tag.get("name")]


def extract_car_from_tags(tag_names: list[str]) -> str | None:
    known_cars = [
        "song plus",
        "t-cross",
        "tera",
        "kicks",
        "boreal",
        "haval",
        "hilux",
        "volvo",
        "bmw x1",
        "compass",
        "renegade",
        "argo",
        "fiorino",
        "xc60",
        "ex30",
    ]

    joined = " | ".join(tag_names).lower()

    for car in known_cars:
        if car in joined:
            return car.title()

    return None


def extract_campaign_from_name(name: str | None) -> str | None:
    if not name:
        return None

    lowered = name.lower()

    if lowered.startswith("facebook"):
        return name.strip()
    if lowered.startswith("instagram"):
        return name.strip()
    if lowered.startswith("google"):
        return name.strip()

    return None


def ts_to_dt(value):
    if not value:
        return None
    return datetime.fromtimestamp(int(value))


def apply_lead_data(lead: Lead, item: dict) -> None:
    custom_fields = item.get("custom_fields_values") or item.get("custom_fields") or []
    tag_names = get_tag_names(item)

    lead.name = item.get("name")
    lead.kommo_pipeline_id = item.get("pipeline_id")
    lead.kommo_status_id = item.get("status_id")
    lead.responsible_user_id = item.get("responsible_user_id")

    lead.car_name = (
        get_custom_field_value(
            custom_fields,
            "carro_interesse",
            "carro",
            "veiculo",
            "veículo",
            "modelo",
            "modelo do carro",
        )
        or extract_car_from_tags(tag_names)
    )

    lead.campaign_name = (
        get_custom_field_value(
            custom_fields,
            "nome_campanha",
            "campanha",
            "nome da campanha",
            "campaign",
        )
        or extract_campaign_from_name(item.get("name"))
    )

    lead.lead_source = get_custom_field_value(
        custom_fields,
        "origem_captacao",
        "origem",
        "origem da captação",
        "origem do lead",
        "source",
    )

    if not lead.lead_source and lead.name:
        lead_name_lower = lead.name.lower()
        if lead_name_lower.startswith("facebook"):
            lead.lead_source = "Facebook"
        elif lead_name_lower.startswith("instagram"):
            lead.lead_source = "Instagram"
        elif lead_name_lower.startswith("google"):
            lead.lead_source = "Google"

    lead.utm_source = get_custom_field_value(custom_fields, "UTM_SOURCE", "utm_source")
    lead.utm_medium = get_custom_field_value(custom_fields, "UTM_MEDIUM", "utm_medium")
    lead.utm_campaign = get_custom_field_value(custom_fields, "UTM_CAMPAIGN", "utm_campaign")
    lead.utm_content = get_custom_field_value(custom_fields, "UTM_CONTENT", "utm_content")
    lead.utm_term = get_custom_field_value(custom_fields, "UTM_TERM", "utm_term")

    lead.created_at_kommo = ts_to_dt(item.get("created_at") or item.get("date_create"))
    lead.updated_at_kommo = ts_to_dt(item.get("updated_at") or item.get("last_modified"))

    if lead.kommo_status_id in SQL_STATUS_IDS and not lead.sql_at:
        lead.sql_at = ts_to_dt(item.get("updated_at") or item.get("last_modified"))

    if lead.kommo_status_id in WON_STATUS_IDS and not lead.won_at:
        lead.won_at = ts_to_dt(item.get("closed_at") or item.get("updated_at") or item.get("last_modified"))

    if lead.kommo_status_id in LOST_STATUS_IDS and not lead.lost_at:
        lead.lost_at = ts_to_dt(item.get("closed_at") or item.get("updated_at") or item.get("last_modified"))


async def sync_single_lead(db: Session, client: KommoClient, lead_id: int) -> dict:
    data = await client.get_lead_by_id(lead_id)

    if "status_code" in data:
        return data

    lead = db.get(Lead, data["id"])
    if not lead:
        lead = Lead(id=data["id"])
        db.add(lead)

    apply_lead_data(lead, data)
    return {"id": lead_id, "status": "synced"}


def extract_lead_ids_from_form(encoded_form: str) -> list[int]:
    parsed = parse_qs(encoded_form, keep_blank_values=True)
    lead_ids: set[int] = set()

    pattern = re.compile(r"^leads\[(add|update|status|responsible|restore|delete)\]\[\d+\]\[id\]$")

    for key, values in parsed.items():
        if pattern.match(key):
            for value in values:
                if value and str(value).isdigit():
                    lead_ids.add(int(value))

    return sorted(lead_ids)


@router.get("/debug/leads")
async def debug_leads():
    client = KommoClient()
    return await client.get_leads(page=1, limit=20)


@router.get("/test")
async def test_kommo():
    client = KommoClient()
    return await client.get_account()


@router.post("/sync/users")
async def sync_users(db: Session = Depends(get_db)):
    client = KommoClient()
    data = await client.get_users(page=1, limit=250)

    if "status_code" in data:
        raise HTTPException(status_code=502, detail=data)

    users_data = data.get("_embedded", {}).get("users", [])
    total_saved = 0

    for item in users_data:
        user = db.get(User, item["id"])

        if not user:
            user = User(
                id=item["id"],
                name=item.get("name") or "Sem nome",
                email=item.get("email"),
                role=str(item.get("rights", {}).get("is_admin", False)),
                active=not item.get("is_free", False),
            )
            db.add(user)
        else:
            user.name = item.get("name") or user.name
            user.email = item.get("email")
            user.role = str(item.get("rights", {}).get("is_admin", False))
            user.active = not item.get("is_free", False)

        total_saved += 1

    db.commit()

    return {
        "status": "ok",
        "users_found": len(users_data),
        "users_saved": total_saved,
    }


@router.post("/sync/leads")
async def sync_leads(db: Session = Depends(get_db)):
    client = KommoClient()

    total_saved = 0
    total_found = 0
    page = 1
    limit = 250

    while True:
        data = await client.get_leads(page=page, limit=limit)

        if "status_code" in data:
            raise HTTPException(status_code=502, detail=data)

        leads_data = data.get("_embedded", {}).get("leads", []) or []

        if not leads_data:
            break

        total_found += len(leads_data)

        for item in leads_data:
            lead = db.get(Lead, item["id"])

            if not lead:
                lead = Lead(id=item["id"])
                db.add(lead)

            apply_lead_data(lead, item)
            total_saved += 1

        db.commit()

        if len(leads_data) < limit:
            break

        page += 1

    return {
        "status": "ok",
        "leads_found": total_found,
        "leads_saved": total_saved,
        "pages_processed": page,
    }


@router.post("/webhooks")
async def kommo_webhooks(request: Request, db: Session = Depends(get_db)):
    raw_body = (await request.body()).decode("utf-8", errors="ignore")
    lead_ids = extract_lead_ids_from_form(raw_body)

    if not lead_ids:
        return {
            "status": "ignored",
            "message": "Nenhum lead_id encontrado no webhook",
            "raw_body": raw_body,
        }

    client = KommoClient()
    synced = []
    errors = []

    for lead_id in lead_ids:
        result = await sync_single_lead(db, client, lead_id)
        if "status_code" in result:
            errors.append({"lead_id": lead_id, "error": result})
        else:
            synced.append(lead_id)

    db.commit()

    return {
        "status": "ok",
        "lead_ids_received": lead_ids,
        "synced_count": len(synced),
        "synced": synced,
        "errors": errors,
    }