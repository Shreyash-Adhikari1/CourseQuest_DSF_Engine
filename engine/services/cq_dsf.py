from assessments.models import Assessment, CriterionScore
from engine.models import Pathway, PathwayRelevance, PathwayScore
from recommendations.models import Recommendation, RecommendationCriterionResult
from engine.services.rag.generator import generate_explanation


# Criteria groups — defines which criteria belong to which group
KNOWLEDGE_CRITERIA = [
    'programming',
    'logical_reasoning',
    'security_awareness',
]

PREFERENCE_CRITERIA = [
    'ai_interest',
    'security_interest',
    'systems_interest',
]

# Adaptive weighting constants
DEFAULT_KNOWLEDGE_WEIGHT = 0.6
DEFAULT_PREFERENCE_WEIGHT = 0.4
BALANCED_KNOWLEDGE_WEIGHT = 0.5
BALANCED_PREFERENCE_WEIGHT = 0.5
ADAPTIVE_THRESHOLD = 0.2

# Strength and improvement thresholds
STRENGTH_THRESHOLD = 0.75
IMPROVEMENT_THRESHOLD = 0.45

def extract_and_save_criterion_scores(assessment):
    """
    Extracts criterion scores from the raw payload and saves
    them as individual CriterionScore rows in the database.
    Returns a dictionary of criterion scores for use by the engine.
    """
    scores = assessment.raw_payload['scores']
    criterion_scores = {}

    for criterion_name, score_data in scores.items():
        CriterionScore.objects.create(
            assessment=assessment,
            criterion_name=criterion_name,
            value=score_data['value'],
            confidence=score_data['confidence']
        )
        criterion_scores[criterion_name] = {
            'value': score_data['value'],
            'confidence': score_data['confidence']
        }

    return criterion_scores

def calculate_adaptive_weights(criterion_scores):
    """
    Calculates adaptive weights based on the difference between
    knowledge and preference group averages.
    Returns a tuple of (knowledge_weight, preference_weight).
    """
    # calculate knowledge group average using raw values only
    knowledge_avg = sum(
        criterion_scores[c]['value'] for c in KNOWLEDGE_CRITERIA
    ) / len(KNOWLEDGE_CRITERIA)

    # calculate preference group average using raw values only
    preference_avg = sum(
        criterion_scores[c]['value'] for c in PREFERENCE_CRITERIA
    ) / len(PREFERENCE_CRITERIA)

    # measure the imbalance between the two groups
    difference = abs(knowledge_avg - preference_avg)

    # if imbalance exceeds threshold, rebalance to 50/50
    if difference > ADAPTIVE_THRESHOLD:
        return BALANCED_KNOWLEDGE_WEIGHT, BALANCED_PREFERENCE_WEIGHT

    # otherwise keep default 60/40
    return DEFAULT_KNOWLEDGE_WEIGHT, DEFAULT_PREFERENCE_WEIGHT

def calculate_pathway_scores(criterion_scores, k_weight, p_weight):
    """
    Calculates knowledge, preference, and final scores for every pathway
    using effective scores (value x confidence x relevance) and adaptive weights.
    Returns a list of dictionaries, one per pathway, with all scores included.
    """
    pathways = Pathway.objects.all()
    pathway_results = []

    for pathway in pathways:
        knowledge_score = 0
        preference_score = 0

        # fetch all relevance values for this pathway
        relevances = PathwayRelevance.objects.filter(pathway=pathway)

        # build a quick lookup dictionary for relevance scores
        relevance_map = {r.criterion_name: r.relevance_score for r in relevances}

        # calculate effective score per criterion and add to correct group
        for criterion_name, scores in criterion_scores.items():
            effective = scores['value'] * scores['confidence'] * relevance_map.get(criterion_name, 0)

            if criterion_name in KNOWLEDGE_CRITERIA:
                knowledge_score += effective
            elif criterion_name in PREFERENCE_CRITERIA:
                preference_score += effective

        # apply adaptive weights to get final score
        final_score = (k_weight * knowledge_score) + (p_weight * preference_score)

        pathway_results.append({
            'pathway': pathway,
            'knowledge_score': round(knowledge_score, 4),
            'preference_score': round(preference_score, 4),
            'final_score': round(final_score, 4)
        })

    return pathway_results

def save_pathway_scores(assessment, pathway_results):
    """
    Saves the calculated pathway scores to the database.
    One PathwayScore row per pathway per assessment.
    Returns the pathway_results list sorted by final_score
    descending for ranking.
    """
    for result in pathway_results:
        PathwayScore.objects.create(
            assessment=assessment,
            pathway=result['pathway'],
            knowledge_score=result['knowledge_score'],
            preference_score=result['preference_score'],
            final_score=result['final_score']
        )

    # sort by final_score descending — highest first
    return sorted(pathway_results, key=lambda x: x['final_score'], reverse=True)

def detect_strengths_and_improvements(criterion_scores):
    """
    Compares each criterion's raw value against thresholds
    to determine strengths and improvement areas.
    Returns two lists — strengths and improvements.
    """
    strengths = []
    improvements = []

    for criterion_name, scores in criterion_scores.items():
        if scores['value'] >= STRENGTH_THRESHOLD:
            strengths.append(criterion_name)
        elif scores['value'] <= IMPROVEMENT_THRESHOLD:
            improvements.append(criterion_name)

    return strengths, improvements

def save_recommendation(assessment, ranked_pathways, strengths, improvements):
    """
    Saves the final recommendation and criterion results to the database.
    explanation is left blank here — RAG + LLM fills it in later.
    Returns the created Recommendation object.
    """
    recommendation = Recommendation.objects.create(
        assessment=assessment,
        primary_pathway=ranked_pathways[0]['pathway'].name,
        secondary_pathway=ranked_pathways[1]['pathway'].name,
        tertiary_pathway=ranked_pathways[2]['pathway'].name,
    )

    # save strengths
    for criterion_name in strengths:
        RecommendationCriterionResult.objects.create(
            recommendation=recommendation,
            criterion_name=criterion_name,
            result_type='strength'
        )

    # save improvements
    for criterion_name in improvements:
        RecommendationCriterionResult.objects.create(
            recommendation=recommendation,
            criterion_name=criterion_name,
            result_type='improvement'
        )

    return recommendation

def run_engine(assessment_id):
    """
    Main entry point for the CQ-DSF engine.
    Takes an assessment_id, runs the full decision pipeline,
    and returns the final Recommendation object.
    """
    # guard — prevent engine from running twice on same assessment
    if Recommendation.objects.filter(assessment_id=assessment_id).exists():
        return Recommendation.objects.get(assessment_id=assessment_id)
    
    # fetch the assessment from the database
    assessment = Assessment.objects.get(id=assessment_id)

    # step 1 — extract and save criterion scores
    criterion_scores = extract_and_save_criterion_scores(assessment)

    # step 2 — calculate adaptive weights
    k_weight, p_weight = calculate_adaptive_weights(criterion_scores)

    # step 3 — calculate pathway scores
    pathway_results = calculate_pathway_scores(criterion_scores, k_weight, p_weight)

    # step 4 — save pathway scores and get ranked results
    ranked_pathways = save_pathway_scores(assessment, pathway_results)

    # step 5 — detect strengths and improvements
    strengths, improvements = detect_strengths_and_improvements(criterion_scores)

    # step 6 — save and return recommendation
    recommendation = save_recommendation(assessment, ranked_pathways, strengths, improvements)
    # build recommendation data for RAG + LLM

    recommendation_data = {
    'primary_pathway': recommendation.primary_pathway,
    'secondary_pathway': recommendation.secondary_pathway,
    'tertiary_pathway': recommendation.tertiary_pathway,
    'strengths': strengths,
    'improvements': improvements
    }

    # generate explanation and save to recommendation

    explanation = generate_explanation(recommendation_data)
    recommendation.explanation = explanation
    recommendation.save()

    return recommendation