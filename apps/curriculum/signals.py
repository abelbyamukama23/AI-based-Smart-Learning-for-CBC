from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.curriculum.models import CurriculumNode, CurriculumEdge

@receiver(post_save, sender=CurriculumNode)
@receiver(post_delete, sender=CurriculumNode)
@receiver(post_save, sender=CurriculumEdge)
@receiver(post_delete, sender=CurriculumEdge)
def trigger_graph_reload(sender, instance, **kwargs):
    """
    Observer Pattern: Whenever a CurriculumNode or CurriculumEdge is created, updated, or deleted,
    we trigger a graph reload on the KnowledgeGraphService so the agents always have real-time data.
    """
    from apps.ai_tutor.kag_service import KnowledgeGraphService
    
    # Reload the in-memory graph
    KnowledgeGraphService().load_graph(force_reload=True)
