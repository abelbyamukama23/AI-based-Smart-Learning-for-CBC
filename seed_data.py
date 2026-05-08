import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cbc_backend.settings')
django.setup()

from apps.accounts.models import School, User, Learner, Role, ClassLevel
from apps.curriculum.models import Subject, Level, Competency, Lesson

def run():
    print("Seeding CBC MVP Data...")

    # 1. Schools
    school1, _ = School.objects.get_or_create(school_name="Gayaza High School", defaults={"region": "Central", "district": "Wakiso"})
    school2, _ = School.objects.get_or_create(school_name="Namilyango College", defaults={"region": "Central", "district": "Mukono"})
    
    # 2. Users / Learners
    user, created = User.objects.get_or_create(email="demo@example.com", defaults={"username": "demo_learner", "role": Role.LEARNER})
    if created:
        user.set_password("password123")
        user.save()
        Learner.objects.create(user=user, school=school1, class_level=ClassLevel.S3)
        print("Created demo_learner (demo@example.com) / password123")
        
    admin, created = User.objects.get_or_create(email="admin@example.com", defaults={"username": "admin", "role": Role.ADMIN, "is_superuser": True, "is_staff": True})
    if created:
        admin.set_password("admin123")
        admin.save()
        print("Created admin (admin@example.com) / admin123")

    # 3. Curriculum Levels
    s1, _ = Level.objects.get_or_create(level_name=ClassLevel.S1, defaults={"sort_order": 1})
    s2, _ = Level.objects.get_or_create(level_name=ClassLevel.S2, defaults={"sort_order": 2})
    s3, _ = Level.objects.get_or_create(level_name=ClassLevel.S3, defaults={"sort_order": 3})

    # 4. Curriculum Subjects
    math, _ = Subject.objects.get_or_create(subject_name="Mathematics")
    bio, _ = Subject.objects.get_or_create(subject_name="Biology")
    phys, _ = Subject.objects.get_or_create(subject_name="Physics")

    # 5. Competencies
    comp1, _ = Competency.objects.get_or_create(
        subject=bio, level=s3, competency_name="Understanding Photosynthesis",
        defaults={"description": "The learner should be able to explain the process of photosynthesis and its importance."}
    )
    comp2, _ = Competency.objects.get_or_create(
        subject=math, level=s1, competency_name="Basic Algebra",
        defaults={"description": "The learner should be able to solve simple linear equations."}
    )

    # 6. Lessons
    lesson1, created = Lesson.objects.get_or_create(
        title="Introduction to Photosynthesis",
        subject=bio,
        class_level=s3,
        defaults={
            "description": "Learn how plants make their own food.",
            "body_html": "<article><h2>Photosynthesis</h2><p>Photosynthesis is the process...</p></article>"
        }
    )
    if created:
        lesson1.competencies.add(comp1)

    lesson2, created = Lesson.objects.get_or_create(
        title="Solving Linear Equations",
        subject=math,
        class_level=s1,
        defaults={
            "description": "Master the basics of finding 'x'.",
            "body_html": "<article><h2>Linear Equations</h2><p>To solve for x...</p></article>"
        }
    )
    if created:
        lesson2.competencies.add(comp2)

    print("Seeding complete!")

if __name__ == '__main__':
    run()
