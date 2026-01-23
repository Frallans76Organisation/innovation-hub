"""
API endpoints for Funding Calls and Funding Matches
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from innovation_hub.database import get_db
from innovation_hub.models import (
    FundingCallCreate, FundingCallUpdate, FundingCallResponse, FundingCallDetailResponse,
    FundingMatchCreate, FundingMatchUpdate, FundingMatchResponse,
    FundingFilter, FundingStats, PaginationParams,
    FundingCallStatusEnum, FundingSourceEnum, AlignmentEntityTypeEnum
)
from .funding_crud import FundingCRUD, FundingMatchCRUD


router = APIRouter(prefix="/api/funding", tags=["Funding"])


# =============================================================================
# FundingCall endpoints
# =============================================================================

@router.get("/", response_model=List[FundingCallResponse])
def get_funding_calls(
    source: Optional[FundingSourceEnum] = None,
    status: Optional[FundingCallStatusEnum] = None,
    search: Optional[str] = None,
    has_deadline_within_days: Optional[int] = Query(None, ge=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Hämta alla finansieringsutlysningar med filter och paginering.

    Filter:
    - source: Källa (vinnova, eu_horizon, etc.)
    - status: Status (öppen, kommande, stängd)
    - search: Sök i titel och beskrivning
    - has_deadline_within_days: Deadline inom X dagar
    """
    filters = FundingFilter(
        source=source,
        status=status,
        search=search,
        has_deadline_within_days=has_deadline_within_days
    )
    pagination = PaginationParams(skip=skip, limit=limit)

    calls = FundingCRUD.get_all(db, filters, pagination)

    # Bygg response med match_count
    result = []
    for call in calls:
        matches = FundingMatchCRUD.get_for_call(db, call.id)
        result.append({
            "id": call.id,
            "title": call.title,
            "description": call.description,
            "source": call.source.value if call.source else None,
            "status": call.status.value if call.status else None,
            "external_id": call.external_id,
            "external_url": call.external_url,
            "open_date": call.open_date,
            "deadline": call.deadline,
            "decision_date": call.decision_date,
            "total_budget": call.total_budget,
            "min_grant": call.min_grant,
            "max_grant": call.max_grant,
            "co_funding_requirement": call.co_funding_requirement,
            "eligible_applicants": call.eligible_applicants or [],
            "focus_areas": call.focus_areas or [],
            "keywords": call.keywords or [],
            "requirements_summary": call.requirements_summary,
            "rag_indexed": call.rag_indexed or False,
            "match_count": len(matches),
            "created_at": call.created_at,
            "updated_at": call.updated_at
        })

    return result


@router.get("/stats", response_model=FundingStats)
def get_funding_stats(db: Session = Depends(get_db)):
    """Hämta statistik för finansieringsutlysningar"""
    return FundingCRUD.get_stats(db)


@router.get("/upcoming")
def get_upcoming_deadlines(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Hämta utlysningar med deadline inom X dagar"""
    calls = FundingCRUD.get_upcoming_deadlines(db, days)

    return [
        {
            "id": call.id,
            "title": call.title,
            "source": call.source.value if call.source else None,
            "deadline": call.deadline,
            "total_budget": call.total_budget,
            "status": call.status.value if call.status else None
        }
        for call in calls
    ]


@router.get("/{call_id}", response_model=FundingCallDetailResponse)
def get_funding_call(call_id: int, db: Session = Depends(get_db)):
    """Hämta en specifik finansieringsutlysning med matchningar"""
    call = FundingCRUD.get_by_id(db, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Funding call not found")

    # Hämta matchningar
    matches = FundingMatchCRUD.get_for_call(db, call_id)
    matches_response = []
    for match in matches:
        # Hämta entitetstitel
        from innovation_hub.database import Idea, Project
        if match.entity_type.value == "idea":
            entity = db.query(Idea).filter(Idea.id == match.entity_id).first()
            entity_title = entity.title if entity else None
        else:
            entity = db.query(Project).filter(Project.id == match.entity_id).first()
            entity_title = entity.name if entity else None

        matches_response.append({
            "id": match.id,
            "funding_call_id": match.funding_call_id,
            "entity_type": match.entity_type.value,
            "entity_id": match.entity_id,
            "match_score": match.match_score,
            "match_reasoning": match.match_reasoning,
            "strengths": match.strengths or [],
            "gaps": match.gaps or [],
            "is_recommended": match.is_recommended or False,
            "user_rating": match.user_rating,
            "funding_title": call.title,
            "entity_title": entity_title,
            "created_at": match.created_at,
            "updated_at": match.updated_at
        })

    return {
        "id": call.id,
        "title": call.title,
        "description": call.description,
        "source": call.source.value if call.source else None,
        "status": call.status.value if call.status else None,
        "external_id": call.external_id,
        "external_url": call.external_url,
        "open_date": call.open_date,
        "deadline": call.deadline,
        "decision_date": call.decision_date,
        "total_budget": call.total_budget,
        "min_grant": call.min_grant,
        "max_grant": call.max_grant,
        "co_funding_requirement": call.co_funding_requirement,
        "eligible_applicants": call.eligible_applicants or [],
        "focus_areas": call.focus_areas or [],
        "keywords": call.keywords or [],
        "requirements_summary": call.requirements_summary,
        "rag_indexed": call.rag_indexed or False,
        "match_count": len(matches),
        "created_at": call.created_at,
        "updated_at": call.updated_at,
        "matches": matches_response
    }


@router.post("/", response_model=FundingCallResponse)
def create_funding_call(
    call_data: FundingCallCreate,
    db: Session = Depends(get_db)
):
    """Skapa en ny finansieringsutlysning"""
    call = FundingCRUD.create(db, call_data)

    return {
        "id": call.id,
        "title": call.title,
        "description": call.description,
        "source": call.source.value if call.source else None,
        "status": call.status.value if call.status else None,
        "external_id": call.external_id,
        "external_url": call.external_url,
        "open_date": call.open_date,
        "deadline": call.deadline,
        "decision_date": call.decision_date,
        "total_budget": call.total_budget,
        "min_grant": call.min_grant,
        "max_grant": call.max_grant,
        "co_funding_requirement": call.co_funding_requirement,
        "eligible_applicants": call.eligible_applicants or [],
        "focus_areas": call.focus_areas or [],
        "keywords": call.keywords or [],
        "requirements_summary": call.requirements_summary,
        "rag_indexed": call.rag_indexed or False,
        "match_count": 0,
        "created_at": call.created_at,
        "updated_at": call.updated_at
    }


@router.put("/{call_id}", response_model=FundingCallResponse)
def update_funding_call(
    call_id: int,
    call_data: FundingCallUpdate,
    db: Session = Depends(get_db)
):
    """Uppdatera en finansieringsutlysning"""
    call = FundingCRUD.update(db, call_id, call_data)
    if not call:
        raise HTTPException(status_code=404, detail="Funding call not found")

    matches = FundingMatchCRUD.get_for_call(db, call_id)

    return {
        "id": call.id,
        "title": call.title,
        "description": call.description,
        "source": call.source.value if call.source else None,
        "status": call.status.value if call.status else None,
        "external_id": call.external_id,
        "external_url": call.external_url,
        "open_date": call.open_date,
        "deadline": call.deadline,
        "decision_date": call.decision_date,
        "total_budget": call.total_budget,
        "min_grant": call.min_grant,
        "max_grant": call.max_grant,
        "co_funding_requirement": call.co_funding_requirement,
        "eligible_applicants": call.eligible_applicants or [],
        "focus_areas": call.focus_areas or [],
        "keywords": call.keywords or [],
        "requirements_summary": call.requirements_summary,
        "rag_indexed": call.rag_indexed or False,
        "match_count": len(matches),
        "created_at": call.created_at,
        "updated_at": call.updated_at
    }


@router.delete("/{call_id}")
def delete_funding_call(call_id: int, db: Session = Depends(get_db)):
    """Ta bort en finansieringsutlysning"""
    if not FundingCRUD.delete(db, call_id):
        raise HTTPException(status_code=404, detail="Funding call not found")

    return {"message": "Funding call deleted successfully"}


# =============================================================================
# FundingMatch endpoints
# =============================================================================

@router.get("/matches/entity/{entity_type}/{entity_id}", response_model=List[FundingMatchResponse])
def get_entity_matches(
    entity_type: AlignmentEntityTypeEnum,
    entity_id: int,
    db: Session = Depends(get_db)
):
    """Hämta alla matchningar för en specifik idé eller projekt"""
    matches = FundingMatchCRUD.get_for_entity(db, entity_type.value, entity_id)

    result = []
    for match in matches:
        # Hämta utlysningstitel
        call = FundingCRUD.get_by_id(db, match.funding_call_id)
        funding_title = call.title if call else None

        # Hämta entitetstitel
        from innovation_hub.database import Idea, Project
        if match.entity_type.value == "idea":
            entity = db.query(Idea).filter(Idea.id == match.entity_id).first()
            entity_title = entity.title if entity else None
        else:
            entity = db.query(Project).filter(Project.id == match.entity_id).first()
            entity_title = entity.name if entity else None

        result.append({
            "id": match.id,
            "funding_call_id": match.funding_call_id,
            "entity_type": match.entity_type.value,
            "entity_id": match.entity_id,
            "match_score": match.match_score,
            "match_reasoning": match.match_reasoning,
            "strengths": match.strengths or [],
            "gaps": match.gaps or [],
            "is_recommended": match.is_recommended or False,
            "user_rating": match.user_rating,
            "funding_title": funding_title,
            "entity_title": entity_title,
            "created_at": match.created_at,
            "updated_at": match.updated_at
        })

    return result


@router.get("/{call_id}/matches", response_model=List[FundingMatchResponse])
def get_call_matches(call_id: int, db: Session = Depends(get_db)):
    """Hämta alla matchningar för en specifik utlysning"""
    call = FundingCRUD.get_by_id(db, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Funding call not found")

    matches = FundingMatchCRUD.get_for_call(db, call_id)

    result = []
    for match in matches:
        # Hämta entitetstitel
        from innovation_hub.database import Idea, Project
        if match.entity_type.value == "idea":
            entity = db.query(Idea).filter(Idea.id == match.entity_id).first()
            entity_title = entity.title if entity else None
        else:
            entity = db.query(Project).filter(Project.id == match.entity_id).first()
            entity_title = entity.name if entity else None

        result.append({
            "id": match.id,
            "funding_call_id": match.funding_call_id,
            "entity_type": match.entity_type.value,
            "entity_id": match.entity_id,
            "match_score": match.match_score,
            "match_reasoning": match.match_reasoning,
            "strengths": match.strengths or [],
            "gaps": match.gaps or [],
            "is_recommended": match.is_recommended or False,
            "user_rating": match.user_rating,
            "funding_title": call.title,
            "entity_title": entity_title,
            "created_at": match.created_at,
            "updated_at": match.updated_at
        })

    return result


@router.post("/matches/", response_model=FundingMatchResponse)
def create_funding_match(
    match_data: FundingMatchCreate,
    db: Session = Depends(get_db)
):
    """Skapa en ny matchning mellan idé/projekt och utlysning"""
    try:
        match = FundingMatchCRUD.create(db, match_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Hämta titlar
    call = FundingCRUD.get_by_id(db, match.funding_call_id)
    funding_title = call.title if call else None

    from innovation_hub.database import Idea, Project
    if match.entity_type.value == "idea":
        entity = db.query(Idea).filter(Idea.id == match.entity_id).first()
        entity_title = entity.title if entity else None
    else:
        entity = db.query(Project).filter(Project.id == match.entity_id).first()
        entity_title = entity.name if entity else None

    return {
        "id": match.id,
        "funding_call_id": match.funding_call_id,
        "entity_type": match.entity_type.value,
        "entity_id": match.entity_id,
        "match_score": match.match_score,
        "match_reasoning": match.match_reasoning,
        "strengths": match.strengths or [],
        "gaps": match.gaps or [],
        "is_recommended": match.is_recommended or False,
        "user_rating": match.user_rating,
        "funding_title": funding_title,
        "entity_title": entity_title,
        "created_at": match.created_at,
        "updated_at": match.updated_at
    }


@router.put("/matches/{match_id}/rating")
def update_match_rating(
    match_id: int,
    rating: int = Query(..., ge=1, le=5),
    db: Session = Depends(get_db)
):
    """Uppdatera användarens betyg för en matchning (1-5 stjärnor)"""
    match = FundingMatchCRUD.update_rating(db, match_id, rating)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    return {"message": "Rating updated", "rating": rating}


@router.put("/matches/{match_id}", response_model=FundingMatchResponse)
def update_funding_match(
    match_id: int,
    match_data: FundingMatchUpdate,
    db: Session = Depends(get_db)
):
    """Uppdatera en matchning"""
    match = FundingMatchCRUD.update(db, match_id, match_data)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    # Hämta titlar
    call = FundingCRUD.get_by_id(db, match.funding_call_id)
    funding_title = call.title if call else None

    from innovation_hub.database import Idea, Project
    if match.entity_type.value == "idea":
        entity = db.query(Idea).filter(Idea.id == match.entity_id).first()
        entity_title = entity.title if entity else None
    else:
        entity = db.query(Project).filter(Project.id == match.entity_id).first()
        entity_title = entity.name if entity else None

    return {
        "id": match.id,
        "funding_call_id": match.funding_call_id,
        "entity_type": match.entity_type.value,
        "entity_id": match.entity_id,
        "match_score": match.match_score,
        "match_reasoning": match.match_reasoning,
        "strengths": match.strengths or [],
        "gaps": match.gaps or [],
        "is_recommended": match.is_recommended or False,
        "user_rating": match.user_rating,
        "funding_title": funding_title,
        "entity_title": entity_title,
        "created_at": match.created_at,
        "updated_at": match.updated_at
    }


@router.delete("/matches/{match_id}")
def delete_funding_match(match_id: int, db: Session = Depends(get_db)):
    """Ta bort en matchning"""
    if not FundingMatchCRUD.delete(db, match_id):
        raise HTTPException(status_code=404, detail="Match not found")

    return {"message": "Match deleted successfully"}
