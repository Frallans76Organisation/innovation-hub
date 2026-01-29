from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, date
from typing import List, Optional
from enum import Enum


# =============================================================================
# Projekt-relaterade Enums
# =============================================================================

class ProjectStatusEnum(str, Enum):
    PROPOSED = "föreslagen"
    PLANNING = "planering"
    IN_PROGRESS = "pågående"
    ON_HOLD = "pausad"
    COMPLETED = "avslutad"
    CANCELLED = "avbruten"


class ProjectTypeEnum(str, Enum):
    INTERNAL = "intern_utveckling"
    VINNOVA = "vinnova"
    EU_FUNDED = "eu_finansierad"
    EXTERNAL_COLLAB = "externt_samarbete"
    MAINTENANCE = "förvaltning"


class RelationshipTypeEnum(str, Enum):
    IMPLEMENTS = "implements"
    EXTENDS = "extends"
    INSPIRES = "inspires"


# =============================================================================
# Idé-relaterade Enums
# =============================================================================

class IdeaTypeEnum(str, Enum):
    IDEA = "idé"
    PROBLEM = "problem"
    NEED = "behov"
    IMPROVEMENT = "förbättring"

class IdeaStatusEnum(str, Enum):
    NEW = "ny"
    REVIEWING = "granskning"
    APPROVED = "godkänd"
    IN_DEVELOPMENT = "utveckling"
    IMPLEMENTED = "implementerad"
    REJECTED = "avvisad"

class PriorityEnum(str, Enum):
    LOW = "låg"
    MEDIUM = "medel"
    HIGH = "hög"

class TargetGroupEnum(str, Enum):
    CITIZENS = "medborgare"
    BUSINESSES = "företag"
    EMPLOYEES = "medarbetare"
    OTHER_ORGS = "andra organisationer"

# Base schemas
class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    department: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = None
    color: str = Field(default="#3498db", pattern=r"^#[0-9a-fA-F]{6}$")

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class TagBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=30)

class TagCreate(TagBase):
    pass

class TagResponse(TagBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class IdeaBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    type: IdeaTypeEnum
    target_group: TargetGroupEnum

class IdeaCreate(IdeaBase):
    submitter_email: str = Field(..., description="Email of the person submitting the idea")
    tags: List[str] = Field(default=[], description="List of tag names")

class IdeaUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=5000)
    type: Optional[IdeaTypeEnum] = None
    status: Optional[IdeaStatusEnum] = None
    priority: Optional[PriorityEnum] = None
    target_group: Optional[TargetGroupEnum] = None
    category_id: Optional[int] = None
    tags: Optional[List[str]] = None

class IdeaResponse(IdeaBase):
    id: int
    status: IdeaStatusEnum
    priority: PriorityEnum
    submitter: UserResponse
    category: Optional[CategoryResponse] = None
    tags: List[TagResponse] = []
    comments: List['CommentResponse'] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Engagement metrics
    vote_count: int = 0

    # AI Analysis results (optional for transparency)
    ai_sentiment: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_analysis_notes: Optional[str] = None
    service_recommendation: Optional[str] = None
    service_confidence: Optional[float] = None
    service_reasoning: Optional[str] = None
    matching_services: Optional[List[dict]] = None
    development_impact: Optional[str] = None

    class Config:
        from_attributes = True

class CommentBase(BaseModel):
    content: str = Field(..., min_length=3, max_length=1000)

class CommentCreate(CommentBase):
    author_id: int = Field(..., description="ID of the comment author")

class CommentResponse(CommentBase):
    id: int
    author: UserResponse
    created_at: datetime

    class Config:
        from_attributes = True

# Statistics schemas
class StatusCount(BaseModel):
    status: IdeaStatusEnum
    count: int

class TypeCount(BaseModel):
    type: IdeaTypeEnum
    count: int

class IdeaStats(BaseModel):
    total_ideas: int
    status_distribution: List[StatusCount]
    type_distribution: List[TypeCount]
    recent_ideas: List[IdeaResponse]

# Filter schemas
class IdeaFilter(BaseModel):
    status: Optional[IdeaStatusEnum] = None
    type: Optional[IdeaTypeEnum] = None
    priority: Optional[PriorityEnum] = None
    target_group: Optional[TargetGroupEnum] = None
    category_id: Optional[int] = None
    submitter_id: Optional[int] = None
    tag: Optional[str] = None
    search: Optional[str] = Field(None, description="Search in title and description")

class PaginationParams(BaseModel):
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)

# Analysis schemas
class ServiceMappingOverview(BaseModel):
    """Overview of how ideas map to existing services"""
    existing_service_count: int = Field(..., description="Ideas that can use existing services")
    develop_existing_count: int = Field(..., description="Ideas requiring development of existing services")
    new_service_count: int = Field(..., description="Ideas requiring completely new services")
    total_ideas_analyzed: int

class ServiceMatch(BaseModel):
    """Service that matches ideas"""
    service_name: str
    service_category: Optional[str]
    idea_count: int
    avg_match_score: float
    ideas: List[dict] = Field(default=[])

class DevelopmentNeed(BaseModel):
    """Idea with its development needs"""
    idea_id: int
    title: str
    priority: PriorityEnum
    service_recommendation: str  # existing_service, develop_existing, new_service
    match_score: float
    impact: str  # low, medium, high

class GapAnalysis(BaseModel):
    """Areas with many ideas but no matching services"""
    area_keywords: List[str]
    idea_count: int
    sample_ideas: List[dict]

class AnalysisStats(BaseModel):
    """Complete analysis statistics"""
    overview: ServiceMappingOverview
    top_matched_services: List[ServiceMatch]
    development_needs: List[DevelopmentNeed]
    gaps: List[GapAnalysis]
    ai_confidence_avg: float


# =============================================================================
# Projekt-schemas
# =============================================================================

class ProjectBase(BaseModel):
    """Bas-schema för projekt"""
    name: str = Field(..., min_length=3, max_length=200, description="Projektnamn")
    description: str = Field(..., min_length=10, max_length=5000, description="Projektbeskrivning")
    project_type: ProjectTypeEnum = Field(..., description="Typ av projekt")
    planned_start: Optional[date] = Field(None, description="Planerat startdatum")
    planned_end: Optional[date] = Field(None, description="Planerat slutdatum")
    estimated_budget: Optional[float] = Field(None, ge=0, description="Uppskattad budget i SEK")
    funding_source: Optional[str] = Field(None, max_length=100, description="Finansieringskälla")
    owner_department: Optional[str] = Field(None, max_length=100, description="Ansvarig avdelning")
    contact_email: Optional[EmailStr] = Field(None, description="Kontaktperson e-post")
    project_manager: Optional[str] = Field(None, max_length=100, description="Projektledare")


class ProjectCreate(ProjectBase):
    """Schema för att skapa nytt projekt"""
    idea_ids: List[int] = Field(default=[], description="ID:n för idéer att koppla till projektet")


class ProjectUpdate(BaseModel):
    """Schema för att uppdatera projekt"""
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=5000)
    status: Optional[ProjectStatusEnum] = None
    project_type: Optional[ProjectTypeEnum] = None
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    estimated_budget: Optional[float] = Field(None, ge=0)
    funding_source: Optional[str] = Field(None, max_length=100)
    owner_department: Optional[str] = Field(None, max_length=100)
    contact_email: Optional[EmailStr] = None
    project_manager: Optional[str] = Field(None, max_length=100)


class ProjectIdeaLink(BaseModel):
    """Schema för att koppla idé till projekt"""
    idea_id: int
    relationship_type: RelationshipTypeEnum = Field(
        default=RelationshipTypeEnum.IMPLEMENTS,
        description="Typ av koppling mellan projekt och idé"
    )
    notes: Optional[str] = Field(None, max_length=500, description="Beskrivning av kopplingen")


class ProjectIdeaResponse(BaseModel):
    """Schema för koppling mellan projekt och idé"""
    idea_id: int
    idea_title: str
    relationship_type: str
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectResponse(ProjectBase):
    """Schema för projektrespons"""
    id: int
    status: ProjectStatusEnum
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    ai_summary: Optional[str] = None
    ai_strategic_alignment: Optional[float] = None
    rag_indexed: bool = False
    linked_ideas_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProjectDetailResponse(ProjectResponse):
    """Detaljerat projektresponse med kopplingar"""
    linked_ideas: List[ProjectIdeaResponse] = []


class ProjectFilter(BaseModel):
    """Filter för projektlistning"""
    status: Optional[ProjectStatusEnum] = None
    project_type: Optional[ProjectTypeEnum] = None
    owner_department: Optional[str] = None
    funding_source: Optional[str] = None
    search: Optional[str] = Field(None, description="Sök i namn och beskrivning")


class ProjectStats(BaseModel):
    """Statistik för projekt"""
    total_projects: int
    by_status: dict
    by_type: dict
    total_budget: float
    ideas_linked: int


# =============================================================================
# Strategi-relaterade Enums
# =============================================================================

class StrategyDocumentTypeEnum(str, Enum):
    """Typ av strategidokument"""
    STRATSYS_GOAL = "stratsys_mål"
    POLICY = "policy"
    GUIDELINE = "riktlinje"
    VISION = "vision"
    ACTION_PLAN = "handlingsplan"
    BUDGET_GOAL = "budgetmål"


class StrategyLevelEnum(int, Enum):
    """Hierarkisk nivå i strategin"""
    STRATEGIC = 1  # Övergripande strategiskt mål
    TACTICAL = 2   # Delmål/taktiskt mål
    OPERATIONAL = 3  # Aktivitet/operativt mål


class AlignmentEntityTypeEnum(str, Enum):
    """Typ av entitet som kan alignas med strategi"""
    IDEA = "idea"
    PROJECT = "project"


# =============================================================================
# Strategi-schemas
# =============================================================================

class StrategyDocumentBase(BaseModel):
    """Bas-schema för strategidokument"""
    title: str = Field(..., min_length=3, max_length=300, description="Titel på strategidokumentet")
    description: Optional[str] = Field(None, max_length=2000, description="Beskrivning av målet/dokumentet")
    document_type: StrategyDocumentTypeEnum = Field(..., description="Typ av strategidokument")

    # Källa och extern referens
    source: Optional[str] = Field(None, max_length=100, description="Källa (stratsys, manual, sharepoint)")
    external_id: Optional[str] = Field(None, max_length=100, description="Externt ID (t.ex. Stratsys-ID)")
    external_url: Optional[str] = Field(None, max_length=500, description="URL till originaldokument")

    # Innehåll
    content: Optional[str] = Field(None, description="Fulltext-innehåll")

    # Hierarki
    parent_id: Optional[int] = Field(None, description="ID för överordnat mål/dokument")
    level: int = Field(default=1, ge=1, le=3, description="Hierarkisk nivå (1=strategiskt, 2=delmål, 3=aktivitet)")
    sort_order: int = Field(default=0, ge=0, description="Sorteringsordning")

    # Organisation
    responsible_department: Optional[str] = Field(None, max_length=100, description="Ansvarig avdelning")
    responsible_person: Optional[str] = Field(None, max_length=100, description="Ansvarig person")

    # Tidsperiod
    time_period: Optional[str] = Field(None, max_length=50, description="Tidsperiod (t.ex. '2024-2027')")
    valid_from: Optional[date] = Field(None, description="Giltig från")
    valid_to: Optional[date] = Field(None, description="Giltig till")


class StrategyDocumentCreate(StrategyDocumentBase):
    """Schema för att skapa nytt strategidokument"""
    keywords: List[str] = Field(default=[], description="Nyckelord för sökning")


class StrategyDocumentUpdate(BaseModel):
    """Schema för att uppdatera strategidokument"""
    title: Optional[str] = Field(None, min_length=3, max_length=300)
    description: Optional[str] = Field(None, max_length=2000)
    document_type: Optional[StrategyDocumentTypeEnum] = None
    source: Optional[str] = Field(None, max_length=100)
    external_id: Optional[str] = Field(None, max_length=100)
    external_url: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = None
    parent_id: Optional[int] = None
    level: Optional[int] = Field(None, ge=1, le=3)
    sort_order: Optional[int] = Field(None, ge=0)
    responsible_department: Optional[str] = Field(None, max_length=100)
    responsible_person: Optional[str] = Field(None, max_length=100)
    time_period: Optional[str] = Field(None, max_length=50)
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    is_active: Optional[bool] = None
    keywords: Optional[List[str]] = None


class StrategyDocumentResponse(StrategyDocumentBase):
    """Schema för strategidokument-respons"""
    id: int
    summary: Optional[str] = None  # AI-genererad sammanfattning
    keywords: Optional[List[str]] = None
    is_active: bool = True
    rag_indexed: bool = False
    alignment_count: int = 0  # Antal idéer/projekt som alignar med detta mål
    children_count: int = 0  # Antal undermål
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StrategyDocumentDetailResponse(StrategyDocumentResponse):
    """Detaljerad strategidokument-respons med children"""
    children: List['StrategyDocumentResponse'] = []
    alignments: List['StrategicAlignmentResponse'] = []


class StrategyTreeNode(BaseModel):
    """Nod i strategiträd för hierarkisk visning"""
    id: int
    title: str
    level: int
    document_type: StrategyDocumentTypeEnum
    is_active: bool
    alignment_count: int = 0
    children: List['StrategyTreeNode'] = []

    class Config:
        from_attributes = True


# =============================================================================
# Strategic Alignment schemas
# =============================================================================

class StrategicAlignmentBase(BaseModel):
    """Bas-schema för strategisk alignment"""
    entity_type: AlignmentEntityTypeEnum = Field(..., description="Typ av entitet (idea/project)")
    entity_id: int = Field(..., description="ID för idén eller projektet")
    strategy_document_id: int = Field(..., description="ID för strategidokumentet")


class StrategicAlignmentCreate(StrategicAlignmentBase):
    """Schema för att skapa alignment"""
    alignment_score: Optional[float] = Field(None, ge=0, le=1, description="Alignment-poäng (0-1)")
    alignment_reasoning: Optional[str] = Field(None, max_length=2000, description="Motivering för alignment")


class StrategicAlignmentUpdate(BaseModel):
    """Schema för att uppdatera alignment"""
    alignment_score: Optional[float] = Field(None, ge=0, le=1)
    alignment_reasoning: Optional[str] = Field(None, max_length=2000)
    verified_by_human: Optional[bool] = None
    verified_by: Optional[str] = Field(None, max_length=100)


class StrategicAlignmentResponse(StrategicAlignmentBase):
    """Schema för alignment-respons"""
    id: int
    alignment_score: Optional[float] = None
    alignment_reasoning: Optional[str] = None
    verified_by_human: bool = False
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Inkludera strategidokument-info för enkel visning
    strategy_title: Optional[str] = None
    strategy_level: Optional[int] = None

    class Config:
        from_attributes = True


class StrategicAlignmentWithEntity(StrategicAlignmentResponse):
    """Alignment med entitetsdetaljer"""
    entity_title: str  # Titel på idé eller projekt
    entity_status: str  # Status på idé eller projekt


# =============================================================================
# Strategy Analysis schemas
# =============================================================================

class StrategyAlignmentAnalysis(BaseModel):
    """Resultat av AI-analys för strategisk alignment"""
    strategy_document_id: int
    strategy_title: str
    alignment_score: float = Field(..., ge=0, le=1)
    alignment_reasoning: str
    key_matches: List[str] = Field(default=[], description="Nyckelord som matchar")
    confidence: float = Field(..., ge=0, le=1)


class EntityAlignmentResult(BaseModel):
    """Alignment-resultat för en entitet"""
    entity_type: AlignmentEntityTypeEnum
    entity_id: int
    entity_title: str
    alignments: List[StrategyAlignmentAnalysis]
    overall_alignment_score: float = Field(..., ge=0, le=1)
    top_aligned_goals: List[str]


class StrategyStats(BaseModel):
    """Statistik för strategidokument"""
    total_documents: int
    by_type: dict
    by_level: dict
    active_count: int
    total_alignments: int
    avg_alignment_score: float
    ideas_aligned: int
    projects_aligned: int


class StrategyCoverageReport(BaseModel):
    """Rapport över strategitäckning"""
    total_goals: int
    goals_with_alignments: int
    coverage_percentage: float
    uncovered_goals: List[dict]  # Mål utan kopplingar
    most_aligned_goals: List[dict]  # Mål med flest kopplingar


class StrategyFilter(BaseModel):
    """Filter för strategidokument"""
    document_type: Optional[StrategyDocumentTypeEnum] = None
    level: Optional[int] = Field(None, ge=1, le=3)
    responsible_department: Optional[str] = None
    is_active: Optional[bool] = None
    parent_id: Optional[int] = None
    search: Optional[str] = Field(None, description="Sök i titel och beskrivning")


# =============================================================================
# Finansierings-relaterade Enums (Fas 3)
# =============================================================================

class FundingCallStatusEnum(str, Enum):
    """Status för finansieringsutlysning"""
    UPCOMING = "kommande"
    OPEN = "öppen"
    CLOSING_SOON = "stänger_snart"
    CLOSED = "stängd"


class FundingSourceEnum(str, Enum):
    """Källa för finansieringsutlysning"""
    VINNOVA = "vinnova"
    EU_HORIZON = "eu_horizon"
    EU_DIGITAL = "eu_digital"
    REGIONAL = "regional"
    OTHER = "other"


# =============================================================================
# Finansierings-schemas (Fas 3)
# =============================================================================

class FundingCallBase(BaseModel):
    """Basschema för finansieringsutlysning"""
    title: str = Field(..., min_length=3, max_length=300)
    description: Optional[str] = Field(None, max_length=5000)
    source: FundingSourceEnum
    external_id: Optional[str] = None
    external_url: Optional[str] = None
    open_date: Optional[date] = None
    deadline: Optional[date] = None
    decision_date: Optional[date] = None
    total_budget: Optional[float] = Field(None, ge=0)
    min_grant: Optional[float] = Field(None, ge=0)
    max_grant: Optional[float] = Field(None, ge=0)
    co_funding_requirement: Optional[float] = Field(None, ge=0, le=100, description="Procent medfinansiering")
    eligible_applicants: List[str] = Field(default=[], description="Berättigade sökande")
    focus_areas: List[str] = Field(default=[], description="Fokusområden")
    requirements_summary: Optional[str] = None


class FundingCallCreate(FundingCallBase):
    """Schema för att skapa finansieringsutlysning"""
    keywords: List[str] = Field(default=[], description="Nyckelord för sökning")
    status: Optional[FundingCallStatusEnum] = FundingCallStatusEnum.UPCOMING


class FundingCallUpdate(BaseModel):
    """Schema för att uppdatera finansieringsutlysning"""
    title: Optional[str] = Field(None, min_length=3, max_length=300)
    description: Optional[str] = Field(None, max_length=5000)
    source: Optional[FundingSourceEnum] = None
    status: Optional[FundingCallStatusEnum] = None
    external_id: Optional[str] = None
    external_url: Optional[str] = None
    open_date: Optional[date] = None
    deadline: Optional[date] = None
    decision_date: Optional[date] = None
    total_budget: Optional[float] = Field(None, ge=0)
    min_grant: Optional[float] = Field(None, ge=0)
    max_grant: Optional[float] = Field(None, ge=0)
    co_funding_requirement: Optional[float] = Field(None, ge=0, le=100)
    eligible_applicants: Optional[List[str]] = None
    focus_areas: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    requirements_summary: Optional[str] = None


class FundingCallResponse(FundingCallBase):
    """Schema för svar med finansieringsutlysning"""
    id: int
    status: FundingCallStatusEnum
    keywords: List[str] = []
    rag_indexed: bool = False
    match_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FundingCallDetailResponse(FundingCallResponse):
    """Detaljerat svar med matchningar"""
    matches: List['FundingMatchResponse'] = []


# FundingMatch schemas
class FundingMatchBase(BaseModel):
    """Basschema för finansieringsmatchning"""
    entity_type: AlignmentEntityTypeEnum
    entity_id: int
    funding_call_id: int


class FundingMatchCreate(FundingMatchBase):
    """Schema för att skapa finansieringsmatchning"""
    match_score: Optional[float] = Field(None, ge=0, le=1)
    match_reasoning: Optional[str] = None
    strengths: List[str] = []
    gaps: List[str] = []
    is_recommended: bool = False


class FundingMatchUpdate(BaseModel):
    """Schema för att uppdatera finansieringsmatchning"""
    match_score: Optional[float] = Field(None, ge=0, le=1)
    match_reasoning: Optional[str] = None
    strengths: Optional[List[str]] = None
    gaps: Optional[List[str]] = None
    is_recommended: Optional[bool] = None
    user_rating: Optional[int] = Field(None, ge=1, le=5)


class FundingMatchResponse(FundingMatchBase):
    """Schema för svar med finansieringsmatchning"""
    id: int
    match_score: Optional[float] = None
    match_reasoning: Optional[str] = None
    strengths: List[str] = []
    gaps: List[str] = []
    is_recommended: bool = False
    user_rating: Optional[int] = None
    funding_title: Optional[str] = None
    entity_title: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Filter och statistik
class FundingFilter(BaseModel):
    """Filter för finansieringsutlysningar"""
    source: Optional[FundingSourceEnum] = None
    status: Optional[FundingCallStatusEnum] = None
    search: Optional[str] = Field(None, description="Sök i titel och beskrivning")
    has_deadline_within_days: Optional[int] = Field(None, ge=1, description="Deadline inom X dagar")


class FundingStats(BaseModel):
    """Statistik för finansieringsutlysningar"""
    total_calls: int
    open_calls: int
    upcoming_calls: int
    closed_calls: int
    total_budget_available: float
    by_source: dict
    upcoming_deadlines: List[dict]


# =============================================================================
# Rebuild models för att lösa forward references
# =============================================================================

# Uppdatera forward references för modeller som refererar till andra modeller
StrategyDocumentDetailResponse.model_rebuild()
StrategyTreeNode.model_rebuild()
IdeaResponse.model_rebuild()
FundingCallDetailResponse.model_rebuild()