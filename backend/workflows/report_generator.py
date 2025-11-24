"""Final Report Generator for Frontend UI"""

from typing import Dict, Any, List
from pathlib import Path
import json


def generate_final_report(
    session_id: str,
    user_input: Dict[str, Any],
    personas: List[Dict[str, Any]],
    round1_result: Dict[str, Any],
    round2_result: Dict[str, Any],
    round3_result: Dict[str, Any],
    round4_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate frontend-ready report data after Round 4 completion
    
    Args:
        session_id: Session identifier
        user_input: User input data
        personas: Agent personas
        round1_result: Round 1 results (selected criteria)
        round2_result: Round 2 results (AHP weights)
        round3_result: Round 3 results (decision matrix)
        round4_result: Round 4 results (TOPSIS ranking)
        
    Returns:
        Structured report data for frontend UI
    """
    
    # Extract data from round results
    ranking = round4_result.get('final_ranking', [])
    criteria_weights = round2_result.get('criteria_weights', {})
    decision_matrix = round3_result.get('decision_matrix', {})
    selected_criteria = round1_result.get('final_criteria', [])  # Round 1에서는 final_criteria로 저장됨
    agent_personas = personas
    consistency_ratio = round2_result.get('consistency_ratio', 0)
    
    # 1. Top 3 Recommendations
    top_recommendations = []
    for item in ranking[:3]:  # Top 3 only
        major = item['major']
        criterion_scores = item.get('criterion_scores', {})
        
        # Identify strengths (score >= 7.0)
        strengths = []
        weaknesses = []
        
        for criterion_name, score in criterion_scores.items():
            display_text = f"{criterion_name} ({score:.1f}/10)"
            if score >= 7.0:
                strengths.append(display_text)
            elif score < 6.0:
                weaknesses.append(display_text)
        
        # Sort by score (highest first)
        strengths.sort(key=lambda x: float(x.split('(')[1].split('/')[0]), reverse=True)
        weaknesses.sort(key=lambda x: float(x.split('(')[1].split('/')[0]))
        
        top_recommendations.append({
            "rank": item['rank'],
            "major": major,
            "topsis_score": round(item['closeness_coefficient'], 4),
            "strengths": strengths[:3],  # Top 3 strengths
            "weaknesses": weaknesses[:2] if weaknesses else ["없음"],  # Top 2 weaknesses
            "progress_percentage": round(item['closeness_coefficient'] * 100, 1),
            "distance_to_ideal": round(item['distance_to_ideal'], 4),
            "distance_to_anti_ideal": round(item['distance_to_anti_ideal'], 4)
        })
    
    # 2. Criteria Weights (converted to percentage)
    criteria_weights_percent = {
        name: round(weight * 100, 1)
        for name, weight in criteria_weights.items()
    }
    
    # Sort by weight (descending)
    sorted_criteria_weights = dict(
        sorted(criteria_weights_percent.items(), key=lambda x: x[1], reverse=True)
    )
    
    # 3. Decision Matrix (for table display)
    formatted_decision_matrix = {}
    for major, scores in decision_matrix.items():
        formatted_decision_matrix[major] = {
            criterion: round(score, 1)
            for criterion, score in scores.items()
        }
    
    # 4. Agent Personas (for reference)
    formatted_personas = []
    for persona in agent_personas:
        formatted_personas.append({
            "name": persona.get('name', ''),
            "perspective": persona.get('perspective', ''),
            "key_strengths": persona.get('key_strengths', []),
            "persona_description": persona.get('persona_description', '')
        })
    
    # 5. Complete Ranking (all majors)
    complete_ranking = []
    for item in ranking:
        complete_ranking.append({
            "rank": item['rank'],
            "major": item['major'],
            "topsis_score": round(item['closeness_coefficient'], 4),
            "progress_percentage": round(item['closeness_coefficient'] * 100, 1)
        })
    
    # 6. Criteria Descriptions (for tooltip)
    criteria_descriptions = {
        criterion['name']: criterion.get('description', '')
        for criterion in selected_criteria
    }
    
    return {
        "session_id": session_id,
        "top_recommendations": top_recommendations,
        "complete_ranking": complete_ranking,
        "criteria_weights": sorted_criteria_weights,
        "decision_matrix": formatted_decision_matrix,
        "criteria_descriptions": criteria_descriptions,
        "agent_personas": formatted_personas,
        "metadata": {
            "total_majors": len(ranking),
            "total_criteria": len(criteria_weights),
            "consistency_ratio": round(consistency_ratio, 4)
        }
    }


def save_report(report_data: Dict[str, Any], session_id: str, output_dir: Path = Path("output")) -> Path:
    """
    Save final report as JSON
    
    Args:
        report_data: Generated report data
        session_id: Session identifier
        output_dir: Directory to save report
        
    Returns:
        Path to saved report file
    """
    report_file = output_dir / f"report_{session_id}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    print(f"[REPORT SAVED] {report_file}")
    return report_file


def print_report_summary(report_data: Dict[str, Any]):
    """Print a summary of the generated report"""
    
    print("\n" + "="*80)
    print("📊 FINAL REPORT SUMMARY")
    print("="*80)
    
    print("\n[TOP 3 RECOMMENDATIONS]")
    for rec in report_data['top_recommendations']:
        print(f"\n{rec['rank']}위: {rec['major']} (TOPSIS: {rec['topsis_score']})")
        print(f"  ✅ 강점: {', '.join(rec['strengths'])}")
        print(f"  ⚠️  개선점: {', '.join(rec['weaknesses'])}")
    
    print("\n[CRITERIA WEIGHTS]")
    for criterion, weight in report_data['criteria_weights'].items():
        print(f"  • {criterion}: {weight}%")
    
    print("\n[AGENT PERSONAS]")
    for persona in report_data['agent_personas']:
        print(f"  • {persona['name']}: {persona['perspective']}")
        print(f"    강점: {', '.join(persona['key_strengths'])}")
    
    print("\n" + "="*80)
