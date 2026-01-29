"""
API-endpoints för Strategidokument och Alignment
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models import (
    StrategyDocumentCreate, StrategyDocumentUpdate, StrategyDocumentResponse,
    StrategyDocumentDetailResponse, StrategyDocumentTypeEnum, StrategyTreeNode,
    StrategicAlignmentCreate, StrategicAlignmentUpdate, StrategicAlignmentResponse,
    AlignmentEntityTypeEnum, StrategyStats, StrategyCoverageReport, StrategyFilter
)
from .strategy_crud import StrategyCRUD, AlignmentCRUD

router = APIRouter(prefix="/api/strategy", tags=["Strategy"])


# =============================================================================
# Strategidokument endpoints
# =============================================================================

@router.get("/", response_model=List[StrategyDocumentResponse])
def get_strategy_documents(
    document_type: Optional[StrategyDocumentTypeEnum] = None,
    level: Optional[int] = Query(None, ge=1, le=3),
    responsible_department: Optional[str] = None,
    is_active: Optional[bool] = None,
    parent_id: Optional[int] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Hämta alla strategidokument med filtrering"""
    filters = StrategyFilter(
        document_type=document_type,
        level=level,
        responsible_department=responsible_department,
        is_active=is_active,
        parent_id=parent_id,
        search=search
    )

    from ..models import PaginationParams
    pagination = PaginationParams(skip=skip, limit=limit)

    docs = StrategyCRUD.get_all(db, filters, pagination)

    # Lägg till alignment_count och children_count
    result = []
    for doc in docs:
        doc_dict = {
            "id": doc.id,
            "title": doc.title,
            "description": doc.description,
            "document_type": doc.document_type.value,
            "source": doc.source,
            "external_id": doc.external_id,
            "external_url": doc.external_url,
            "content": doc.content,
            "parent_id": doc.parent_id,
            "level": doc.level,
            "sort_order": doc.sort_order,
            "responsible_department": doc.responsible_department,
            "responsible_person": doc.responsible_person,
            "time_period": doc.time_period,
            "valid_from": doc.valid_from,
            "valid_to": doc.valid_to,
            "summary": doc.summary,
            "keywords": doc.keywords,
            "is_active": doc.is_active,
            "rag_indexed": doc.rag_indexed,
            "alignment_count": len(doc.alignments) if doc.alignments else 0,
            "children_count": len(doc.children) if doc.children else 0,
            "created_at": doc.created_at,
            "updated_at": doc.updated_at
        }
        result.append(doc_dict)

    return result


@router.get("/stats", response_model=StrategyStats)
def get_strategy_stats(db: Session = Depends(get_db)):
    """Hämta statistik för strategidokument"""
    return StrategyCRUD.get_stats(db)


@router.get("/tree", response_model=List[StrategyTreeNode])
def get_strategy_tree(db: Session = Depends(get_db)):
    """Hämta strategin som hierarkiskt träd"""
    return StrategyCRUD.build_tree(db)


@router.get("/coverage", response_model=StrategyCoverageReport)
def get_strategy_coverage(db: Session = Depends(get_db)):
    """Hämta täckningsrapport för strategin"""
    return AlignmentCRUD.get_coverage_report(db)


@router.get("/{doc_id}", response_model=StrategyDocumentDetailResponse)
def get_strategy_document(doc_id: int, db: Session = Depends(get_db)):
    """Hämta specifikt strategidokument med detaljer"""
    doc = StrategyCRUD.get_by_id(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Strategy document not found")

    # Bygg detaljerat svar
    children = StrategyCRUD.get_children(db, doc_id)
    alignments = AlignmentCRUD.get_for_document(db, doc_id)

    return {
        "id": doc.id,
        "title": doc.title,
        "description": doc.description,
        "document_type": doc.document_type.value,
        "source": doc.source,
        "external_id": doc.external_id,
        "external_url": doc.external_url,
        "content": doc.content,
        "parent_id": doc.parent_id,
        "level": doc.level,
        "sort_order": doc.sort_order,
        "responsible_department": doc.responsible_department,
        "responsible_person": doc.responsible_person,
        "time_period": doc.time_period,
        "valid_from": doc.valid_from,
        "valid_to": doc.valid_to,
        "summary": doc.summary,
        "keywords": doc.keywords,
        "is_active": doc.is_active,
        "rag_indexed": doc.rag_indexed,
        "alignment_count": len(alignments),
        "children_count": len(children),
        "created_at": doc.created_at,
        "updated_at": doc.updated_at,
        "children": [
            {
                "id": c.id,
                "title": c.title,
                "description": c.description,
                "document_type": c.document_type.value,
                "source": c.source,
                "external_id": c.external_id,
                "external_url": c.external_url,
                "content": c.content,
                "parent_id": c.parent_id,
                "level": c.level,
                "sort_order": c.sort_order,
                "responsible_department": c.responsible_department,
                "responsible_person": c.responsible_person,
                "time_period": c.time_period,
                "valid_from": c.valid_from,
                "valid_to": c.valid_to,
                "summary": c.summary,
                "keywords": c.keywords,
                "is_active": c.is_active,
                "rag_indexed": c.rag_indexed,
                "alignment_count": 0,
                "children_count": 0,
                "created_at": c.created_at,
                "updated_at": c.updated_at
            } for c in children
        ],
        "alignments": [
            {
                "id": a.id,
                "entity_type": a.entity_type.value,
                "entity_id": a.entity_id,
                "strategy_document_id": a.strategy_document_id,
                "alignment_score": a.alignment_score,
                "alignment_reasoning": a.alignment_reasoning,
                "verified_by_human": a.verified_by_human,
                "verified_by": a.verified_by,
                "verified_at": a.verified_at,
                "created_at": a.created_at,
                "updated_at": a.updated_at,
                "strategy_title": doc.title,
                "strategy_level": doc.level
            } for a in alignments
        ]
    }


@router.post("/", response_model=StrategyDocumentResponse)
def create_strategy_document(
    doc_data: StrategyDocumentCreate,
    db: Session = Depends(get_db)
):
    """Skapa nytt strategidokument"""
    doc = StrategyCRUD.create(db, doc_data)
    return {
        "id": doc.id,
        "title": doc.title,
        "description": doc.description,
        "document_type": doc.document_type.value,
        "source": doc.source,
        "external_id": doc.external_id,
        "external_url": doc.external_url,
        "content": doc.content,
        "parent_id": doc.parent_id,
        "level": doc.level,
        "sort_order": doc.sort_order,
        "responsible_department": doc.responsible_department,
        "responsible_person": doc.responsible_person,
        "time_period": doc.time_period,
        "valid_from": doc.valid_from,
        "valid_to": doc.valid_to,
        "summary": doc.summary,
        "keywords": doc.keywords,
        "is_active": doc.is_active,
        "rag_indexed": doc.rag_indexed,
        "alignment_count": 0,
        "children_count": 0,
        "created_at": doc.created_at,
        "updated_at": doc.updated_at
    }


@router.put("/{doc_id}", response_model=StrategyDocumentResponse)
def update_strategy_document(
    doc_id: int,
    doc_data: StrategyDocumentUpdate,
    db: Session = Depends(get_db)
):
    """Uppdatera strategidokument"""
    doc = StrategyCRUD.update(db, doc_id, doc_data)
    if not doc:
        raise HTTPException(status_code=404, detail="Strategy document not found")

    return {
        "id": doc.id,
        "title": doc.title,
        "description": doc.description,
        "document_type": doc.document_type.value,
        "source": doc.source,
        "external_id": doc.external_id,
        "external_url": doc.external_url,
        "content": doc.content,
        "parent_id": doc.parent_id,
        "level": doc.level,
        "sort_order": doc.sort_order,
        "responsible_department": doc.responsible_department,
        "responsible_person": doc.responsible_person,
        "time_period": doc.time_period,
        "valid_from": doc.valid_from,
        "valid_to": doc.valid_to,
        "summary": doc.summary,
        "keywords": doc.keywords,
        "is_active": doc.is_active,
        "rag_indexed": doc.rag_indexed,
        "alignment_count": len(doc.alignments) if doc.alignments else 0,
        "children_count": len(doc.children) if doc.children else 0,
        "created_at": doc.created_at,
        "updated_at": doc.updated_at
    }


@router.delete("/{doc_id}")
def delete_strategy_document(doc_id: int, db: Session = Depends(get_db)):
    """Ta bort strategidokument"""
    if not StrategyCRUD.delete(db, doc_id):
        raise HTTPException(status_code=404, detail="Strategy document not found")
    return {"message": "Strategy document deleted successfully"}


# =============================================================================
# Alignment endpoints
# =============================================================================

@router.get("/alignments/entity/{entity_type}/{entity_id}", response_model=List[StrategicAlignmentResponse])
def get_entity_alignments(
    entity_type: AlignmentEntityTypeEnum,
    entity_id: int,
    db: Session = Depends(get_db)
):
    """Hämta alla alignments för en idé eller ett projekt"""
    alignments = AlignmentCRUD.get_for_entity(db, entity_type.value, entity_id)
    return [
        {
            "id": a.id,
            "entity_type": a.entity_type.value,
            "entity_id": a.entity_id,
            "strategy_document_id": a.strategy_document_id,
            "alignment_score": a.alignment_score,
            "alignment_reasoning": a.alignment_reasoning,
            "verified_by_human": a.verified_by_human,
            "verified_by": a.verified_by,
            "verified_at": a.verified_at,
            "created_at": a.created_at,
            "updated_at": a.updated_at,
            "strategy_title": a.strategy_document.title if a.strategy_document else None,
            "strategy_level": a.strategy_document.level if a.strategy_document else None
        } for a in alignments
    ]


@router.post("/alignments/", response_model=StrategicAlignmentResponse)
def create_alignment(
    alignment_data: StrategicAlignmentCreate,
    db: Session = Depends(get_db)
):
    """Skapa ny strategisk alignment"""
    try:
        alignment = AlignmentCRUD.create(db, alignment_data)
        return {
            "id": alignment.id,
            "entity_type": alignment.entity_type.value,
            "entity_id": alignment.entity_id,
            "strategy_document_id": alignment.strategy_document_id,
            "alignment_score": alignment.alignment_score,
            "alignment_reasoning": alignment.alignment_reasoning,
            "verified_by_human": alignment.verified_by_human,
            "verified_by": alignment.verified_by,
            "verified_at": alignment.verified_at,
            "created_at": alignment.created_at,
            "updated_at": alignment.updated_at,
            "strategy_title": alignment.strategy_document.title if alignment.strategy_document else None,
            "strategy_level": alignment.strategy_document.level if alignment.strategy_document else None
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/alignments/{alignment_id}", response_model=StrategicAlignmentResponse)
def update_alignment(
    alignment_id: int,
    alignment_data: StrategicAlignmentUpdate,
    db: Session = Depends(get_db)
):
    """Uppdatera alignment"""
    alignment = AlignmentCRUD.update(db, alignment_id, alignment_data)
    if not alignment:
        raise HTTPException(status_code=404, detail="Alignment not found")

    return {
        "id": alignment.id,
        "entity_type": alignment.entity_type.value,
        "entity_id": alignment.entity_id,
        "strategy_document_id": alignment.strategy_document_id,
        "alignment_score": alignment.alignment_score,
        "alignment_reasoning": alignment.alignment_reasoning,
        "verified_by_human": alignment.verified_by_human,
        "verified_by": alignment.verified_by,
        "verified_at": alignment.verified_at,
        "created_at": alignment.created_at,
        "updated_at": alignment.updated_at,
        "strategy_title": alignment.strategy_document.title if alignment.strategy_document else None,
        "strategy_level": alignment.strategy_document.level if alignment.strategy_document else None
    }


@router.delete("/alignments/{alignment_id}")
def delete_alignment(alignment_id: int, db: Session = Depends(get_db)):
    """Ta bort alignment"""
    if not AlignmentCRUD.delete(db, alignment_id):
        raise HTTPException(status_code=404, detail="Alignment not found")
    return {"message": "Alignment deleted successfully"}
