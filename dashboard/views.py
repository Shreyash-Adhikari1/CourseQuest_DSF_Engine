from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Avg
from assessments.models import Assessment, CriterionScore
from engine.models import PathwayScore
from recommendations.models import Recommendation, RecommendationCriterionResult
from django.http import HttpResponse
from xhtml2pdf import pisa
from django.template.loader import render_to_string
from django.shortcuts import render, get_object_or_404, redirect
import io


def global_dashboard(request):
    """
    Global analytics page — aggregate patterns across all assessments.
    """
    # total assessments count
    total_assessments = Assessment.objects.count()

    # pathway distribution — how many students got each primary recommendation
    pathway_distribution = Recommendation.objects.values(
        'primary_pathway'
    ).annotate(
        count=Count('id')
    ).order_by('-count')

    # strength frequency — most common strengths across all students
    strength_frequency = RecommendationCriterionResult.objects.filter(
        result_type='strength'
    ).values('criterion_name').annotate(
        count=Count('id')
    ).order_by('-count')

    # improvement frequency — most common improvements across all students
    improvement_frequency = RecommendationCriterionResult.objects.filter(
        result_type='improvement'
    ).values('criterion_name').annotate(
        count=Count('id')
    ).order_by('-count')

    # average criterion scores across all students
    average_scores = CriterionScore.objects.values(
        'criterion_name'
    ).annotate(
        avg_value=Avg('value'),
        avg_confidence=Avg('confidence')
    ).order_by('criterion_name')

    # recent assessments list
    recent_assessments = Assessment.objects.order_by(
        '-submitted_at'
    )[:10]

    context = {
        'total_assessments': total_assessments,
        'pathway_distribution': list(pathway_distribution),
        'strength_frequency': list(strength_frequency),
        'improvement_frequency': list(improvement_frequency),
        'average_scores': list(average_scores),
        'recent_assessments': recent_assessments,
    }

    return render(request, 'dashboard/global.html', context)


def individual_report(request, test_taker_id):
    """
    Individual report page — full recommendation and charts
    for one specific assessment.
    """
    assessment = get_object_or_404(Assessment, test_taker_id=test_taker_id)

    # handle name/email form submission
    if request.method == 'POST':
        name = request.POST.get('test_taker_name', '').strip()
        email = request.POST.get('test_taker_email', '').strip()
        if name:
            assessment.test_taker_name = name
        if email:
            assessment.test_taker_email = email
        assessment.save()

    # fetch recommendation
    recommendation = get_object_or_404(Recommendation, assessment=assessment)

    # fetch criterion scores
    criterion_scores = CriterionScore.objects.filter(assessment=assessment)

    # fetch pathway scores
    pathway_scores = PathwayScore.objects.filter(
        assessment=assessment
    ).select_related('pathway').order_by('-final_score')

    # fetch strengths and improvements
    strengths = RecommendationCriterionResult.objects.filter(
        recommendation=recommendation,
        result_type='strength'
    )
    improvements = RecommendationCriterionResult.objects.filter(
        recommendation=recommendation,
        result_type='improvement'
    )

    # prepare criterion radar chart data
    radar_labels = [cs.criterion_name for cs in criterion_scores]
    radar_values = [cs.value for cs in criterion_scores]

    # prepare pathway comparison chart data
    pathway_labels = [ps.pathway.name for ps in pathway_scores]
    pathway_final_scores = [ps.final_score for ps in pathway_scores]
    pathway_knowledge_scores = [ps.knowledge_score for ps in pathway_scores]
    pathway_preference_scores = [ps.preference_score for ps in pathway_scores]

    context = {
        'assessment': assessment,
        'recommendation': recommendation,
        'criterion_scores': criterion_scores,
        'pathway_scores': pathway_scores,
        'strengths': strengths,
        'improvements': improvements,
        'radar_labels': radar_labels,
        'radar_values': radar_values,
        'pathway_labels': pathway_labels,
        'pathway_final_scores': pathway_final_scores,
        'pathway_knowledge_scores': pathway_knowledge_scores,
        'pathway_preference_scores': pathway_preference_scores,
    }
    return render(request, 'dashboard/report.html', context)