"""
API endpoints för Projekt
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database.connection import get_db
from ..models import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectDetailResponse,
    ProjectFilter, PaginationParams, ProjectIdeaLink, ProjectIdeaResponse,
    ProjectStats, ProjectStatusEnum, ProjectTypeEnum
)
from .project_crud import ProjectCRUD

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("/", response_model=List[ProjectResponse])
def get_projects(
    status: Optional[ProjectStatusEnum] = None,
    project_type: Optional[ProjectTypeEnum] = None,
    owner_department: Optional[str] = None,
    funding_source: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Hämta alla projekt med valfria filter"""
    filters = ProjectFilter(
        status=status,
        project_type=project_type,
        owner_department=owner_department,
        funding_source=funding_source,
        search=search
    )
    pagination = PaginationParams(skip=skip, limit=limit)

    projects = ProjectCRUD.get_all(db, filters, pagination)

    # Lägg till antal kopplade idéer för varje projekt
    result = []
    for project in projects:
        project_dict = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "status": project.status.value,
            "project_type": project.project_type.value,
            "planned_start": project.planned_start,
            "planned_end": project.planned_end,
            "actual_start": project.actual_start,
            "actual_end": project.actual_end,
            "estimated_budget": project.estimated_budget,
            "funding_source": project.funding_source,
            "owner_department": project.owner_department,
            "contact_email": project.contact_email,
            "project_manager": project.project_manager,
            "ai_summary": project.ai_summary,
            "ai_strategic_alignment": project.ai_strategic_alignment,
            "rag_indexed": project.rag_indexed,
            "linked_ideas_count": len(project.ideas) if project.ideas else 0,
            "created_at": project.created_at,
            "updated_at": project.updated_at
        }
        result.append(project_dict)

    return result


@router.get("/stats", response_model=ProjectStats)
def get_project_stats(db: Session = Depends(get_db)):
    """Hämta projektstatistik"""
    return ProjectCRUD.get_stats(db)


@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """Hämta ett specifikt projekt med alla detaljer"""
    project = ProjectCRUD.get_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projektet hittades inte")

    # Hämta kopplade idéer
    linked_ideas = ProjectCRUD.get_project_ideas(db, project_id)

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "status": project.status.value,
        "project_type": project.project_type.value,
        "planned_start": project.planned_start,
        "planned_end": project.planned_end,
        "actual_start": project.actual_start,
        "actual_end": project.actual_end,
        "estimated_budget": project.estimated_budget,
        "funding_source": project.funding_source,
        "owner_department": project.owner_department,
        "contact_email": project.contact_email,
        "project_manager": project.project_manager,
        "ai_summary": project.ai_summary,
        "ai_strategic_alignment": project.ai_strategic_alignment,
        "rag_indexed": project.rag_indexed,
        "linked_ideas_count": len(linked_ideas),
        "linked_ideas": linked_ideas,
        "created_at": project.created_at,
        "updated_at": project.updated_at
    }


@router.post("/", response_model=ProjectResponse, status_code=201)
def create_project(project_data: ProjectCreate, db: Session = Depends(get_db)):
    """Skapa nytt projekt"""
    project = ProjectCRUD.create(db, project_data)

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "status": project.status.value,
        "project_type": project.project_type.value,
        "planned_start": project.planned_start,
        "planned_end": project.planned_end,
        "actual_start": project.actual_start,
        "actual_end": project.actual_end,
        "estimated_budget": project.estimated_budget,
        "funding_source": project.funding_source,
        "owner_department": project.owner_department,
        "contact_email": project.contact_email,
        "project_manager": project.project_manager,
        "ai_summary": project.ai_summary,
        "ai_strategic_alignment": project.ai_strategic_alignment,
        "rag_indexed": project.rag_indexed,
        "linked_ideas_count": len(project.ideas) if project.ideas else 0,
        "created_at": project.created_at,
        "updated_at": project.updated_at
    }


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """Uppdatera projekt"""
    project = ProjectCRUD.update(db, project_id, project_data)
    if not project:
        raise HTTPException(status_code=404, detail="Projektet hittades inte")

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "status": project.status.value,
        "project_type": project.project_type.value,
        "planned_start": project.planned_start,
        "planned_end": project.planned_end,
        "actual_start": project.actual_start,
        "actual_end": project.actual_end,
        "estimated_budget": project.estimated_budget,
        "funding_source": project.funding_source,
        "owner_department": project.owner_department,
        "contact_email": project.contact_email,
        "project_manager": project.project_manager,
        "ai_summary": project.ai_summary,
        "ai_strategic_alignment": project.ai_strategic_alignment,
        "rag_indexed": project.rag_indexed,
        "linked_ideas_count": len(project.ideas) if project.ideas else 0,
        "created_at": project.created_at,
        "updated_at": project.updated_at
    }


@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """Ta bort projekt"""
    success = ProjectCRUD.delete(db, project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Projektet hittades inte")

    return {"message": "Projektet har tagits bort", "id": project_id}


# =============================================================================
# Idékopplingar
# =============================================================================

@router.get("/{project_id}/ideas", response_model=List[ProjectIdeaResponse])
def get_project_ideas(project_id: int, db: Session = Depends(get_db)):
    """Hämta alla idéer kopplade till ett projekt"""
    project = ProjectCRUD.get_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projektet hittades inte")

    return ProjectCRUD.get_project_ideas(db, project_id)


@router.post("/{project_id}/ideas", response_model=ProjectIdeaResponse, status_code=201)
def link_idea_to_project(
    project_id: int,
    link_data: ProjectIdeaLink,
    db: Session = Depends(get_db)
):
    """Koppla idé till projekt"""
    result = ProjectCRUD.link_idea(db, project_id, link_data)
    if not result:
        raise HTTPException(
            status_code=404,
            detail="Projektet eller idén hittades inte"
        )

    # Hämta idétitel för respons
    from ..database import Idea
    idea = db.query(Idea).filter(Idea.id == link_data.idea_id).first()

    return {
        "idea_id": result.idea_id,
        "idea_title": idea.title if idea else "Okänd",
        "relationship_type": result.relationship_type,
        "notes": result.notes,
        "created_at": result.created_at
    }


@router.delete("/{project_id}/ideas/{idea_id}")
def unlink_idea_from_project(
    project_id: int,
    idea_id: int,
    db: Session = Depends(get_db)
):
    """Ta bort koppling mellan projekt och idé"""
    success = ProjectCRUD.unlink_idea(db, project_id, idea_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Kopplingen hittades inte"
        )

    return {
        "message": "Kopplingen har tagits bort",
        "project_id": project_id,
        "idea_id": idea_id
    }
