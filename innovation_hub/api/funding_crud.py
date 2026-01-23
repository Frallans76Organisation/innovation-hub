"""
CRUD operations for Funding Calls and Funding Matches
"""
from typing import List, Optional
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from innovation_hub.database import (
    FundingCall, FundingMatch,
    FundingCallStatus, FundingSource, AlignmentEntityType,
    Idea, Project
)
from innovation_hub.models import (
    FundingCallCreate, FundingCallUpdate,
    FundingMatchCreate, FundingMatchUpdate,
    FundingFilter, PaginationParams
)


class FundingCRUD:
    """CRUD operations for FundingCall"""

    @staticmethod
    def get_by_id(db: Session, call_id: int) -> Optional[FundingCall]:
        """Hämta en finansieringsutlysning via ID"""
        return db.query(FundingCall).filter(FundingCall.id == call_id).first()

    @staticmethod
    def get_all(
        db: Session,
        filters: FundingFilter,
        pagination: PaginationParams
    ) -> List[FundingCall]:
        """Hämta alla finansieringsutlysningar med filter och paginering"""
        query = db.query(FundingCall)

        # Applicera filter
        if filters.source:
            query = query.filter(FundingCall.source == FundingSource(filters.source.value))

        if filters.status:
            query = query.filter(FundingCall.status == FundingCallStatus(filters.status.value))

        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(
                or_(
                    FundingCall.title.ilike(search_term),
                    FundingCall.description.ilike(search_term)
                )
            )

        if filters.has_deadline_within_days:
            deadline_limit = date.today() + timedelta(days=filters.has_deadline_within_days)
            query = query.filter(
                and_(
                    FundingCall.deadline >= date.today(),
                    FundingCall.deadline <= deadline_limit
                )
            )

        # Sortera efter deadline (närmaste först), sedan efter skapandedatum
        query = query.order_by(
            FundingCall.deadline.asc().nullslast(),
            FundingCall.created_at.desc()
        )

        # Paginering
        return query.offset(pagination.skip).limit(pagination.limit).all()

    @staticmethod
    def get_open_calls(db: Session) -> List[FundingCall]:
        """Hämta alla öppna utlysningar"""
        return db.query(FundingCall).filter(
            FundingCall.status == FundingCallStatus.OPEN
        ).order_by(FundingCall.deadline.asc().nullslast()).all()

    @staticmethod
    def get_upcoming_deadlines(db: Session, days: int = 30) -> List[FundingCall]:
        """Hämta utlysningar med deadline inom X dagar"""
        deadline_limit = date.today() + timedelta(days=days)
        return db.query(FundingCall).filter(
            and_(
                FundingCall.deadline >= date.today(),
                FundingCall.deadline <= deadline_limit,
                FundingCall.status.in_([FundingCallStatus.OPEN, FundingCallStatus.CLOSING_SOON])
            )
        ).order_by(FundingCall.deadline.asc()).all()

    @staticmethod
    def create(db: Session, call_data: FundingCallCreate) -> FundingCall:
        """Skapa en ny finansieringsutlysning"""
        # Konvertera enum-värden
        source = FundingSource(call_data.source.value) if call_data.source else None
        status = FundingCallStatus(call_data.status.value) if call_data.status else FundingCallStatus.UPCOMING

        call = FundingCall(
            title=call_data.title,
            description=call_data.description,
            source=source,
            status=status,
            external_id=call_data.external_id,
            external_url=call_data.external_url,
            open_date=call_data.open_date,
            deadline=call_data.deadline,
            decision_date=call_data.decision_date,
            total_budget=call_data.total_budget,
            min_grant=call_data.min_grant,
            max_grant=call_data.max_grant,
            co_funding_requirement=call_data.co_funding_requirement,
            eligible_applicants=call_data.eligible_applicants,
            focus_areas=call_data.focus_areas,
            keywords=call_data.keywords,
            requirements_summary=call_data.requirements_summary
        )

        db.add(call)
        db.commit()
        db.refresh(call)
        return call

    @staticmethod
    def update(
        db: Session,
        call_id: int,
        call_data: FundingCallUpdate
    ) -> Optional[FundingCall]:
        """Uppdatera en finansieringsutlysning"""
        call = FundingCRUD.get_by_id(db, call_id)
        if not call:
            return None

        update_data = call_data.model_dump(exclude_unset=True)

        # Konvertera enum-värden
        if 'source' in update_data and update_data['source']:
            update_data['source'] = FundingSource(update_data['source'].value)
        if 'status' in update_data and update_data['status']:
            update_data['status'] = FundingCallStatus(update_data['status'].value)

        for key, value in update_data.items():
            setattr(call, key, value)

        db.commit()
        db.refresh(call)
        return call

    @staticmethod
    def delete(db: Session, call_id: int) -> bool:
        """Ta bort en finansieringsutlysning"""
        call = FundingCRUD.get_by_id(db, call_id)
        if not call:
            return False

        db.delete(call)
        db.commit()
        return True

    @staticmethod
    def get_stats(db: Session) -> dict:
        """Hämta statistik för finansieringsutlysningar"""
        total = db.query(FundingCall).count()

        open_count = db.query(FundingCall).filter(
            FundingCall.status == FundingCallStatus.OPEN
        ).count()

        upcoming_count = db.query(FundingCall).filter(
            FundingCall.status == FundingCallStatus.UPCOMING
        ).count()

        closed_count = db.query(FundingCall).filter(
            FundingCall.status == FundingCallStatus.CLOSED
        ).count()

        # Total budget för öppna utlysningar
        open_calls = db.query(FundingCall).filter(
            FundingCall.status == FundingCallStatus.OPEN
        ).all()
        total_budget = sum(c.total_budget or 0 for c in open_calls)

        # Per källa
        by_source = {}
        for source in FundingSource:
            count = db.query(FundingCall).filter(
                FundingCall.source == source
            ).count()
            by_source[source.value] = count

        # Kommande deadlines (inom 30 dagar)
        upcoming_deadlines = FundingCRUD.get_upcoming_deadlines(db, 30)
        deadline_list = [
            {
                "id": c.id,
                "title": c.title,
                "deadline": c.deadline.isoformat() if c.deadline else None,
                "source": c.source.value if c.source else None
            }
            for c in upcoming_deadlines[:5]  # Max 5
        ]

        return {
            "total_calls": total,
            "open_calls": open_count,
            "upcoming_calls": upcoming_count,
            "closed_calls": closed_count,
            "total_budget_available": total_budget,
            "by_source": by_source,
            "upcoming_deadlines": deadline_list
        }


class FundingMatchCRUD:
    """CRUD operations for FundingMatch"""

    @staticmethod
    def get_by_id(db: Session, match_id: int) -> Optional[FundingMatch]:
        """Hämta en matchning via ID"""
        return db.query(FundingMatch).filter(FundingMatch.id == match_id).first()

    @staticmethod
    def get_for_entity(
        db: Session,
        entity_type: str,
        entity_id: int
    ) -> List[FundingMatch]:
        """Hämta alla matchningar för en specifik entitet (idé eller projekt)"""
        return db.query(FundingMatch).filter(
            and_(
                FundingMatch.entity_type == AlignmentEntityType(entity_type),
                FundingMatch.entity_id == entity_id
            )
        ).order_by(FundingMatch.match_score.desc().nullslast()).all()

    @staticmethod
    def get_for_call(db: Session, call_id: int) -> List[FundingMatch]:
        """Hämta alla matchningar för en specifik utlysning"""
        return db.query(FundingMatch).filter(
            FundingMatch.funding_call_id == call_id
        ).order_by(FundingMatch.match_score.desc().nullslast()).all()

    @staticmethod
    def create(db: Session, match_data: FundingMatchCreate) -> FundingMatch:
        """Skapa en ny matchning"""
        # Validera att utlysningen finns
        call = db.query(FundingCall).filter(
            FundingCall.id == match_data.funding_call_id
        ).first()
        if not call:
            raise ValueError(f"FundingCall with id {match_data.funding_call_id} not found")

        # Validera att entiteten finns
        entity_type = AlignmentEntityType(match_data.entity_type.value)
        if entity_type == AlignmentEntityType.IDEA:
            entity = db.query(Idea).filter(Idea.id == match_data.entity_id).first()
        else:
            entity = db.query(Project).filter(Project.id == match_data.entity_id).first()

        if not entity:
            raise ValueError(f"{match_data.entity_type.value} with id {match_data.entity_id} not found")

        # Kontrollera om matchning redan finns
        existing = db.query(FundingMatch).filter(
            and_(
                FundingMatch.funding_call_id == match_data.funding_call_id,
                FundingMatch.entity_type == entity_type,
                FundingMatch.entity_id == match_data.entity_id
            )
        ).first()

        if existing:
            raise ValueError("Match already exists for this entity and funding call")

        match = FundingMatch(
            funding_call_id=match_data.funding_call_id,
            entity_type=entity_type,
            entity_id=match_data.entity_id,
            match_score=match_data.match_score,
            match_reasoning=match_data.match_reasoning,
            strengths=match_data.strengths,
            gaps=match_data.gaps,
            is_recommended=match_data.is_recommended
        )

        db.add(match)
        db.commit()
        db.refresh(match)
        return match

    @staticmethod
    def update(
        db: Session,
        match_id: int,
        match_data: FundingMatchUpdate
    ) -> Optional[FundingMatch]:
        """Uppdatera en matchning"""
        match = FundingMatchCRUD.get_by_id(db, match_id)
        if not match:
            return None

        update_data = match_data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(match, key, value)

        db.commit()
        db.refresh(match)
        return match

    @staticmethod
    def update_rating(
        db: Session,
        match_id: int,
        rating: int
    ) -> Optional[FundingMatch]:
        """Uppdatera användarens betyg för en matchning"""
        match = FundingMatchCRUD.get_by_id(db, match_id)
        if not match:
            return None

        match.user_rating = rating
        db.commit()
        db.refresh(match)
        return match

    @staticmethod
    def delete(db: Session, match_id: int) -> bool:
        """Ta bort en matchning"""
        match = FundingMatchCRUD.get_by_id(db, match_id)
        if not match:
            return False

        db.delete(match)
        db.commit()
        return True

    @staticmethod
    def get_recommended_for_entity(
        db: Session,
        entity_type: str,
        entity_id: int
    ) -> List[FundingMatch]:
        """Hämta rekommenderade matchningar för en entitet"""
        return db.query(FundingMatch).filter(
            and_(
                FundingMatch.entity_type == AlignmentEntityType(entity_type),
                FundingMatch.entity_id == entity_id,
                FundingMatch.is_recommended == True
            )
        ).order_by(FundingMatch.match_score.desc()).all()
