"""
CRUD-operationer för Strategidokument och Alignment
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional
from datetime import datetime

from ..database import (
    StrategyDocument, StrategicAlignment,
    StrategyDocumentType, AlignmentEntityType,
    Idea, Project
)
from ..models import (
    StrategyDocumentCreate, StrategyDocumentUpdate,
    StrategicAlignmentCreate, StrategicAlignmentUpdate,
    StrategyFilter, PaginationParams
)


class StrategyCRUD:
    """CRUD-operationer för strategidokument"""

    @staticmethod
    def get_by_id(db: Session, doc_id: int) -> Optional[StrategyDocument]:
        """Hämta strategidokument med ID"""
        return db.query(StrategyDocument)\
            .options(joinedload(StrategyDocument.children))\
            .options(joinedload(StrategyDocument.alignments))\
            .filter(StrategyDocument.id == doc_id)\
            .first()

    @staticmethod
    def get_all(
        db: Session,
        filters: StrategyFilter = None,
        pagination: PaginationParams = None
    ) -> List[StrategyDocument]:
        """Hämta alla strategidokument med filter och paginering"""
        query = db.query(StrategyDocument)

        if filters:
            if filters.document_type:
                query = query.filter(
                    StrategyDocument.document_type == StrategyDocumentType(filters.document_type)
                )
            if filters.level:
                query = query.filter(StrategyDocument.level == filters.level)
            if filters.responsible_department:
                query = query.filter(
                    StrategyDocument.responsible_department.ilike(f"%{filters.responsible_department}%")
                )
            if filters.is_active is not None:
                query = query.filter(StrategyDocument.is_active == filters.is_active)
            if filters.parent_id is not None:
                query = query.filter(StrategyDocument.parent_id == filters.parent_id)
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        StrategyDocument.title.ilike(search_term),
                        StrategyDocument.description.ilike(search_term),
                        StrategyDocument.content.ilike(search_term)
                    )
                )

        query = query.order_by(StrategyDocument.level, StrategyDocument.sort_order, StrategyDocument.title)

        if pagination:
            query = query.offset(pagination.skip).limit(pagination.limit)

        return query.all()

    @staticmethod
    def get_root_documents(db: Session) -> List[StrategyDocument]:
        """Hämta alla rotdokument (utan förälder)"""
        return db.query(StrategyDocument)\
            .filter(StrategyDocument.parent_id.is_(None))\
            .filter(StrategyDocument.is_active == True)\
            .order_by(StrategyDocument.sort_order, StrategyDocument.title)\
            .all()

    @staticmethod
    def get_children(db: Session, parent_id: int) -> List[StrategyDocument]:
        """Hämta alla barn till ett dokument"""
        return db.query(StrategyDocument)\
            .filter(StrategyDocument.parent_id == parent_id)\
            .filter(StrategyDocument.is_active == True)\
            .order_by(StrategyDocument.sort_order, StrategyDocument.title)\
            .all()

    @staticmethod
    def create(db: Session, doc_data: StrategyDocumentCreate) -> StrategyDocument:
        """Skapa nytt strategidokument"""
        doc_dict = doc_data.model_dump()

        # Konvertera enum
        doc_dict['document_type'] = StrategyDocumentType(doc_dict['document_type'])

        db_doc = StrategyDocument(**doc_dict)
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)
        return db_doc

    @staticmethod
    def update(db: Session, doc_id: int, doc_data: StrategyDocumentUpdate) -> Optional[StrategyDocument]:
        """Uppdatera strategidokument"""
        db_doc = db.query(StrategyDocument).filter(StrategyDocument.id == doc_id).first()
        if not db_doc:
            return None

        update_data = doc_data.model_dump(exclude_unset=True)

        # Konvertera enum
        if 'document_type' in update_data and update_data['document_type'] is not None:
            update_data['document_type'] = StrategyDocumentType(update_data['document_type'])

        for field, value in update_data.items():
            setattr(db_doc, field, value)

        db.commit()
        db.refresh(db_doc)
        return db_doc

    @staticmethod
    def delete(db: Session, doc_id: int) -> bool:
        """Ta bort strategidokument"""
        db_doc = db.query(StrategyDocument).filter(StrategyDocument.id == doc_id).first()
        if not db_doc:
            return False

        # Ta bort alignments först
        db.query(StrategicAlignment)\
            .filter(StrategicAlignment.strategy_document_id == doc_id)\
            .delete()

        # Uppdatera barn till att inte ha förälder
        db.query(StrategyDocument)\
            .filter(StrategyDocument.parent_id == doc_id)\
            .update({"parent_id": None})

        db.delete(db_doc)
        db.commit()
        return True

    @staticmethod
    def build_tree(db: Session, parent_id: Optional[int] = None) -> List[dict]:
        """Bygg hierarkiskt träd av strategidokument"""
        if parent_id is None:
            docs = StrategyCRUD.get_root_documents(db)
        else:
            docs = StrategyCRUD.get_children(db, parent_id)

        result = []
        for doc in docs:
            # Räkna alignments
            alignment_count = db.query(StrategicAlignment)\
                .filter(StrategicAlignment.strategy_document_id == doc.id)\
                .count()

            node = {
                "id": doc.id,
                "title": doc.title,
                "level": doc.level,
                "document_type": doc.document_type.value,
                "is_active": doc.is_active,
                "alignment_count": alignment_count,
                "children": StrategyCRUD.build_tree(db, doc.id)
            }
            result.append(node)

        return result

    @staticmethod
    def get_stats(db: Session) -> dict:
        """Hämta statistik för strategidokument"""
        total_documents = db.query(StrategyDocument).count()
        active_count = db.query(StrategyDocument)\
            .filter(StrategyDocument.is_active == True)\
            .count()

        # Per typ
        by_type = {}
        for doc_type in StrategyDocumentType:
            count = db.query(StrategyDocument)\
                .filter(StrategyDocument.document_type == doc_type)\
                .count()
            by_type[doc_type.value] = count

        # Per nivå
        by_level = {}
        for level in [1, 2, 3]:
            count = db.query(StrategyDocument)\
                .filter(StrategyDocument.level == level)\
                .count()
            by_level[level] = count

        # Alignment-statistik
        total_alignments = db.query(StrategicAlignment).count()

        avg_score = db.query(func.avg(StrategicAlignment.alignment_score))\
            .filter(StrategicAlignment.alignment_score.isnot(None))\
            .scalar() or 0

        ideas_aligned = db.query(StrategicAlignment)\
            .filter(StrategicAlignment.entity_type == AlignmentEntityType.IDEA)\
            .distinct(StrategicAlignment.entity_id)\
            .count()

        projects_aligned = db.query(StrategicAlignment)\
            .filter(StrategicAlignment.entity_type == AlignmentEntityType.PROJECT)\
            .distinct(StrategicAlignment.entity_id)\
            .count()

        return {
            "total_documents": total_documents,
            "by_type": by_type,
            "by_level": by_level,
            "active_count": active_count,
            "total_alignments": total_alignments,
            "avg_alignment_score": float(avg_score),
            "ideas_aligned": ideas_aligned,
            "projects_aligned": projects_aligned
        }


class AlignmentCRUD:
    """CRUD-operationer för strategiska alignments"""

    @staticmethod
    def get_by_id(db: Session, alignment_id: int) -> Optional[StrategicAlignment]:
        """Hämta alignment med ID"""
        return db.query(StrategicAlignment)\
            .options(joinedload(StrategicAlignment.strategy_document))\
            .filter(StrategicAlignment.id == alignment_id)\
            .first()

    @staticmethod
    def get_for_entity(
        db: Session,
        entity_type: str,
        entity_id: int
    ) -> List[StrategicAlignment]:
        """Hämta alla alignments för en entitet"""
        return db.query(StrategicAlignment)\
            .options(joinedload(StrategicAlignment.strategy_document))\
            .filter(
                StrategicAlignment.entity_type == AlignmentEntityType(entity_type),
                StrategicAlignment.entity_id == entity_id
            )\
            .order_by(desc(StrategicAlignment.alignment_score))\
            .all()

    @staticmethod
    def get_for_document(db: Session, doc_id: int) -> List[StrategicAlignment]:
        """Hämta alla alignments för ett strategidokument"""
        return db.query(StrategicAlignment)\
            .filter(StrategicAlignment.strategy_document_id == doc_id)\
            .order_by(desc(StrategicAlignment.alignment_score))\
            .all()

    @staticmethod
    def create(db: Session, alignment_data: StrategicAlignmentCreate) -> StrategicAlignment:
        """Skapa ny alignment"""
        alignment_dict = alignment_data.model_dump()

        # Konvertera enum
        alignment_dict['entity_type'] = AlignmentEntityType(alignment_dict['entity_type'])

        # Kontrollera att entitet finns
        if alignment_dict['entity_type'] == AlignmentEntityType.IDEA:
            entity = db.query(Idea).filter(Idea.id == alignment_dict['entity_id']).first()
        else:
            entity = db.query(Project).filter(Project.id == alignment_dict['entity_id']).first()

        if not entity:
            raise ValueError(f"Entity not found: {alignment_dict['entity_type'].value} {alignment_dict['entity_id']}")

        # Kontrollera att strategidokument finns
        doc = db.query(StrategyDocument)\
            .filter(StrategyDocument.id == alignment_dict['strategy_document_id'])\
            .first()
        if not doc:
            raise ValueError(f"Strategy document not found: {alignment_dict['strategy_document_id']}")

        # Kontrollera om alignment redan finns
        existing = db.query(StrategicAlignment).filter(
            StrategicAlignment.entity_type == alignment_dict['entity_type'],
            StrategicAlignment.entity_id == alignment_dict['entity_id'],
            StrategicAlignment.strategy_document_id == alignment_dict['strategy_document_id']
        ).first()

        if existing:
            # Uppdatera befintlig
            existing.alignment_score = alignment_dict.get('alignment_score')
            existing.alignment_reasoning = alignment_dict.get('alignment_reasoning')
            db.commit()
            db.refresh(existing)
            return existing

        db_alignment = StrategicAlignment(**alignment_dict)
        db.add(db_alignment)
        db.commit()
        db.refresh(db_alignment)
        return db_alignment

    @staticmethod
    def update(
        db: Session,
        alignment_id: int,
        alignment_data: StrategicAlignmentUpdate
    ) -> Optional[StrategicAlignment]:
        """Uppdatera alignment"""
        db_alignment = db.query(StrategicAlignment)\
            .filter(StrategicAlignment.id == alignment_id)\
            .first()
        if not db_alignment:
            return None

        update_data = alignment_data.model_dump(exclude_unset=True)

        # Hantera verifiering
        if 'verified_by_human' in update_data and update_data['verified_by_human']:
            update_data['verified_at'] = datetime.utcnow()

        for field, value in update_data.items():
            setattr(db_alignment, field, value)

        db.commit()
        db.refresh(db_alignment)
        return db_alignment

    @staticmethod
    def delete(db: Session, alignment_id: int) -> bool:
        """Ta bort alignment"""
        result = db.query(StrategicAlignment)\
            .filter(StrategicAlignment.id == alignment_id)\
            .delete()
        db.commit()
        return result > 0

    @staticmethod
    def delete_for_entity(db: Session, entity_type: str, entity_id: int) -> int:
        """Ta bort alla alignments för en entitet"""
        result = db.query(StrategicAlignment).filter(
            StrategicAlignment.entity_type == AlignmentEntityType(entity_type),
            StrategicAlignment.entity_id == entity_id
        ).delete()
        db.commit()
        return result

    @staticmethod
    def get_coverage_report(db: Session) -> dict:
        """Generera täckningsrapport för strategin"""
        total_goals = db.query(StrategyDocument)\
            .filter(StrategyDocument.is_active == True)\
            .count()

        goals_with_alignments = db.query(StrategyDocument)\
            .join(StrategicAlignment, StrategicAlignment.strategy_document_id == StrategyDocument.id)\
            .filter(StrategyDocument.is_active == True)\
            .distinct()\
            .count()

        coverage_percentage = (goals_with_alignments / total_goals * 100) if total_goals > 0 else 0

        # Mål utan kopplingar
        uncovered = db.query(StrategyDocument)\
            .outerjoin(StrategicAlignment)\
            .filter(StrategyDocument.is_active == True)\
            .filter(StrategicAlignment.id.is_(None))\
            .all()

        uncovered_goals = [
            {"id": g.id, "title": g.title, "level": g.level}
            for g in uncovered
        ]

        # Mål med flest kopplingar
        most_aligned = db.query(
            StrategyDocument,
            func.count(StrategicAlignment.id).label('count')
        ).join(StrategicAlignment)\
            .filter(StrategyDocument.is_active == True)\
            .group_by(StrategyDocument.id)\
            .order_by(desc('count'))\
            .limit(10)\
            .all()

        most_aligned_goals = [
            {"id": g.id, "title": g.title, "alignment_count": count}
            for g, count in most_aligned
        ]

        return {
            "total_goals": total_goals,
            "goals_with_alignments": goals_with_alignments,
            "coverage_percentage": round(coverage_percentage, 1),
            "uncovered_goals": uncovered_goals,
            "most_aligned_goals": most_aligned_goals
        }
