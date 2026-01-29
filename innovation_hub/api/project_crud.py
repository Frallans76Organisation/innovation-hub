"""
CRUD-operationer för Projekt
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional

from ..database import Project, ProjectIdea, Idea
from ..database import ProjectStatus, ProjectType
from ..models import (
    ProjectCreate, ProjectUpdate, ProjectFilter,
    PaginationParams, ProjectIdeaLink
)


class ProjectCRUD:
    """CRUD-operationer för projekt"""

    @staticmethod
    def get_by_id(db: Session, project_id: int) -> Optional[Project]:
        """Hämta projekt med ID"""
        return db.query(Project)\
            .options(joinedload(Project.ideas))\
            .filter(Project.id == project_id)\
            .first()

    @staticmethod
    def get_all(
        db: Session,
        filters: ProjectFilter = None,
        pagination: PaginationParams = None
    ) -> List[Project]:
        """Hämta alla projekt med filter och paginering"""
        query = db.query(Project)

        if filters:
            if filters.status:
                query = query.filter(Project.status == ProjectStatus(filters.status))
            if filters.project_type:
                query = query.filter(Project.project_type == ProjectType(filters.project_type))
            if filters.owner_department:
                query = query.filter(Project.owner_department.ilike(f"%{filters.owner_department}%"))
            if filters.funding_source:
                query = query.filter(Project.funding_source.ilike(f"%{filters.funding_source}%"))
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        Project.name.ilike(search_term),
                        Project.description.ilike(search_term)
                    )
                )

        query = query.order_by(desc(Project.created_at))

        if pagination:
            query = query.offset(pagination.skip).limit(pagination.limit)

        return query.all()

    @staticmethod
    def create(db: Session, project_data: ProjectCreate) -> Project:
        """Skapa nytt projekt"""
        # Extrahera idea_ids innan vi skapar projektet
        idea_ids = project_data.idea_ids

        # Skapa projekt utan idea_ids
        project_dict = project_data.model_dump(exclude={'idea_ids'})

        # Konvertera enum
        project_dict['project_type'] = ProjectType(project_dict['project_type'])

        db_project = Project(**project_dict)
        db.add(db_project)
        db.flush()  # Flush för att få projekt-ID

        # Koppla idéer om angivna
        if idea_ids:
            for idea_id in idea_ids:
                idea = db.query(Idea).filter(Idea.id == idea_id).first()
                if idea:
                    project_idea = ProjectIdea(
                        project_id=db_project.id,
                        idea_id=idea_id,
                        relationship_type="implements"
                    )
                    db.add(project_idea)

        db.commit()
        db.refresh(db_project)
        return db_project

    @staticmethod
    def update(db: Session, project_id: int, project_data: ProjectUpdate) -> Optional[Project]:
        """Uppdatera projekt"""
        db_project = db.query(Project).filter(Project.id == project_id).first()
        if not db_project:
            return None

        update_data = project_data.model_dump(exclude_unset=True)

        # Konvertera enums
        if 'status' in update_data and update_data['status'] is not None:
            update_data['status'] = ProjectStatus(update_data['status'])
        if 'project_type' in update_data and update_data['project_type'] is not None:
            update_data['project_type'] = ProjectType(update_data['project_type'])

        for field, value in update_data.items():
            setattr(db_project, field, value)

        db.commit()
        db.refresh(db_project)
        return db_project

    @staticmethod
    def delete(db: Session, project_id: int) -> bool:
        """Ta bort projekt"""
        db_project = db.query(Project).filter(Project.id == project_id).first()
        if not db_project:
            return False

        # Ta bort kopplingar först
        db.query(ProjectIdea).filter(ProjectIdea.project_id == project_id).delete()

        db.delete(db_project)
        db.commit()
        return True

    @staticmethod
    def link_idea(
        db: Session,
        project_id: int,
        link_data: ProjectIdeaLink
    ) -> Optional[ProjectIdea]:
        """Koppla idé till projekt"""
        # Kontrollera att projekt och idé finns
        project = db.query(Project).filter(Project.id == project_id).first()
        idea = db.query(Idea).filter(Idea.id == link_data.idea_id).first()

        if not project or not idea:
            return None

        # Kontrollera om koppling redan finns
        existing = db.query(ProjectIdea).filter(
            ProjectIdea.project_id == project_id,
            ProjectIdea.idea_id == link_data.idea_id
        ).first()

        if existing:
            # Uppdatera befintlig koppling
            existing.relationship_type = link_data.relationship_type.value
            existing.notes = link_data.notes
            db.commit()
            db.refresh(existing)
            return existing

        # Skapa ny koppling
        project_idea = ProjectIdea(
            project_id=project_id,
            idea_id=link_data.idea_id,
            relationship_type=link_data.relationship_type.value,
            notes=link_data.notes
        )
        db.add(project_idea)
        db.commit()
        db.refresh(project_idea)
        return project_idea

    @staticmethod
    def unlink_idea(db: Session, project_id: int, idea_id: int) -> bool:
        """Ta bort koppling mellan projekt och idé"""
        result = db.query(ProjectIdea).filter(
            ProjectIdea.project_id == project_id,
            ProjectIdea.idea_id == idea_id
        ).delete()

        db.commit()
        return result > 0

    @staticmethod
    def get_project_ideas(db: Session, project_id: int) -> List[dict]:
        """Hämta alla idéer kopplade till ett projekt"""
        links = db.query(ProjectIdea, Idea)\
            .join(Idea, ProjectIdea.idea_id == Idea.id)\
            .filter(ProjectIdea.project_id == project_id)\
            .all()

        result = []
        for link, idea in links:
            result.append({
                "idea_id": idea.id,
                "idea_title": idea.title,
                "relationship_type": link.relationship_type,
                "notes": link.notes,
                "created_at": link.created_at
            })

        return result

    @staticmethod
    def get_idea_projects(db: Session, idea_id: int) -> List[Project]:
        """Hämta alla projekt kopplade till en idé"""
        return db.query(Project)\
            .join(ProjectIdea, ProjectIdea.project_id == Project.id)\
            .filter(ProjectIdea.idea_id == idea_id)\
            .all()

    @staticmethod
    def get_stats(db: Session) -> dict:
        """Hämta projektstatistik"""
        total_projects = db.query(Project).count()

        # Per status
        by_status = {}
        for status in ProjectStatus:
            count = db.query(Project).filter(Project.status == status).count()
            by_status[status.value] = count

        # Per typ
        by_type = {}
        for project_type in ProjectType:
            count = db.query(Project).filter(Project.project_type == project_type).count()
            by_type[project_type.value] = count

        # Total budget
        total_budget = db.query(func.sum(Project.estimated_budget))\
            .filter(Project.estimated_budget.isnot(None))\
            .scalar() or 0

        # Antal kopplingar
        ideas_linked = db.query(ProjectIdea).count()

        return {
            "total_projects": total_projects,
            "by_status": by_status,
            "by_type": by_type,
            "total_budget": float(total_budget),
            "ideas_linked": ideas_linked
        }

    @staticmethod
    def get_with_idea_count(db: Session, project_id: int) -> Optional[dict]:
        """Hämta projekt med antal kopplade idéer"""
        project = ProjectCRUD.get_by_id(db, project_id)
        if not project:
            return None

        idea_count = db.query(ProjectIdea)\
            .filter(ProjectIdea.project_id == project_id)\
            .count()

        return {
            "project": project,
            "linked_ideas_count": idea_count
        }
