from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc
from typing import List, Optional
import asyncio
from ..database import User, Category, Idea, Tag, Comment, IdeaTag
from ..database import IdeaStatus, IdeaType, Priority, TargetGroup
from ..models import (
    UserCreate, CategoryCreate, IdeaCreate, IdeaUpdate,
    TagCreate, CommentCreate, IdeaFilter, PaginationParams
)
from ..ai import get_ai_analysis_service

class UserCRUD:
    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def create(db: Session, user_data: UserCreate) -> User:
        db_user = User(**user_data.model_dump())
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def get_or_create(db: Session, email: str, name: str, department: str = None) -> User:
        user = UserCRUD.get_by_email(db, email)
        if not user:
            user_data = UserCreate(email=email, name=name, department=department)
            user = UserCRUD.create(db, user_data)
        return user

class CategoryCRUD:
    @staticmethod
    def get_all(db: Session) -> List[Category]:
        return db.query(Category).order_by(Category.name).all()

    @staticmethod
    def get_by_id(db: Session, category_id: int) -> Optional[Category]:
        return db.query(Category).filter(Category.id == category_id).first()

    @staticmethod
    def create(db: Session, category_data: CategoryCreate) -> Category:
        db_category = Category(**category_data.model_dump())
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        return db_category

class TagCRUD:
    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[Tag]:
        return db.query(Tag).filter(Tag.name == name).first()

    @staticmethod
    def get_or_create(db: Session, name: str) -> Tag:
        tag = TagCRUD.get_by_name(db, name)
        if not tag:
            tag_data = TagCreate(name=name)
            tag = Tag(**tag_data.model_dump())
            db.add(tag)
            db.commit()
            db.refresh(tag)
        return tag

    @staticmethod
    def get_all(db: Session) -> List[Tag]:
        return db.query(Tag).order_by(Tag.name).all()

class IdeaCRUD:
    @staticmethod
    def get_by_id(db: Session, idea_id: int) -> Optional[Idea]:
        return db.query(Idea)\
            .options(
                joinedload(Idea.submitter),
                joinedload(Idea.category),
                joinedload(Idea.tags)
            )\
            .filter(Idea.id == idea_id)\
            .first()

    @staticmethod
    def get_all(
        db: Session,
        filters: IdeaFilter = None,
        pagination: PaginationParams = None
    ) -> List[Idea]:
        query = db.query(Idea)\
            .options(
                joinedload(Idea.submitter),
                joinedload(Idea.category),
                joinedload(Idea.tags)
            )

        if filters:
            if filters.status:
                query = query.filter(Idea.status == IdeaStatus(filters.status))
            if filters.type:
                query = query.filter(Idea.type == IdeaType(filters.type))
            if filters.priority:
                query = query.filter(Idea.priority == Priority(filters.priority))
            if filters.target_group:
                query = query.filter(Idea.target_group == TargetGroup(filters.target_group))
            if filters.category_id:
                query = query.filter(Idea.category_id == filters.category_id)
            if filters.submitter_id:
                query = query.filter(Idea.submitter_id == filters.submitter_id)
            if filters.tag:
                query = query.join(Idea.tags).filter(Tag.name == filters.tag)
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        Idea.title.ilike(search_term),
                        Idea.description.ilike(search_term)
                    )
                )

        query = query.order_by(desc(Idea.created_at))

        if pagination:
            query = query.offset(pagination.skip).limit(pagination.limit)

        return query.all()

    @staticmethod
    def create(db: Session, idea_data: IdeaCreate) -> Idea:
        """Create idea without AI analysis (legacy method)"""
        return IdeaCRUD._create_idea_base(db, idea_data)

    @staticmethod
    async def create_with_ai_analysis(db: Session, idea_data: IdeaCreate) -> Idea:
        """Create idea with AI analysis enhancement"""
        try:
            print(f"🤖 Creating idea with AI analysis: '{idea_data.title}'")

            # Perform AI analysis
            ai_service = get_ai_analysis_service()
            analysis = await ai_service.analyze_idea_comprehensive(
                title=idea_data.title,
                description=idea_data.description,
                idea_type=idea_data.type,
                target_group=idea_data.target_group
            )

            print(f"✅ AI analysis complete: confidence={analysis.confidence_score:.2f}")

            # Create base idea
            db_idea = IdeaCRUD._create_idea_base(db, idea_data)

            # Apply AI enhancements
            if analysis.category_id:
                db_idea.category_id = analysis.category_id
                print(f"🏷️ Auto-assigned category: {analysis.category_name}")

            if analysis.priority:
                db_idea.priority = analysis.priority
                print(f"⚡ Auto-assigned priority: {analysis.priority.value}")

            if analysis.status and analysis.confidence_score > 0.7:
                db_idea.status = analysis.status
                print(f"📊 Auto-assigned status: {analysis.status.value}")

            # Store AI analysis results
            db_idea.ai_sentiment = analysis.sentiment
            db_idea.ai_confidence = analysis.confidence_score
            db_idea.ai_analysis_notes = analysis.analysis_notes

            # Store service mapping results
            db_idea.service_recommendation = analysis.service_recommendation
            db_idea.service_confidence = analysis.service_confidence
            db_idea.service_reasoning = analysis.service_reasoning
            db_idea.matching_services = analysis.matching_services
            db_idea.development_impact = analysis.development_impact

            # Add AI-generated tags
            if analysis.tags:
                for tag_name in analysis.tags:
                    tag = TagCRUD.get_or_create(db, tag_name.strip().lower())
                    # Check if tag already exists for this idea
                    existing = db.query(IdeaTag).filter(
                        IdeaTag.idea_id == db_idea.id,
                        IdeaTag.tag_id == tag.id
                    ).first()
                    if not existing:
                        idea_tag = IdeaTag(idea_id=db_idea.id, tag_id=tag.id)
                        db.add(idea_tag)

                print(f"🏷️ Auto-generated tags: {', '.join(analysis.tags)}")

            db.commit()
            db.refresh(db_idea)

            print(f"✅ Idea created with AI enhancements: ID={db_idea.id}")
            return db_idea

        except Exception as e:
            print(f"❌ AI analysis failed, falling back to basic creation: {e}")
            # Fallback to basic creation if AI fails
            return IdeaCRUD._create_idea_base(db, idea_data)

    @staticmethod
    def _create_idea_base(db: Session, idea_data: IdeaCreate) -> Idea:
        """Base idea creation without AI analysis"""
        # Get or create user
        user = UserCRUD.get_by_email(db, idea_data.submitter_email)
        if not user:
            # Create basic user with just email and name
            user = UserCRUD.get_or_create(
                db,
                email=idea_data.submitter_email,
                name=idea_data.submitter_email.split('@')[0]  # Use email prefix as name
            )

        # Create idea with proper enum conversion
        idea_dict = idea_data.model_dump(exclude={'submitter_email', 'tags'})

        # Convert string enums to database enums
        idea_dict['type'] = IdeaType(idea_dict['type'])
        idea_dict['target_group'] = TargetGroup(idea_dict['target_group'])

        db_idea = Idea(**idea_dict, submitter_id=user.id)
        db.add(db_idea)
        db.flush()  # Flush to get idea ID

        # Handle tags
        if idea_data.tags:
            for tag_name in idea_data.tags:
                tag = TagCRUD.get_or_create(db, tag_name.strip().lower())
                idea_tag = IdeaTag(idea_id=db_idea.id, tag_id=tag.id)
                db.add(idea_tag)

        db.commit()
        db.refresh(db_idea)
        return db_idea

    @staticmethod
    def update(db: Session, idea_id: int, idea_data: IdeaUpdate) -> Optional[Idea]:
        db_idea = db.query(Idea).filter(Idea.id == idea_id).first()
        if not db_idea:
            return None

        # Update basic fields with enum conversion
        update_data = idea_data.model_dump(exclude_unset=True, exclude={'tags'})

        # Convert string enums to database enums
        if 'type' in update_data and update_data['type'] is not None:
            update_data['type'] = IdeaType(update_data['type'])
        if 'status' in update_data and update_data['status'] is not None:
            update_data['status'] = IdeaStatus(update_data['status'])
        if 'priority' in update_data and update_data['priority'] is not None:
            update_data['priority'] = Priority(update_data['priority'])
        if 'target_group' in update_data and update_data['target_group'] is not None:
            update_data['target_group'] = TargetGroup(update_data['target_group'])

        for field, value in update_data.items():
            setattr(db_idea, field, value)

        # Handle tags update
        if idea_data.tags is not None:
            # Remove existing tags
            db.query(IdeaTag).filter(IdeaTag.idea_id == idea_id).delete()

            # Add new tags
            for tag_name in idea_data.tags:
                tag = TagCRUD.get_or_create(db, tag_name.strip().lower())
                idea_tag = IdeaTag(idea_id=idea_id, tag_id=tag.id)
                db.add(idea_tag)

        db.commit()
        db.refresh(db_idea)
        return db_idea

    @staticmethod
    def delete(db: Session, idea_id: int) -> bool:
        db_idea = db.query(Idea).filter(Idea.id == idea_id).first()
        if not db_idea:
            return False

        db.delete(db_idea)
        db.commit()
        return True

    @staticmethod
    def get_stats(db: Session) -> dict:
        total_ideas = db.query(Idea).count()

        # Status distribution
        status_counts = []
        for status in IdeaStatus:
            count = db.query(Idea).filter(Idea.status == status).count()
            status_counts.append({"status": status.value, "count": count})

        # Type distribution
        type_counts = []
        for idea_type in IdeaType:
            count = db.query(Idea).filter(Idea.type == idea_type).count()
            type_counts.append({"type": idea_type.value, "count": count})

        # Recent ideas (last 5)
        recent_ideas = db.query(Idea)\
            .options(
                joinedload(Idea.submitter),
                joinedload(Idea.category),
                joinedload(Idea.tags)
            )\
            .order_by(desc(Idea.created_at))\
            .limit(5)\
            .all()

        return {
            "total_ideas": total_ideas,
            "status_distribution": status_counts,
            "type_distribution": type_counts,
            "recent_ideas": recent_ideas
        }

class CommentCRUD:
    @staticmethod
    def create(db: Session, idea_id: int, comment_data: CommentCreate) -> Comment:
        db_comment = Comment(
            content=comment_data.content,
            idea_id=idea_id,
            author_id=comment_data.author_id
        )
        db.add(db_comment)
        db.commit()
        db.refresh(db_comment)
        return db_comment

    @staticmethod
    def get_by_idea(db: Session, idea_id: int) -> List[Comment]:
        return db.query(Comment)\
            .options(joinedload(Comment.author))\
            .filter(Comment.idea_id == idea_id)\
            .order_by(Comment.created_at)\
            .all()