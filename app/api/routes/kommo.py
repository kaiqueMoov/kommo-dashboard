import re
import unicodedata
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

BLOCKED_USER_NAMES = {
    "pedro lunardini",
    "moov",
    "joao",
    "daniela santos",
    "gabriela macena",
}

CAR_PATTERNS = [
    (["song plus", "songplus"], "Song Plus"),
    (["song pro", "songpro"], "Song Pro"),
    (["dolphin mini"], "Dolphin Mini"),
    (["dolphin"], "Dolphin"),
    (["t-cross", "tcross"], "T-Cross"),
    (["tera"], "Tera"),
    (["kicks"], "Kicks"),
    (["boreal"], "Boreal"),
    (["haval h6", "h6 hev2", "h6"], "Haval H6"),
    (["hilux"], "Hilux"),
    (["volvo ex30", "ex30"], "Volvo EX30"),
    (["bmw x1", "x1 m sport", "x1"], "BMW X1"),
    (["compass"], "Compass"),
    (["renegade"], "Renegade"),
    (["argo"], "Argo"),
    (["fiorino"], "Fiorino"),
    (["xc60"], "Volvo XC60"),
    (["scudo"], "Scudo"),
    (["fastback"], "Fastback"),
    (["nivus"], "Nivus"),
    (["creta"], "Creta"),
    (["pulse"], "Pulse"),
    (["tracker"], "Tracker"),
    (["corolla cross"], "Corolla Cross"),
]

GENERIC_CAMPAIGN_TAGS = {
    "lead finalizado",
    "sql",
    "novo lead",
    "novo lead trafego pago",
    "mensagem enviada",
    "respondeu a primeira mensagem",
    "orcamento enviado",
    "orçamento enviado",
    "em negociacao",
    "em negociação",
    "aguardando documentos",
    "subir ficha",
    "em analise",
    "em análise",
    "venda ganha",
}


def normalize_text(value: str | None) -> str:
    if not value:
        return ""

    value = unicodedata.normalize("NFD", str(value))
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    return value.strip().lower()


def normalize_person_name(value: str | None) -> str:
    return normalize_text(value)


def clean_extracted_value(value) -> str | None:
    if value is None:
        return None

    if isinstance(value, dict):
        value = value.get("value")

    value = str(value).strip()
    if not value:
        return None

    normalized = normalize_text(value)
    if normalized in {"none", "null", "sem campanha", "sem carro", "sem origem", "-", "--", "n/a"}:
        return None

    return value


def first_non_empty(*values) -> str | None:
    for value in values:
        cleaned = clean_extracted_value(value)
        if cleaned:
            return cleaned
    return None


def has_finalized_tag(tag_names: list[str]) -> bool:
    normalized_tags = [normalize_text(tag) for tag in tag_names]
    return "lead finalizado" in normalized_tags


def get_custom_field_value(custom_fields: list[dict] | None, *field_names: str) -> str | None:
    if not custom_fields:
        return None

    normalized_names = {normalize_text(name) for name in field_names}

    for field in custom_fields:
        current_name = normalize_text(field.get("field_name") or field.get("name"))
        if current_name in normalized_names:
            values = field.get("values", [])
            if values:
                first = values[0]
                if isinstance(first, dict):
                    return clean_extracted_value(first.get("value"))
                return clean_extracted_value(first)

    return None


def get_tag_names(item: dict) -> list[str]:
    tags = item.get("_embedded", {}).get("tags", []) or []
    return [str(tag.get("name", "")).strip() for tag in tags if tag.get("name")]


def extract_known_car(text: str | None) -> str | None:
    normalized = normalize_text(text)
    if not normalized:
        return None

    for aliases, label in CAR_PATTERNS:
        for alias in aliases:
            if normalize_text(alias) in normalized:
                return label

    return None


def extract_car_from_tags(tag_names: list[str]) -> str | None:
    for tag in tag_names:
        found = extract_known_car(tag)
        if found:
            return found
    return None


def extract_car_from_name(name: str | None) -> str | None:
    return extract_known_car(name)


def extract_campaign_from_tags(tag_names: list[str]) -> str | None:
    for tag in tag_names:
        cleaned = clean_extracted_value(tag)
        if not cleaned:
            continue

        normalized = normalize_text(cleaned)

        if normalized in GENERIC_CAMPAIGN_TAGS:
            continue

        if extract_known_car(cleaned):
            continue

        if any(word in normalized for word in ["facebook", "instagram", "google", "meta", "tiktok", "campanha", "ads", "anuncio", "anúncio"]):
            return cleaned

    return None


def extract_campaign_from_name(name: str | None) -> str | None:
    cleaned = clean_extracted_value(name)
    if not cleaned:
        return None

    normalized = normalize_text(cleaned)

    if normalized.startswith(("facebook", "instagram", "google", "meta", "tiktok")):
        return cleaned

    if any(word in normalized for word in ["campanha", "ads", "trafego", "tráfego", "anuncio", "anúncio"]):
        return cleaned

    return None


def extract_lead_source_from_name(name: str | None) -> str | None:
    normalized = normalize_text(name)

    if normalized.startswith("facebook") or "facebook" in normalized or "meta" in normalized:
        return "Facebook"
    if normalized.startswith("instagram") or "instagram" in normalized:
        return "Instagram"
    if normalized.startswith("google") or "google" in normalized:
        return "Google"
    if "tiktok" in normalized:
        return "TikTok"

    return None


def ts_to_dt(value):
    
    if not value:
        return None
    return datetime.fromtimestamp(int(value))
def ensure_valid_responsible_user_id(db: Session, lead: Lead) -> None:
    if not lead.responsible_user_id:
        return

    existing_user = db.get(User, lead.responsible_user_id)
    if not existing_user:
        lead.responsible_user_id = None


def apply_lead_data(lead: Lead, item: dict) -> None:
    custom_fields = item.get("custom_fields_values") or item.get("custom_fields") or []
    tag_names = get_tag_names(item)

    lead.is_finalized = has_finalized_tag(tag_names)

    lead.name = item.get("name")
    lead.kommo_pipeline_id = item.get("pipeline_id")
    lead.kommo_status_id = item.get("status_id")
    lead.responsible_user_id = item.get("responsible_user_id")

    utm_source = get_custom_field_value(custom_fields, "UTM_SOURCE", "utm_source")
    utm_medium = get_custom_field_value(custom_fields, "UTM_MEDIUM", "utm_medium")
    utm_campaign = get_custom_field_value(custom_fields, "UTM_CAMPAIGN", "utm_campaign")
    utm_content = get_custom_field_value(custom_fields, "UTM_CONTENT", "utm_content")
    utm_term = get_custom_field_value(custom_fields, "UTM_TERM", "utm_term")

    lead.car_name = first_non_empty(
        get_custom_field_value(
            custom_fields,
            "carro_interesse",
            "carro de interesse",
            "veiculo de interesse",
            "veículo de interesse",
            "carro",
            "veiculo",
            "veículo",
            "modelo",
            "modelo do carro",
            "modelo desejado",
            "veiculo desejado",
            "veículo desejado",
            "carro desejado",
            "produto",
            "interesse",
        ),
        extract_car_from_tags(tag_names),
        extract_car_from_name(item.get("name")),
        lead.car_name,
    )

    lead.campaign_name = first_non_empty(
        get_custom_field_value(
            custom_fields,
            "nome_campanha",
            "nome da campanha",
            "campanha",
            "campaign",
            "campanha meta",
            "campanha google",
            "anuncio",
            "anúncio",
            "ad name",
            "ads",
        ),
        utm_campaign,
        extract_campaign_from_tags(tag_names),
        extract_campaign_from_name(item.get("name")),
        lead.campaign_name,
    )

    lead.lead_source = first_non_empty(
        get_custom_field_value(
            custom_fields,
            "origem_captacao",
            "origem",
            "origem da captação",
            "origem do lead",
            "source",
            "canal",
        ),
        utm_source,
        extract_lead_source_from_name(item.get("name")),
        lead.lead_source,
    )

    lead.utm_source = utm_source
    lead.utm_medium = utm_medium
    lead.utm_campaign = utm_campaign
    lead.utm_content = utm_content
    lead.utm_term = utm_term

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
    ensure_valid_responsible_user_id(db, lead)

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
    total_blocked = 0

    for item in users_data:
        current_name = normalize_person_name(item.get("name"))
        if current_name in BLOCKED_USER_NAMES:
            total_blocked += 1
            continue

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
        "users_blocked": total_blocked,
    }


@router.post("/sync/leads")
async def sync_leads(db: Session = Depends(get_db)):
    client = KommoClient()

    total_saved = 0
    total_found = 0
    page = 1
    limit = 250
    details_fetched = 0

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
            ensure_valid_responsible_user_id(db, lead)

            needs_detail = not lead.car_name or not lead.campaign_name or not lead.lead_source

            if needs_detail:
                detail = await client.get_lead_by_id(item["id"])
                if "status_code" not in detail:
                    apply_lead_data(lead, detail)
                    ensure_valid_responsible_user_id(db, lead)
                    details_fetched += 1

            total_saved += 1

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        if len(leads_data) < limit:
            break

        page += 1

    return {
        "status": "ok",
        "leads_found": total_found,
        "leads_saved": total_saved,
        "details_fetched": details_fetched,
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