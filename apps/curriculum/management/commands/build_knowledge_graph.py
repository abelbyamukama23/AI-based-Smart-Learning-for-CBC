import json
import logging
from django.core.management.base import BaseCommand
from apps.curriculum.models import Lesson, CurriculumNode, CurriculumEdge, NodeType, EdgeType
from decouple import config
from openai import OpenAI

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Build the Curriculum Knowledge Graph by extracting concepts and edges from Lessons using DeepSeek."

    def handle(self, *args, **options):
        self.stdout.write("Starting Knowledge Graph Build Process...")
        api_key = config("DEEPSEEK_API_KEY", default="")
        if not api_key:
            self.stdout.write(self.style.ERROR("DEEPSEEK_API_KEY is not set. Cannot build graph."))
            return

        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
        lessons = Lesson.objects.all()

        for lesson in lessons:
            self.stdout.write(f"Processing Lesson: {lesson.title}")
            
            # 1. Create a node for the lesson itself
            lesson_node, _ = CurriculumNode.objects.get_or_create(
                name=lesson.title,
                node_type=NodeType.LESSON,
                defaults={"description": lesson.description[:255]}
            )

            # 2. Extract concepts and prerequisites using LLM
            prompt = (
                f"Analyze the following educational lesson from the Uganda CBC curriculum.\n"
                f"Title: {lesson.title}\n"
                f"Subject: {lesson.subject.subject_name if lesson.subject else 'General'}\n"
                f"Content: {lesson.description}\n\n"
                f"Extract the core conceptual topics taught in this lesson. Also, what concepts must a student "
                f"already understand BEFORE learning this lesson (prerequisites)?\n"
                f"Return ONLY valid JSON in this exact format:\n"
                f"{{\n"
                f"  \"core_concepts\": [\"Concept A\", \"Concept B\"],\n"
                f"  \"prerequisites\": [\"Concept C\"]\n"
                f"}}"
            )

            try:
                resp = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                
                result = json.loads(resp.choices[0].message.content)
                core_concepts = result.get("core_concepts", [])
                prerequisites = result.get("prerequisites", [])

                # 3. Create Core Concept Nodes and TEACHES edges
                for concept_name in core_concepts:
                    concept_node, _ = CurriculumNode.objects.get_or_create(
                        name=concept_name,
                        node_type=NodeType.CONCEPT
                    )
                    CurriculumEdge.objects.get_or_create(
                        source=lesson_node,
                        target=concept_node,
                        relationship=EdgeType.TEACHES
                    )

                # 4. Create Prerequisite Nodes and REQUIRES edges
                for prereq_name in prerequisites:
                    prereq_node, _ = CurriculumNode.objects.get_or_create(
                        name=prereq_name,
                        node_type=NodeType.CONCEPT
                    )
                    CurriculumEdge.objects.get_or_create(
                        source=lesson_node,
                        target=prereq_node,
                        relationship=EdgeType.REQUIRES
                    )
                    
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Failed to process lesson {lesson.title}: {e}"))

        self.stdout.write(self.style.SUCCESS("Knowledge Graph Build Process Complete!"))
