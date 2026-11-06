from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from apps.flashcards.models import Flashcard, StudyAttempt

User = get_user_model()


class StudyAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='felicia', password='pass12345')
        self.client.force_authenticate(self.user)
        self.easy = Flashcard.objects.create(question='Easy', answer='A')
        self.hard = Flashcard.objects.create(question='Hard', answer='B')

    def test_submit_attempt(self):
        res = self.client.post('/api/flashcards/study/attempts/',
                               {'flashcard': self.easy.id, 'is_correct': True, 'confidence': 4},
                               format='json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(StudyAttempt.objects.get().user, self.user)

    def test_confidence_out_of_range_rejected(self):
        res = self.client.post('/api/flashcards/study/attempts/',
                               {'flashcard': self.easy.id, 'is_correct': True, 'confidence': 9},
                               format='json')
        self.assertEqual(res.status_code, 400)

    def test_weak_cards_come_first(self):
        StudyAttempt.objects.create(user=self.user, flashcard=self.easy, is_correct=True, confidence=5)
        StudyAttempt.objects.create(user=self.user, flashcard=self.hard, is_correct=False, confidence=1)
        res = self.client.get('/api/flashcards/study/next/')
        self.assertEqual(res.json()[0]['id'], self.hard.id)

    def test_stats(self):
        StudyAttempt.objects.create(user=self.user, flashcard=self.easy, is_correct=True, confidence=4)
        StudyAttempt.objects.create(user=self.user, flashcard=self.hard, is_correct=False, confidence=2)
        res = self.client.get('/api/flashcards/study/stats/')
        self.assertEqual(res.json()['total'], 2)
        self.assertEqual(res.json()['accuracy'], 0.5)

    def test_login_required(self):
        self.client.force_authenticate(None)
        res = self.client.get('/api/flashcards/study/stats/')
        self.assertIn(res.status_code, (401, 403))