"""
CRUD operations for analysis and statistics
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict
from collections import defaultdict, Counter

from ..database import Idea, IdeaStatus, Priority
from ..models import (
    ServiceMappingOverview, ServiceMatch, DevelopmentNeed,
    GapAnalysis, AnalysisStats, PriorityEnum
)

class AnalysisCRUD:
    @staticmethod
    def get_analysis_stats(db: Session) -> AnalysisStats:
        """Get comprehensive analysis statistics"""

        # Get all ideas
        all_ideas = db.query(Idea).all()

        # Calculate service mapping overview
        overview = AnalysisCRUD._get_service_mapping_overview(all_ideas)

        # Get top matched services
        top_services = AnalysisCRUD._get_top_matched_services(all_ideas)

        # Get development needs
        dev_needs = AnalysisCRUD._get_development_needs(all_ideas)

        # Get gap analysis
        gaps = AnalysisCRUD._get_gap_analysis(all_ideas)

        # Calculate average AI confidence
        confidences = [idea.ai_confidence for idea in all_ideas if idea.ai_confidence]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return AnalysisStats(
            overview=overview,
            top_matched_services=top_services,
            development_needs=dev_needs,
            gaps=gaps,
            ai_confidence_avg=avg_confidence
        )

    @staticmethod
    def _get_service_mapping_overview(ideas: List[Idea]) -> ServiceMappingOverview:
        """Calculate service mapping overview statistics"""
        existing_count = 0
        develop_count = 0
        new_count = 0
        analyzed_count = 0

        for idea in ideas:
            if idea.service_recommendation:
                analyzed_count += 1
                if idea.service_recommendation == "existing_service":
                    existing_count += 1
                elif idea.service_recommendation == "develop_existing":
                    develop_count += 1
                elif idea.service_recommendation == "new_service":
                    new_count += 1

        return ServiceMappingOverview(
            existing_service_count=existing_count,
            develop_existing_count=develop_count,
            new_service_count=new_count,
            total_ideas_analyzed=analyzed_count
        )

    @staticmethod
    def _get_top_matched_services(ideas: List[Idea], limit: int = 10) -> List[ServiceMatch]:
        """Get services that are matched most frequently"""
        service_data = defaultdict(lambda: {
            'count': 0,
            'scores': [],
            'category': None,
            'ideas': []
        })

        for idea in ideas:
            if idea.matching_services and isinstance(idea.matching_services, list):
                for service in idea.matching_services:
                    service_name = service.get('name')
                    if service_name:
                        service_data[service_name]['count'] += 1
                        service_data[service_name]['scores'].append(service.get('match_score', 0.0))
                        service_data[service_name]['category'] = service.get('category')
                        service_data[service_name]['ideas'].append({
                            'id': idea.id,
                            'title': idea.title,
                            'priority': idea.priority.value if idea.priority else 'medel'
                        })

        # Convert to ServiceMatch objects
        matches = []
        for service_name, data in service_data.items():
            avg_score = sum(data['scores']) / len(data['scores']) if data['scores'] else 0.0
            matches.append(ServiceMatch(
                service_name=service_name,
                service_category=data['category'],
                idea_count=data['count'],
                avg_match_score=avg_score,
                ideas=data['ideas'][:5]  # Limit to 5 sample ideas
            ))

        # Sort by idea count and return top matches
        matches.sort(key=lambda x: x.idea_count, reverse=True)
        return matches[:limit]

    @staticmethod
    def _get_development_needs(ideas: List[Idea], limit: int = 50) -> List[DevelopmentNeed]:
        """Get ideas sorted by development priority and impact"""
        needs = []

        for idea in ideas:
            if idea.service_recommendation:
                # Calculate match score (use highest matching service score)
                match_score = 0.0
                if idea.matching_services and isinstance(idea.matching_services, list):
                    scores = [s.get('match_score', 0.0) for s in idea.matching_services]
                    match_score = max(scores) if scores else 0.0

                needs.append(DevelopmentNeed(
                    idea_id=idea.id,
                    title=idea.title,
                    priority=PriorityEnum(idea.priority.value) if idea.priority else PriorityEnum.MEDIUM,
                    service_recommendation=idea.service_recommendation,
                    match_score=match_score,
                    impact=idea.development_impact or "medium"
                ))

        # Sort by priority (high first) and impact (high first)
        priority_order = {"hög": 3, "medel": 2, "låg": 1}
        impact_order = {"high": 3, "medium": 2, "low": 1}

        needs.sort(
            key=lambda x: (
                priority_order.get(x.priority.value, 0),
                impact_order.get(x.impact, 0)
            ),
            reverse=True
        )

        return needs[:limit]

    @staticmethod
    def _get_gap_analysis(ideas: List[Idea], limit: int = 5) -> List[GapAnalysis]:
        """Identify areas with many ideas but no matching services"""
        # Find ideas with new_service recommendation
        gap_ideas = [
            idea for idea in ideas
            if idea.service_recommendation == "new_service"
        ]

        if not gap_ideas:
            return []

        # Extract keywords from these ideas (from tags)
        keyword_ideas = defaultdict(list)

        for idea in gap_ideas:
            # Get keywords from tags
            for tag in idea.tags:
                keyword_ideas[tag.name].append({
                    'id': idea.id,
                    'title': idea.title,
                    'priority': idea.priority.value if idea.priority else 'medel'
                })

        # Create gap analysis entries
        gaps = []
        for keyword, idea_list in keyword_ideas.items():
            if len(idea_list) >= 2:  # Only include if at least 2 ideas share this keyword
                gaps.append(GapAnalysis(
                    area_keywords=[keyword],
                    idea_count=len(idea_list),
                    sample_ideas=idea_list[:3]  # Show max 3 sample ideas
                ))

        # Sort by idea count
        gaps.sort(key=lambda x: x.idea_count, reverse=True)

        # Group similar keywords together
        merged_gaps = []
        used_keywords = set()

        for gap in gaps:
            keyword = gap.area_keywords[0]
            if keyword not in used_keywords:
                # Find similar keywords (could be enhanced with better matching)
                similar = [g for g in gaps if g.area_keywords[0] not in used_keywords]

                if similar:
                    # Take the first one for now
                    merged_gaps.append(gap)
                    used_keywords.add(keyword)

        return merged_gaps[:limit]
