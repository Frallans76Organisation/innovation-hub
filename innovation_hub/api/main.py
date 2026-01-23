from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from ..database import get_db, Base, engine
from ..models import (
    IdeaResponse, IdeaCreate, IdeaUpdate, IdeaStats,
    CategoryResponse, CategoryCreate,
    TagResponse, CommentResponse, CommentCreate,
    IdeaFilter, PaginationParams,
    IdeaTypeEnum, IdeaStatusEnum, PriorityEnum, TargetGroupEnum,
    AnalysisStats
)
from .crud import IdeaCRUD, CategoryCRUD, TagCRUD, CommentCRUD
from .analysis_crud import AnalysisCRUD
from ..database import IdeaTag
from .documents import router as documents_router

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Innovation Hub API",
    description="API for managing ideas, needs, and innovation in Swedish organizations",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include document management router
app.include_router(documents_router)

# Include project management router
from .projects import router as projects_router
app.include_router(projects_router)

# Include strategy management router
from .strategy import router as strategy_router
app.include_router(strategy_router)

# Include funding management router
from .funding import router as funding_router
app.include_router(funding_router)

# Ideas endpoints
@app.get("/api/ideas", response_model=List[IdeaResponse])
def get_ideas(
    status: Optional[IdeaStatusEnum] = None,
    type: Optional[IdeaTypeEnum] = None,
    priority: Optional[PriorityEnum] = None,
    target_group: Optional[TargetGroupEnum] = None,
    category_id: Optional[int] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all ideas with optional filtering and pagination"""
    filters = IdeaFilter(
        status=status,
        type=type,
        priority=priority,
        target_group=target_group,
        category_id=category_id,
        tag=tag,
        search=search
    )
    pagination = PaginationParams(skip=skip, limit=limit)
    return IdeaCRUD.get_all(db, filters, pagination)

@app.get("/api/ideas/stats", response_model=IdeaStats)
def get_idea_stats(db: Session = Depends(get_db)):
    """Get statistics about ideas"""
    return IdeaCRUD.get_stats(db)

@app.get("/api/ideas/{idea_id}", response_model=IdeaResponse)
def get_idea(idea_id: int, db: Session = Depends(get_db)):
    """Get a specific idea by ID"""
    idea = IdeaCRUD.get_by_id(db, idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    return idea

@app.post("/api/ideas", response_model=IdeaResponse)
async def create_idea(idea: IdeaCreate, db: Session = Depends(get_db)):
    """Create a new idea with AI analysis"""
    return await IdeaCRUD.create_with_ai_analysis(db, idea)

@app.put("/api/ideas/{idea_id}", response_model=IdeaResponse)
def update_idea(idea_id: int, idea: IdeaUpdate, db: Session = Depends(get_db)):
    """Update an existing idea"""
    updated_idea = IdeaCRUD.update(db, idea_id, idea)
    if not updated_idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    return updated_idea

@app.delete("/api/ideas/{idea_id}")
def delete_idea(idea_id: int, db: Session = Depends(get_db)):
    """Delete an idea"""
    if not IdeaCRUD.delete(db, idea_id):
        raise HTTPException(status_code=404, detail="Idea not found")
    return {"message": "Idea deleted successfully"}

@app.post("/api/ideas/{idea_id}/analyze", response_model=IdeaResponse)
async def analyze_existing_idea(idea_id: int, db: Session = Depends(get_db)):
    """Run AI analysis on an existing idea and update it"""
    # Get existing idea
    idea = IdeaCRUD.get_by_id(db, idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    try:
        from ..ai import get_ai_analysis_service

        print(f"🤖 Running AI analysis on existing idea: '{idea.title}'")

        # Perform AI analysis (includes service mapping)
        ai_service = get_ai_analysis_service()
        analysis = await ai_service.analyze_idea_comprehensive(
            title=idea.title,
            description=idea.description,
            idea_type=idea.type.value,
            target_group=idea.target_group.value
        )

        # Apply AI enhancements
        updates_made = []

        if analysis.category_id and analysis.category_id != idea.category_id:
            idea.category_id = analysis.category_id
            updates_made.append(f"category: {analysis.category_name}")

        if analysis.priority and analysis.priority != idea.priority:
            idea.priority = analysis.priority
            updates_made.append(f"priority: {analysis.priority.value}")

        if analysis.status and analysis.confidence_score > 0.8:
            # Only auto-update status if confidence is very high
            if analysis.status != idea.status:
                idea.status = analysis.status
                updates_made.append(f"status: {analysis.status.value}")

        # Update AI analysis results
        idea.ai_sentiment = analysis.sentiment
        idea.ai_confidence = analysis.confidence_score
        idea.ai_analysis_notes = analysis.analysis_notes

        # Update service mapping results
        idea.service_recommendation = analysis.service_recommendation
        idea.service_confidence = analysis.service_confidence
        idea.service_reasoning = analysis.service_reasoning
        idea.matching_services = analysis.matching_services
        idea.development_impact = analysis.development_impact
        updates_made.append("service mapping")

        # Add new AI-generated tags (preserve existing ones)
        if analysis.tags:
            for tag_name in analysis.tags:
                tag = TagCRUD.get_or_create(db, tag_name.strip().lower())
                # Check if tag already exists for this idea
                existing = db.query(IdeaTag).filter(
                    IdeaTag.idea_id == idea.id,
                    IdeaTag.tag_id == tag.id
                ).first()
                if not existing:
                    idea_tag = IdeaTag(idea_id=idea.id, tag_id=tag.id)
                    db.add(idea_tag)
                    updates_made.append(f"tag: {tag_name}")

        db.commit()
        db.refresh(idea)

        print(f"✅ AI analysis applied to idea {idea_id}: {', '.join(updates_made) if updates_made else 'no changes needed'}")

        return idea

    except Exception as e:
        print(f"❌ AI analysis failed for idea {idea_id}: {e}")
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")

# Categories endpoints
@app.get("/api/categories", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    """Get all categories"""
    return CategoryCRUD.get_all(db)

@app.post("/api/categories", response_model=CategoryResponse)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    """Create a new category"""
    return CategoryCRUD.create(db, category)

# Tags endpoints
@app.get("/api/tags", response_model=List[TagResponse])
def get_tags(db: Session = Depends(get_db)):
    """Get all tags"""
    return TagCRUD.get_all(db)

# Comments endpoints
@app.get("/api/ideas/{idea_id}/comments", response_model=List[CommentResponse])
def get_idea_comments(idea_id: int, db: Session = Depends(get_db)):
    """Get all comments for an idea"""
    # Verify idea exists
    idea = IdeaCRUD.get_by_id(db, idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    return CommentCRUD.get_by_idea(db, idea_id)

@app.post("/api/ideas/{idea_id}/comments", response_model=CommentResponse)
def create_comment(
    idea_id: int,
    comment: CommentCreate,
    db: Session = Depends(get_db)
):
    """Add a comment to an idea"""
    # Verify idea exists
    idea = IdeaCRUD.get_by_id(db, idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    return CommentCRUD.create(db, idea_id, comment)

# Vote endpoints
@app.post("/api/ideas/{idea_id}/vote")
def toggle_vote(idea_id: int, user_id: int = Query(...), db: Session = Depends(get_db)):
    """Toggle vote for an idea (thumbs up/down)"""
    from ..database.models import Vote, Idea

    # Verify idea exists
    idea = db.query(Idea).filter(Idea.id == idea_id).first()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    # Check if user already voted
    existing_vote = db.query(Vote).filter(
        Vote.idea_id == idea_id,
        Vote.user_id == user_id
    ).first()

    if existing_vote:
        # Remove vote
        db.delete(existing_vote)
        idea.vote_count = max(0, idea.vote_count - 1)
        db.commit()
        return {"status": "removed", "vote_count": idea.vote_count}
    else:
        # Add vote
        vote = Vote(idea_id=idea_id, user_id=user_id)
        db.add(vote)
        idea.vote_count = idea.vote_count + 1
        db.commit()
        return {"status": "added", "vote_count": idea.vote_count}

@app.get("/api/ideas/{idea_id}/vote/status")
def get_vote_status(idea_id: int, user_id: int = Query(...), db: Session = Depends(get_db)):
    """Check if user has voted for an idea"""
    from ..database.models import Vote

    vote = db.query(Vote).filter(
        Vote.idea_id == idea_id,
        Vote.user_id == user_id
    ).first()

    return {"has_voted": vote is not None}

# Analysis endpoints
@app.get("/api/analysis/stats", response_model=AnalysisStats)
def get_analysis_stats(db: Session = Depends(get_db)):
    """Get comprehensive analysis statistics including service mapping"""
    return AnalysisCRUD.get_analysis_stats(db)

# Health check endpoints
@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint with database connectivity check"""
    try:
        # Check database connectivity
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        return {
            "status": "unhealthy",
            "message": "Innovation Hub API is running but database is unavailable",
            "database": db_status
        }

    return {
        "status": "healthy",
        "message": "Innovation Hub API is running",
        "database": db_status,
        "version": "1.0.0"
    }

@app.get("/api/health/ready")
def readiness_check(db: Session = Depends(get_db)):
    """Readiness probe - checks if app is ready to serve traffic"""
    try:
        # Check if database is accessible
        from sqlalchemy import text
        db.execute(text("SELECT 1"))

        # Check if critical tables exist
        from ..database.models import Idea, Category
        db.query(Idea).first()
        db.query(Category).first()

        return {"status": "ready", "message": "Application is ready to serve traffic"}
    except Exception as e:
        return {
            "status": "not_ready",
            "message": f"Application is not ready: {str(e)}"
        }

@app.get("/api/health/live")
def liveness_check():
    """Liveness probe - simple check if app is alive"""
    return {"status": "alive", "message": "Application is alive"}

# Mount static files for frontend
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

# Root endpoint - serve frontend
@app.get("/")
def root():
    """Serve frontend application"""
    frontend_index = os.path.join(frontend_path, "index.html")
    if os.path.exists(frontend_index):
        return FileResponse(frontend_index)
    else:
        return {
            "message": "Innovation Hub API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/api/health",
            "frontend": "Frontend not found - check frontend directory"
        }