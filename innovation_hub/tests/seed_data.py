from sqlalchemy.orm import Session
from ..database import get_db, User, Category, Idea, Tag, Comment, IdeaTag
from ..database import IdeaType, IdeaStatus, Priority, TargetGroup

def create_seed_data(db: Session):
    """Create realistic Swedish innovation hub test data"""

    # Create users (Swedish names and organizations)
    users = [
        User(name="Anna Andersson", email="anna.andersson@kommun.se", department="IT-avdelningen"),
        User(name="Erik Nilsson", email="erik.nilsson@kommun.se", department="Medborgarservice"),
        User(name="Maria Johansson", email="maria.johansson@kommun.se", department="Miljö och hållbarhet"),
        User(name="Lars Petersson", email="lars.petersson@kommun.se", department="Ekonomi"),
        User(name="Ingrid Svensson", email="ingrid.svensson@kommun.se", department="Personal och organisation"),
    ]

    for user in users:
        db.add(user)
    db.commit()

    # Create categories (Swedish public sector)
    categories = [
        Category(name="Digital transformation", description="Digitalisering av tjänster och processer", color="#3498db"),
        Category(name="Medborgarservice", description="Förbättring av service till medborgare", color="#e74c3c"),
        Category(name="Miljö och klimat", description="Hållbarhet och miljöinitiativ", color="#27ae60"),
        Category(name="Processer och effektivitet", description="Förbättring av interna processer", color="#f39c12"),
        Category(name="Innovation och utveckling", description="Nya idéer och lösningar", color="#9b59b6"),
    ]

    for category in categories:
        db.add(category)
    db.commit()

    # Create tags (Swedish context)
    tag_names = [
        "digitalisering", "ai", "automation", "användarupplevelse", "tillgänglighet",
        "miljö", "hållbarhet", "effektivitet", "kostnadsbesparingar", "innovation",
        "medborgarfokus", "öppna data", "säkerhet", "integritet", "mobilapp"
    ]

    tags = []
    for tag_name in tag_names:
        tag = Tag(name=tag_name)
        db.add(tag)
        tags.append(tag)
    db.commit()

    # Create realistic ideas (Swedish public sector context)
    ideas_data = [
        {
            "title": "AI-chatbot för medborgartjänster",
            "description": "Utveckla en intelligent chatbot som kan svara på vanliga frågor från medborgare dygnet runt. Skulle minska belastningen på kundtjänst och ge snabbare svar på enkla frågor som öppettider, kontaktuppgifter och enkla ärenden.",
            "type": IdeaType.IDEA,
            "status": IdeaStatus.NEW,
            "priority": Priority.HIGH,
            "target_group": TargetGroup.CITIZENS,
            "submitter_id": 1,
            "category_id": 1,
            "tag_names": ["ai", "digitalisering", "medborgarfokus"]
        },
        {
            "title": "Mobil app för ärendehantering",
            "description": "En mobilapp där medborgare kan lämna in ärenden, följa status och kommunicera med handläggare. Skulle göra det enklare för medborgare att interagera med kommunen och minska administration.",
            "type": IdeaType.IDEA,
            "status": IdeaStatus.REVIEWING,
            "priority": Priority.HIGH,
            "target_group": TargetGroup.CITIZENS,
            "submitter_id": 2,
            "category_id": 2,
            "tag_names": ["mobilapp", "digitalisering", "användarupplevelse"]
        },
        {
            "title": "Automatiserad fakturahantering",
            "description": "Implementera AI-baserad fakturahantering som automatiskt läser, kategoriserar och föreslår godkännanden. Skulle spara betydande tid för ekonomiavdelningen och minska risken för fel.",
            "type": IdeaType.IMPROVEMENT,
            "status": IdeaStatus.APPROVED,
            "priority": Priority.MEDIUM,
            "target_group": TargetGroup.EMPLOYEES,
            "submitter_id": 4,
            "category_id": 4,
            "tag_names": ["automation", "ai", "effektivitet", "kostnadsbesparingar"]
        },
        {
            "title": "Problem med långsam handläggningstid",
            "description": "Många ärenden tar för lång tid att handlägga på grund av manuella processer och dålig systemintegration. Medborgare klagar på långa väntetider och oklara statusuppdateringar.",
            "type": IdeaType.PROBLEM,
            "status": IdeaStatus.NEW,
            "priority": Priority.HIGH,
            "target_group": TargetGroup.CITIZENS,
            "submitter_id": 2,
            "category_id": 4,
            "tag_names": ["effektivitet", "processer"]
        },
        {
            "title": "Behov av bättre tillgänglighet på webben",
            "description": "Vår webbplats uppfyller inte WCAG-standarderna fullt ut. Vi behöver förbättra tillgängligheten för personer med funktionsnedsättningar, särskilt för screenreader-användare.",
            "type": IdeaType.NEED,
            "status": IdeaStatus.IN_DEVELOPMENT,
            "priority": Priority.HIGH,
            "target_group": TargetGroup.CITIZENS,
            "submitter_id": 1,
            "category_id": 1,
            "tag_names": ["tillgänglighet", "webb", "inkludering"]
        },
        {
            "title": "Grön IT-initiative",
            "description": "Föreslår att vi implementerar en grön IT-strategi för att minska vårt miljöavtryck. Detta inkluderar energieffektiva servrar, molnlösningar och minskning av pappersförbrukning genom digitalisering.",
            "type": IdeaType.IDEA,
            "status": IdeaStatus.NEW,
            "priority": Priority.MEDIUM,
            "target_group": TargetGroup.OTHER_ORGS,
            "submitter_id": 3,
            "category_id": 3,
            "tag_names": ["miljö", "hållbarhet", "digitalisering"]
        },
        {
            "title": "Öppna data-portal",
            "description": "Skapa en portal där kommunens data görs tillgänglig för allmänheten i öppna format. Detta skulle öka transparensen och möjliggöra för utvecklare att skapa innovativa tjänster.",
            "type": IdeaType.IDEA,
            "status": IdeaStatus.IMPLEMENTED,
            "priority": Priority.MEDIUM,
            "target_group": TargetGroup.BUSINESSES,
            "submitter_id": 1,
            "category_id": 5,
            "tag_names": ["öppna data", "transparens", "innovation"]
        },
        {
            "title": "Digital signering av dokument",
            "description": "Implementera BankID-baserad digital signering för att minska behovet av fysiska möten och pappershantering. Skulle särskilt hjälpa under pandemier eller för personer med mobilitetshinder.",
            "type": IdeaType.IMPROVEMENT,
            "status": IdeaStatus.NEW,
            "priority": Priority.MEDIUM,
            "target_group": TargetGroup.CITIZENS,
            "submitter_id": 5,
            "category_id": 1,
            "tag_names": ["digitalisering", "säkerhet", "tillgänglighet"]
        }
    ]

    # Create ideas with tags
    for idea_data in ideas_data:
        tag_names = idea_data.pop("tag_names")
        idea = Idea(**idea_data)
        db.add(idea)
        db.flush()  # Get the ID

        # Add tags
        for tag_name in tag_names:
            tag = next((t for t in tags if t.name == tag_name), None)
            if tag:
                idea_tag = IdeaTag(idea_id=idea.id, tag_id=tag.id)
                db.add(idea_tag)

    db.commit()

    # Create some comments
    comments_data = [
        {
            "content": "Utmärkt idé! Vi borde också integrera detta med vårt befintliga ärendehanteringssystem.",
            "idea_id": 1,
            "author_id": 2
        },
        {
            "content": "Har ni undersökt kostnaderna för detta? Vi behöver en budget innan vi kan gå vidare.",
            "idea_id": 1,
            "author_id": 4
        },
        {
            "content": "Vi har redan börjat arbeta med detta. Kommer att ha en första version klar inom 3 månader.",
            "idea_id": 5,
            "author_id": 1
        },
        {
            "content": "Detta är verkligen ett problem som påverkar många medborgare. Prioritet att lösa!",
            "idea_id": 4,
            "author_id": 3
        }
    ]

    for comment_data in comments_data:
        comment = Comment(**comment_data)
        db.add(comment)

    db.commit()
    print("✅ Test data created successfully!")

def reset_database(db: Session):
    """Reset database by deleting all data"""
    # Delete in correct order due to foreign keys
    db.query(Comment).delete()
    db.query(IdeaTag).delete()
    db.query(Idea).delete()
    db.query(Tag).delete()
    db.query(Category).delete()
    db.query(User).delete()
    db.commit()
    print("🗑️ Database reset successfully!")