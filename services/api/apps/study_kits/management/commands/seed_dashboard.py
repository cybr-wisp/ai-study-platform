from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken

from apps.courses.models import Course
from apps.flashcards.models import Flashcard
from apps.learning.models import CardProgress
from apps.study_kits.models import StudyKit, StudyKitStatus, StudyKitType

# Matches the student dashboard mockup: every kit sits at 75% mastery.
SEED_COURSES = [
    ('Calculus II', '#22C55E', [
        ('Lecture 1', StudyKitType.LECTURE),
        ('Lecture 2', StudyKitType.LECTURE),
        ('Tutorial 1', StudyKitType.TUTORIAL),
    ]),
    ('Physics II', '#A855F7', [
        ('Lecture 1', StudyKitType.LECTURE),
        ('Tutorial 1', StudyKitType.TUTORIAL),
    ]),
]
CARDS_PER_KIT = 4
MASTERED_PER_KIT = 3


class Command(BaseCommand):
    help = 'Seed a dev user with the courses and study kits shown in the dashboard mockup.'

    def add_arguments(self, parser):
        parser.add_argument('--email', default='dev@example.com')
        parser.add_argument('--password', default='dev-password-123')
        parser.add_argument('--token-days', type=int, default=30, help='Lifetime of the printed dev access token.')

    def handle(self, *args, **options):
        User = get_user_model()
        user, created = User.objects.get_or_create(
            email=options['email'], defaults={'username': options['email']},
        )
        if created:
            user.set_password(options['password'])
            user.save()

        for position, (title, color, kits) in enumerate(SEED_COURSES):
            course, _ = Course.objects.get_or_create(
                owner=user, title=title, defaults={'color': color, 'position': position},
            )
            for kit_title, kit_type in kits:
                kit, kit_created = StudyKit.objects.get_or_create(
                    course=course, title=kit_title,
                    defaults={'kit_type': kit_type, 'status': StudyKitStatus.READY},
                )
                if kit_created:
                    self._seed_cards(user, kit)

        token = AccessToken.for_user(user)
        token.set_exp(from_time=timezone.now(), lifetime=timedelta(days=options['token_days']))
        self.stdout.write(self.style.SUCCESS(f'Seeded dashboard data for {user.email}.'))
        self.stdout.write(f'API_DEV_TOKEN={token}')

    def _seed_cards(self, user, kit):
        for i in range(CARDS_PER_KIT):
            card = Flashcard.objects.create(
                study_kit=kit, front=f'{kit.title} question {i + 1}',
                back=f'{kit.title} answer {i + 1}', position=i,
            )
            CardProgress.objects.create(
                user=user, flashcard=card, times_seen=1, times_correct=1,
                is_mastered=i < MASTERED_PER_KIT,
            )
