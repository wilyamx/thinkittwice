from django.core.management import BaseCommand

from PoleLuxe.models.user import (
    User,
    UserDailyChallengeQuizAnswer,
    UserKnowledgeQuizAnswer,
    UserKnowledgeQuizResult,
)
from PoleLuxe.models.knowledge import UserKnowledgeResult
from PoleLuxe.models.dailychallenge import DailyChallengeResult


class Command(BaseCommand):
    """
    Delete user quiz results (including the answers)
    e.g.
    ./manage.py removeuserquizresult {0,1,2} 3761
    """
    DAILY_CHALLENGE_QUIZ_RESULT = 0
    KNOWLEDGE_QUIZ_RESULT = 1
    DC_AND_K_QUIZ_RESULT = 2

    def add_arguments(self, parser):
        parser.add_argument('quiz_type', type=int)
        parser.add_argument('user_id', type=int)

    def _remove_knowledge_quiz_result(self, user):
        UserKnowledgeQuizAnswer.objects.filter(
            user=user
        ).delete()
        UserKnowledgeQuizResult.objects.filter(
            user_id=user
        ).delete()
        UserKnowledgeResult.objects.filter(
            user_id=user
        ).delete()

    def _remove_daily_challenge_quiz_result(self, user):
        UserDailyChallengeQuizAnswer.objects.filter(
            user=user
        ).delete()
        DailyChallengeResult.objects.filter(
            user_id=user
        ).delete()

    def handle(self, *args, **options):
        user_id = options['user_id']
        quiz_type = options['quiz_type']

        user = None
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            print('User {} does not exist'.format(user_id))

        if user:
            # POST /api/v1/userdailychallengequizanswers/
            # POST /api/v1/daily_challenge
            if quiz_type == self.DAILY_CHALLENGE_QUIZ_RESULT:
                self._remove_daily_challenge_quiz_result(user)

            # POST /api/v1/userknowledgequizanswers/
            elif quiz_type == self.KNOWLEDGE_QUIZ_RESULT:
                self._remove_knowledge_quiz_result(user)

            # all quiz types
            elif quiz_type == self.DC_AND_K_QUIZ_RESULT:
                self._remove_daily_challenge_quiz_result(user)
                self._remove_knowledge_quiz_result(user)

            user.update_and_get_points()
