#!/usr/bin/env python3
"""
AI Innovation Analysis Script for GitHub Actions
This script analyzes innovation ideas submitted via GitHub Issues
"""

import os
import sys
import requests
import json


def get_env_var(name, default=None):
    """Safely get environment variable"""
    return os.getenv(name, default)


def analyze_with_ai(text_content, issue_title):
    """Analyze the idea using AI service"""

    # Configuration
    ai_service_url = get_env_var(
        "AI_SERVICE_URL", "https://llm.innovationsarenan.se/v1"
    )
    ai_api_key = get_env_var("AI_API_KEY")

    prompt = f"""Analyze this innovation idea:

Title: {issue_title}

Content: {text_content}

Provide analysis in JSON format with:
- summary
- potential_impact (Low/Medium/High)
- feasibility (Low/Medium/High)  
- innovation_score (1-10)
- recommendation
- implementation_challenges (array)
- success_factors (array)
- related_services (array)

Be analytical and provide actionable insights."""

    headers = {"Content-Type": "application/json"}
    if ai_api_key:
        headers["Authorization"] = f"Bearer {ai_api_key}"

    data = {
        "model": "mistralai/Devstral-2-123B-Instruct-2512",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 800,
    }

    try:
        response = requests.post(
            f"{ai_service_url}/chat/completions", headers=headers, json=data, timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"⚠️ AI Service Error: {str(e)}", file=sys.stderr)
        return None


def perform_service_mapping(text_content, issue_title):
    """Perform service mapping using RAG"""
    try:
        from rag_service_integration import RAGServiceMapper

        mapper = RAGServiceMapper()
        service_mapping = mapper.map_idea_to_services(text_content, issue_title)

        # Get integration recommendations
        recommendations = mapper.get_service_recommendations(text_content)

        return {
            "service_mapping": service_mapping,
            "integration_recommendations": recommendations,
        }

    except ImportError:
        print("⚠️ RAG service integration not available", file=sys.stderr)
        return None
    except Exception as e:
        print(f"⚠️ Service mapping error: {str(e)}", file=sys.stderr)
        return None


def post_github_comment(repo, issue_number, comment_body, github_token):
    """Post comment to GitHub issue"""
    comment_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    try:
        response = requests.post(
            comment_url, headers=headers, json={"body": comment_body}
        )
        return response.status_code == 201
    except Exception as e:
        print(f"❌ Failed to post comment: {str(e)}", file=sys.stderr)
        return False


def format_analysis_result(ai_response):
    """Format the AI analysis into a readable comment"""
    try:
        analysis = json.loads(ai_response)

        comment = f"""## 🤖 AI Innovation Analysis

### Idea Evaluation

**Summary**: {analysis.get("summary", "N/A")}

**Potential Impact**: {analysis.get("potential_impact", "Unknown")}
**Feasibility**: {analysis.get("feasibility", "Unknown")}
**Innovation Score**: {analysis.get("innovation_score", "N/A")}/10

**Recommendation**: {analysis.get("recommendation", "N/A")}

### Implementation Considerations

**Potential Challenges**:
"""

        if analysis.get("implementation_challenges"):
            for challenge in analysis["implementation_challenges"]:
                comment += f"\n- {challenge}"
        else:
            comment += "\n- None identified"

        comment += "\n\n**Key Success Factors**:"

        if analysis.get("success_factors"):
            for factor in analysis["success_factors"]:
                comment += f"\n- {factor}"
        else:
            comment += "\n- None identified"

        comment += f"""

### Related Services

"""

        if analysis.get("related_services"):
            for service in analysis["related_services"]:
                comment += f"\n- {service}"
        else:
            comment += "\n- None identified"

        comment += """

---
*This is an automated analysis. Human review will follow.*

Thank you for your contribution to Göteborg's innovation ecosystem! 🌟"""

        return comment

    except json.JSONDecodeError:
        return f"""## 🤖 AI Innovation Analysis

**Raw Analysis**: {ai_response[:500]}...

**Note**: The AI response could not be parsed as JSON.

---
*This is an automated analysis. Human review will follow.*"""


def format_service_mapping(service_mapping_result):
    """Format service mapping results for the comment"""
    if not service_mapping_result:
        return ""

    service_mapping = service_mapping_result.get("service_mapping", {})
    recommendations = service_mapping_result.get("integration_recommendations", [])

    mapping_section = "\n\n### 🗺️ Service Mapping Analysis"

    if isinstance(service_mapping, dict):
        if "raw_analysis" in service_mapping:
            mapping_section += f"\n\n{service_mapping['raw_analysis']}"
        elif "service_mappings" in service_mapping:
            mapping_section += "\n\n**Service Mappings Found:**"
            for mapping in service_mapping["service_mappings"]:
                mapping_section += f"\n- {mapping}"
    else:
        mapping_section += f"\n\n{str(service_mapping)}"

    if recommendations:
        mapping_section += "\n\n### 💡 Integration Recommendations"
        for i, rec in enumerate(recommendations, 1):
            if isinstance(rec, dict):
                mapping_section += (
                    f"\n{i}. {rec.get('recommendation', 'No recommendation')}"
                )
            else:
                mapping_section += f"\n{i}. {str(rec)}"

    return mapping_section


def main():
    """Main execution function"""
    print("🚀 Starting AI Innovation Analysis...")

    # Get environment variables
    issue_number = get_env_var("ISSUE_NUMBER")
    issue_title = get_env_var("ISSUE_TITLE")
    issue_body = get_env_var("ISSUE_BODY")
    repo = get_env_var("REPO")
    github_token = get_env_var("GITHUB_TOKEN")

    if not all([issue_number, issue_title, issue_body, repo, github_token]):
        print("❌ Missing required environment variables", file=sys.stderr)
        sys.exit(1)

    # Perform AI analysis
    print("🤖 Analyzing idea with AI service...")
    ai_analysis = analyze_with_ai(issue_body, issue_title)

    # Perform service mapping
    print("🗺️ Mapping idea to existing services...")
    service_mapping_result = perform_service_mapping(issue_body, issue_title)

    if ai_analysis and "choices" in ai_analysis:
        ai_response = ai_analysis["choices"][0]["message"]["content"]
        comment_body = format_analysis_result(ai_response)

        # Add service mapping to comment if available
        if service_mapping_result:
            comment_body += format_service_mapping(service_mapping_result)
    else:
        print("⚠️ AI analysis failed, using fallback")
        comment_body = """## 🤖 AI Innovation Analysis

**Status**: Automated analysis unavailable

**Note**: This idea will be reviewed manually by our innovation team.

---
Thank you for your contribution! 🌟"""

    # Post the analysis comment
    print("📝 Posting analysis to GitHub issue...")
    success = post_github_comment(repo, issue_number, comment_body, github_token)

    if success:
        print("✅ AI Innovation Analysis completed successfully!")
        return 0
    else:
        print("❌ Analysis completed but failed to post results", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
