from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, Float, JSON, Boolean, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .connection import Base
import enum


# =============================================================================
# Projekt-relaterade Enums
# =============================================================================

class ProjectStatus(enum.Enum):
    PROPOSED = "föreslagen"
    PLANNING = "planering"
    IN_PROGRESS = "pågående"
    ON_HOLD = "pausad"
    COMPLETED = "avslutad"
    CANCELLED = "avbruten"


class ProjectType(enum.Enum):
    INTERNAL = "intern_utveckling"
    VINNOVA = "vinnova"
    EU_FUNDED = "eu_finansierad"
    EXTERNAL_COLLAB = "externt_samarbete"
    MAINTENANCE = "förvaltning"


# =============================================================================
# Idé-relaterade Enums
# =============================================================================

class IdeaType(enum.Enum):
    IDEA = "idé"
    PROBLEM = "problem"
    NEED = "behov"
    IMPROVEMENT = "förbättring"

class IdeaStatus(enum.Enum):
    NEW = "ny"
    REVIEWING = "granskning"
    APPROVED = "godkänd"
    IN_DEVELOPMENT = "utveckling"
    IMPLEMENTED = "implementerad"
    REJECTED = "avvisad"

class Priority(enum.Enum):
    LOW = "låg"
    MEDIUM = "medel"
    HIGH = "hög"

class TargetGroup(enum.Enum):
    CITIZENS = "medborgare"
    BUSINESSES = "företag"
    EMPLOYEES = "medarbetare"
    OTHER_ORGS = "andra organisationer"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    department = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    ideas = relationship("Idea", back_populates="submitter")

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    color = Column(String, default="#3498db")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    ideas = relationship("Idea", back_populates="category")

class Idea(Base):
    __tablename__ = "ideas"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    type = Column(Enum(IdeaType), nullable=False)
    status = Column(Enum(IdeaStatus), default=IdeaStatus.NEW)
    priority = Column(Enum(Priority), default=Priority.MEDIUM)
    target_group = Column(Enum(TargetGroup), nullable=False)

    # AI Analysis results
    ai_sentiment = Column(String)
    ai_confidence = Column(Float)
    ai_analysis_notes = Column(Text)

    # Service Mapping results
    service_recommendation = Column(String)  # existing_service, develop_existing, new_service
    service_confidence = Column(Float)
    service_reasoning = Column(Text)
    matching_services = Column(JSON)  # Store matched services as JSON
    development_impact = Column(String)  # low, medium, high

    # Engagement metrics
    vote_count = Column(Integer, default=0)

    # Relationships
    submitter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))

    submitter = relationship("User", back_populates="ideas")
    category = relationship("Category", back_populates="ideas")
    tags = relationship("Tag", secondary="idea_tags", back_populates="ideas")
    comments = relationship("Comment", back_populates="idea")
    votes = relationship("Vote", back_populates="idea", cascade="all, delete-orphan")
    projects = relationship("Project", secondary="project_ideas", back_populates="ideas")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    ideas = relationship("Idea", secondary="idea_tags", back_populates="tags")

class IdeaTag(Base):
    __tablename__ = "idea_tags"

    idea_id = Column(Integer, ForeignKey("ideas.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), primary_key=True)

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)

    # Relationships
    idea_id = Column(Integer, ForeignKey("ideas.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    idea = relationship("Idea", back_populates="comments")
    author = relationship("User")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Vote(Base):
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)

    # Relationships
    idea_id = Column(Integer, ForeignKey("ideas.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    idea = relationship("Idea", back_populates="votes")
    user = relationship("User")

    created_at = Column(DateTime(timezone=True), server_default=func.now())


# =============================================================================
# Projekt-modeller
# =============================================================================

class Project(Base):
    """Utvecklingsprojekt som kan kopplas till idéer och behov"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.PROPOSED)
    project_type = Column(Enum(ProjectType), nullable=False)

    # Tidsramar
    planned_start = Column(Date)
    planned_end = Column(Date)
    actual_start = Column(Date)
    actual_end = Column(Date)

    # Budget och resurser
    estimated_budget = Column(Float)
    funding_source = Column(String)  # "intern", "vinnova", "eu_horizon", etc.

    # Organisation
    owner_department = Column(String)
    contact_email = Column(String)
    project_manager = Column(String)

    # AI-analys
    ai_summary = Column(Text)
    ai_strategic_alignment = Column(Float)  # 0-1 score för strategisk koppling

    # RAG-indexering
    rag_indexed = Column(Boolean, default=False)

    # Relationer
    ideas = relationship("Idea", secondary="project_ideas", back_populates="projects")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ProjectIdea(Base):
    """Koppling mellan projekt och idéer (many-to-many)"""
    __tablename__ = "project_ideas"

    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    idea_id = Column(Integer, ForeignKey("ideas.id", ondelete="CASCADE"), primary_key=True)
    relationship_type = Column(String, default="implements")  # implements, extends, inspires
    notes = Column(Text)  # Fritext för att beskriva kopplingen

    created_at = Column(DateTime(timezone=True), server_default=func.now())


# =============================================================================
# Strategi-relaterade Enums
# =============================================================================

class StrategyDocumentType(enum.Enum):
    """Typ av strategidokument"""
    STRATSYS_GOAL = "stratsys_mål"
    POLICY = "policy"
    GUIDELINE = "riktlinje"
    VISION = "vision"
    ACTION_PLAN = "handlingsplan"
    BUDGET_GOAL = "budgetmål"


class StrategyLevel(enum.Enum):
    """Hierarkisk nivå i strategin"""
    STRATEGIC = 1  # Övergripande strategiskt mål
    TACTICAL = 2   # Delmål/taktiskt mål
    OPERATIONAL = 3  # Aktivitet/operativt mål


class AlignmentEntityType(enum.Enum):
    """Typ av entitet som kan alignas med strategi"""
    IDEA = "idea"
    PROJECT = "project"


# =============================================================================
# Strategi-modeller
# =============================================================================

class StrategyDocument(Base):
    """Strategidokument från Stratsys, policies och riktlinjer"""
    __tablename__ = "strategy_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    document_type = Column(Enum(StrategyDocumentType), nullable=False)

    # Källa och extern referens
    source = Column(String)  # "stratsys", "manual", "sharepoint"
    external_id = Column(String)  # Stratsys ID eller annan extern referens
    external_url = Column(String)  # Länk till originaldokument

    # Innehåll
    content = Column(Text)  # Fulltext-innehåll
    summary = Column(Text)  # AI-genererad sammanfattning
    keywords = Column(JSON)  # Extraherade nyckelord

    # Hierarki
    parent_id = Column(Integer, ForeignKey("strategy_documents.id"))
    level = Column(Integer, default=1)  # 1=strategiskt, 2=delmål, 3=aktivitet
    sort_order = Column(Integer, default=0)  # För sortering inom samma nivå

    # Organisation
    responsible_department = Column(String)
    responsible_person = Column(String)

    # Tidsperiod
    time_period = Column(String)  # "2024-2027", "Q1 2025"
    valid_from = Column(Date)
    valid_to = Column(Date)

    # Status
    is_active = Column(Boolean, default=True)

    # RAG-indexering
    rag_indexed = Column(Boolean, default=False)

    # Relationer
    parent = relationship("StrategyDocument", remote_side=[id], backref="children")
    alignments = relationship("StrategicAlignment", back_populates="strategy_document", cascade="all, delete-orphan")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class StrategicAlignment(Base):
    """Koppling mellan idéer/projekt och strategiska mål"""
    __tablename__ = "strategic_alignments"

    id = Column(Integer, primary_key=True, index=True)

    # Entitet som alignas (idé eller projekt)
    entity_type = Column(Enum(AlignmentEntityType), nullable=False)
    entity_id = Column(Integer, nullable=False)

    # Strategidokument som alignas mot
    strategy_document_id = Column(Integer, ForeignKey("strategy_documents.id", ondelete="CASCADE"), nullable=False)

    # Alignment-bedömning
    alignment_score = Column(Float)  # 0-1 score för hur väl entiteten alignar
    alignment_reasoning = Column(Text)  # AI-genererad motivering

    # Verifiering
    verified_by_human = Column(Boolean, default=False)
    verified_by = Column(String)  # Namn på person som verifierat
    verified_at = Column(DateTime(timezone=True))

    # Relationer
    strategy_document = relationship("StrategyDocument", back_populates="alignments")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# =============================================================================
# Finansierings-enums (Fas 3)
# =============================================================================

class FundingCallStatus(enum.Enum):
    """Status för finansieringsutlysning"""
    UPCOMING = "kommande"
    OPEN = "öppen"
    CLOSING_SOON = "stänger_snart"
    CLOSED = "stängd"


class FundingSource(enum.Enum):
    """Källa för finansieringsutlysning"""
    VINNOVA = "vinnova"
    EU_HORIZON = "eu_horizon"
    EU_DIGITAL = "eu_digital"
    REGIONAL = "regional"
    OTHER = "other"


# =============================================================================
# Finansierings-modeller (Fas 3)
# =============================================================================

class FundingCall(Base):
    """Finansieringsutlysning från Vinnova, EU, etc."""
    __tablename__ = "funding_calls"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    source = Column(Enum(FundingSource), nullable=False)
    status = Column(Enum(FundingCallStatus), default=FundingCallStatus.UPCOMING)

    # Externa referenser
    external_id = Column(String)  # ID hos Vinnova/EU
    external_url = Column(String)  # Länk till utlysningen

    # Datum
    open_date = Column(Date)  # När utlysningen öppnar
    deadline = Column(Date)  # Sista ansökningsdag
    decision_date = Column(Date)  # Förväntad beslutsdatum

    # Budget
    total_budget = Column(Float)  # Total budget för utlysningen
    min_grant = Column(Float)  # Minsta bidrag
    max_grant = Column(Float)  # Största bidrag
    co_funding_requirement = Column(Float)  # Procent medfinansiering (0-100)

    # Metadata (JSON)
    eligible_applicants = Column(JSON)  # ["kommun", "region", "företag", "universitet"]
    focus_areas = Column(JSON)  # ["digitalisering", "hållbarhet", "AI"]
    keywords = Column(JSON)  # Extraherade nyckelord

    # AI-genererat
    requirements_summary = Column(Text)  # AI-sammanfattning av krav

    # RAG-indexering
    rag_indexed = Column(Boolean, default=False)

    # Relationer
    matches = relationship("FundingMatch", back_populates="funding_call", cascade="all, delete-orphan")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class FundingMatch(Base):
    """Matchning mellan idé/projekt och finansieringsutlysning"""
    __tablename__ = "funding_matches"

    id = Column(Integer, primary_key=True, index=True)

    # Koppling till utlysning
    funding_call_id = Column(Integer, ForeignKey("funding_calls.id", ondelete="CASCADE"), nullable=False)

    # Polymorf relation (idé eller projekt) - återanvänder AlignmentEntityType
    entity_type = Column(Enum(AlignmentEntityType), nullable=False)
    entity_id = Column(Integer, nullable=False)

    # Matchning
    match_score = Column(Float)  # 0-1 score för matchning
    match_reasoning = Column(Text)  # AI-genererad motivering
    strengths = Column(JSON)  # ["Stark digital fokus", "Rätt målgrupp"]
    gaps = Column(JSON)  # ["Saknar medfinansiering", "Tidplan för kort"]

    # Status och användarfeedback
    is_recommended = Column(Boolean, default=False)  # AI-rekommenderad
    user_rating = Column(Integer)  # 1-5 stjärnor från användare

    # Relationer
    funding_call = relationship("FundingCall", back_populates="matches")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())