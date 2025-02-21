from git_real.models import PullRequest
import git_real
import mock
from django.test import TestCase
from curriculum_tracking.models import (
    AgileCard,
    RecruitProject,
    TopicProgress,
    WorkshopAttendance,
    ContentItem,
    TopicReview,
)
from . import factories
from core.tests.factories import UserFactory
from social_auth.tests.factories import SocialProfileFactory, GithubOAuthTokenFactory
from datetime import timedelta
from git_real.constants import GIT_REAL_BOT_USERNAME, GITHUB_DATETIME_FORMAT
from git_real.tests import factories as git_real_factories

from curriculum_tracking.constants import (
    RED_FLAG,
    NOT_YET_COMPETENT,
    COMPETENT,
    EXCELLENT,
)
from django.utils import timezone

TYPESCRIPT = "ts"
JAVASCRIPT = "js"


class oldest_open_pr_updated_time_Tests(TestCase):
    def setUp(self):
        self.card = factories.AgileCardFactory()
        self.card.recruit_project.repository = git_real_factories.RepositoryFactory()
        self.card.save()
        self.repository = self.card.recruit_project.repository

    def test_no_prs(self):
        self.assertIsNone(self.card.oldest_open_pr_updated_time)

    def test_has_prs(self):
        today = timezone.now()
        yesterday = today - timezone.timedelta(days=1)

        pr_yesterday = git_real_factories.PullRequestFactory(
            repository=self.repository, updated_at=yesterday
        )
        self.assertEqual(self.card.oldest_open_pr_updated_time, yesterday)
        git_real_factories.PullRequestFactory(
            repository=self.repository, updated_at=today
        )
        self.assertEqual(self.card.oldest_open_pr_updated_time, yesterday)
        pr_yesterday.state = PullRequest.CLOSED
        pr_yesterday.save()
        self.assertEqual(self.card.oldest_open_pr_updated_time, today)


class start_project_Tests(TestCase):
    def setUp(self):
        bot = SocialProfileFactory(github_name=GIT_REAL_BOT_USERNAME)
        GithubOAuthTokenFactory(user=bot.user)

    def assert_users_same(self, card, project):
        card_assignees = sorted([o.id for o in card.assignees.all()])
        card_reviewers = sorted([o.id for o in card.reviewers.all()])
        project_reviewers = sorted([o.id for o in project.reviewer_users.all()])
        project_assignees = sorted([o.id for o in project.recruit_users.all()])

        self.assertEqual(card_assignees, project_assignees)
        self.assertEqual(card_reviewers, project_reviewers)

    @mock.patch("git_real.helpers.get_repo")
    @mock.patch.object(RecruitProject, "setup_repository")
    def test_start_project_creates_project_if_not_exists(self, get_repo, *_):

        card = factories.AgileCardFactory(
            status=AgileCard.READY,
            recruit_project=None,
            content_item=factories.ProjectContentItemFactory(
                project_submission_type=ContentItem.REPOSITORY
            ),
            assignees=[SocialProfileFactory().user],
        )

        self.assertIsNone(card.recruit_project)

        get_repo.return_value = {
            "full_name": "me/kiff",
            "owner": {"login": "me"},
            "ssh_url": "https://whatever.git",
            "private": True,
            "created_at": timezone.now().strftime(GITHUB_DATETIME_FORMAT),
            "archived": False,
        }

        card.start_project()

        self.assertIsNotNone(card.recruit_project)
        project = card.recruit_project

        card.refresh_from_db()
        project.refresh_from_db()

        self.assert_users_same(card=card, project=project)
        self.assertEqual(project.content_item, card.content_item)
        self.assertTrue(project.setup_repository.called)
        self.assertEqual(card.status, AgileCard.IN_PROGRESS)
        self.assertIsNotNone(project.start_time)

    @mock.patch.object(RecruitProject, "setup_repository")
    def test_start_project_works_even_if_project_instance_exists(self, *_):
        card = factories.AgileCardFactory(
            status=AgileCard.READY,
            recruit_project=None,
            content_item=factories.ProjectContentItemFactory(),
            assignees=[SocialProfileFactory().user],
        )
        self.assertIsNone(card.recruit_project)

        card.set_due_time(timezone.now())
        self.assertEqual(card.status, AgileCard.READY)

        self.assertIsNotNone(card.recruit_project)
        card.start_project()

        project = card.recruit_project

        card.refresh_from_db()
        project.refresh_from_db()

        self.assert_users_same(card=card, project=project)
        self.assertEqual(project.content_item, card.content_item)
        self.assertTrue(project.setup_repository.called)
        self.assertEqual(card.status, AgileCard.IN_PROGRESS)
        self.assertIsNotNone(project.start_time)

    @mock.patch("social_auth.github_api.Api")
    @mock.patch("git_real.helpers.add_collaborator")
    @mock.patch.object(RecruitProject, "setup_repository")
    @mock.patch("git_real.helpers.get_repo")
    def test_that_project_submission_type_REPOSITORY_creates_a_repo_with_flavourful_name(
        self, get_repo, *_
    ):
        content_item = factories.ProjectContentItemFactory(
            flavours=[TYPESCRIPT, JAVASCRIPT]
        )

        card_ts = factories.AgileCardFactory(
            status=AgileCard.READY,
            recruit_project=None,
            content_item=content_item,
            flavours=[TYPESCRIPT],
            assignees=[SocialProfileFactory().user],
        )

        card_js = factories.AgileCardFactory(
            status=AgileCard.READY,
            recruit_project=None,
            content_item=content_item,
            flavours=[JAVASCRIPT],
            assignees=[SocialProfileFactory().user],
        )

        self.assertIsNone(card_js.recruit_project)

        card_ts.start_project()
        card_js.start_project()

        self.assertNotEqual(card_ts.recruit_project, card_js.recruit_project)

        ts_project_flavours = [o.name for o in card_ts.recruit_project.flavours.all()]
        self.assertEqual(ts_project_flavours, [TYPESCRIPT])

        js_project_flavours = [o.name for o in card_js.recruit_project.flavours.all()]
        self.assertEqual(js_project_flavours, [JAVASCRIPT])

    @mock.patch("social_auth.github_api.Api")
    @mock.patch("git_real.helpers.add_collaborator")
    @mock.patch.object(RecruitProject, "setup_repository")
    @mock.patch("git_real.helpers.get_repo")
    def test_that_if_we_start_different_flavours_of_the_same_card_we_get_seperate_project_instances_REPOSITORY(
        self, get_repo, *_
    ):
        def get_repo_mock(
            github_auth_login="", repo_full_name="", api=None, response404=None
        ):
            return {
                "full_name": f"me/{repo_full_name}",
                "owner": {"login": "me"},
                "ssh_url": f"https://{repo_full_name}.git",
                "private": True,
                "created_at": timezone.now().strftime(GITHUB_DATETIME_FORMAT),
                "archived": False,
            }

        get_repo.side_effect = get_repo_mock
        content_item = factories.ContentItemFactory(
            content_type=ContentItem.PROJECT,
            project_submission_type=ContentItem.REPOSITORY,
            flavours=[TYPESCRIPT, JAVASCRIPT],
        )

        card_js = factories.AgileCardFactory(
            content_item=content_item,
            flavours=[JAVASCRIPT],
            status=AgileCard.READY,
            recruit_project=None,
        )
        card_ts = factories.AgileCardFactory(
            content_item=content_item,
            flavours=[TYPESCRIPT],
            status=AgileCard.READY,
            recruit_project=None,
        )
        assignee = SocialProfileFactory().user
        card_js.assignees.set([assignee])
        card_ts.assignees.set([assignee])

        card_js.start_project()
        card_ts.start_project()

        projects = RecruitProject.objects.filter(recruit_users__in=[assignee])
        self.assertEqual(projects.count(), 2)

        self.assertTrue(card_js.recruit_project.flavours_match([JAVASCRIPT]))
        self.assertTrue(card_ts.recruit_project.flavours_match([TYPESCRIPT]))
        self.assertEqual(
            card_ts.recruit_project.content_item, card_js.recruit_project.content_item
        )

    def test_that_project_submission_type_LINK_leaves_repository_field_null_and_fills_assignees_in_correctly(
        self,
    ):
        card = factories.AgileCardFactory(
            content_item=factories.ContentItemFactory(
                content_type=ContentItem.PROJECT,
                project_submission_type=ContentItem.LINK,
            ),
            status=AgileCard.READY,
            recruit_project=None,
        )
        user = UserFactory()
        card.assignees.set([user])
        card.start_project()

        self.assertIsNone(card.repository)
        self.assertEqual(list(card.assignees.all()), [user])
        self.assertEqual(list(card.recruit_project.recruit_users.all()), [user])

    def create_continue_repo_card(
        self,
        flavours,
        card_flavours,
        assignee,
        reviewer,
        pre_content_item=None,
        content_item=None,
    ):

        pre_content = pre_content_item or factories.ContentItemFactory(
            content_type=ContentItem.PROJECT,
            project_submission_type=ContentItem.REPOSITORY,
            flavours=flavours,
        )
        pre_card = factories.AgileCardFactory(
            content_item=pre_content,
            status=AgileCard.COMPLETE,
            flavours=card_flavours,
            recruit_project=factories.RecruitProjectFactory(
                content_item=pre_content,
                repository=factories.RepositoryFactory(),
            ),
        )
        pre_card.assignees.set([assignee])
        pre_card.recruit_project.recruit_users.set([assignee])

        card = factories.AgileCardFactory(
            content_item=content_item
            or factories.ContentItemFactory(
                content_type=ContentItem.PROJECT,
                project_submission_type=ContentItem.CONTINUE_REPO,
                continue_from_repo=pre_card.content_item,
                flavours=flavours,
            ),
            flavours=card_flavours,
            status=AgileCard.READY,
            recruit_project=None,
        )
        card.requires_cards.add(pre_card)
        card.assignees.set([assignee])
        card.reviewers.set([reviewer])
        return card

    def test_that_if_we_start_different_flavours_of_the_same_card_we_get_seperate_project_instances_LINK(
        self,
    ):
        content_item = factories.ContentItemFactory(
            content_type=ContentItem.PROJECT,
            project_submission_type=ContentItem.LINK,
            flavours=[TYPESCRIPT, JAVASCRIPT],
        )

        card_js = factories.AgileCardFactory(
            content_item=content_item,
            flavours=[JAVASCRIPT],
            status=AgileCard.READY,
            recruit_project=None,
        )
        card_ts = factories.AgileCardFactory(
            content_item=content_item,
            flavours=[TYPESCRIPT],
            status=AgileCard.READY,
            recruit_project=None,
        )
        assignee = UserFactory()
        card_js.assignees.set([assignee])
        card_ts.assignees.set([assignee])

        card_js.start_project()
        card_ts.start_project()

        projects = RecruitProject.objects.filter(recruit_users__in=[assignee])
        self.assertEqual(projects.count(), 2)

        self.assertTrue(card_js.recruit_project.flavours_match([JAVASCRIPT]))
        self.assertTrue(card_ts.recruit_project.flavours_match([TYPESCRIPT]))
        self.assertEqual(
            card_ts.recruit_project.content_item, card_js.recruit_project.content_item
        )
        self.assertIsNone(card_js.recruit_project.repository)

    @mock.patch("social_auth.github_api.Api")
    @mock.patch("git_real.helpers.add_collaborator")
    def test_that_if_we_start_different_flavours_of_the_same_card_we_get_seperate_project_instances_CONTINUE_REPO(
        self, add_collaborator, Api
    ):
        assignee = SocialProfileFactory().user
        reviewer = SocialProfileFactory().user
        card_js = self.create_continue_repo_card(
            flavours=[TYPESCRIPT, JAVASCRIPT],
            card_flavours=[JAVASCRIPT],
            assignee=assignee,
            reviewer=reviewer,
        )

        content_item = card_js.content_item
        pre_content_item = content_item.continue_from_repo

        card_ts = self.create_continue_repo_card(
            flavours=[TYPESCRIPT, JAVASCRIPT],
            card_flavours=[TYPESCRIPT],
            assignee=assignee,
            reviewer=reviewer,
            pre_content_item=pre_content_item,
            content_item=content_item,
        )

        card_js.start_project()
        card_ts.start_project()

        projects = RecruitProject.objects.filter(recruit_users__in=[assignee])
        self.assertEqual(projects.count(), 4)

        self.assertTrue(card_js.recruit_project.flavours_match([JAVASCRIPT]))
        self.assertTrue(card_ts.recruit_project.flavours_match([TYPESCRIPT]))
        self.assertEqual(
            card_ts.recruit_project.content_item, card_js.recruit_project.content_item
        )


class Project_set_due_time_Tests(TestCase):
    def make_topic_card(self):
        self.card = factories.AgileCardFactory(
            content_item=factories.ContentItemFactory(content_type=ContentItem.TOPIC),
            status=AgileCard.READY,
        )
        self.card.assignees.set([UserFactory()])

    def make_project_card(self):
        self.card = factories.AgileCardFactory(
            content_item=factories.ContentItemFactory(
                content_type=ContentItem.PROJECT,
                project_submission_type=ContentItem.LINK,
            ),
            status=AgileCard.READY,
        )
        self.card.assignees.set([UserFactory()])

    def test_set_due_time_on_PROJECT_no_instance(self):
        self.make_project_card()
        self.card.set_due_time(timezone.now())

        self.assertEqual(self.card.status, AgileCard.READY)
        self.assertIsNotNone(self.card.recruit_project.due_time)

    def test_set_due_time_on_TOPIC_no_instance(self):
        self.make_topic_card()
        self.card.set_due_time(timezone.now())
        self.assertEqual(self.card.status, AgileCard.READY)
        self.assertIsNotNone(self.card.topic_progress.due_time)

    def test_set_due_time_on_PROJECT_with_instance(self):
        self.make_project_card()
        self.card.start_project()
        self.card.set_due_time(timezone.now())

        self.assertEqual(self.card.status, AgileCard.IN_PROGRESS)
        self.assertIsNotNone(self.card.recruit_project.due_time)

    def test_set_due_time_on_TOPIC_with_instance(self):
        self.make_topic_card()
        self.card.start_topic()
        self.card.set_due_time(timezone.now())
        self.assertEqual(self.card.status, AgileCard.IN_PROGRESS)
        self.assertIsNotNone(self.card.topic_progress.due_time)


class derive_status_from_project_Tests(TestCase):
    def setUp(self):
        self.project = factories.RecruitProjectFactory(flavours=[JAVASCRIPT])

        trust = factories.ReviewTrustFactory(
            content_item=self.project.content_item, flavours=[JAVASCRIPT]
        )
        self.trusted_user = trust.user

    def set_project_start_time(self):
        self.project.start_time = timezone.now() - timedelta(days=15)
        self.project.save()

    def test_no_reviews_or_review_request(self):
        self.assertEqual(
            AgileCard.derive_status_from_project(self.project), AgileCard.IN_PROGRESS
        )

    def test_trusted_nyc_after_request_for_review(self):
        self.set_project_start_time()
        self.project.request_review(force_timestamp=timezone.now() - timedelta(days=10))
        review = factories.RecruitProjectReviewFactory(
            status=NOT_YET_COMPETENT,
            recruit_project=self.project,
            reviewer_user=self.trusted_user,
        )

        self.assertTrue(review.trusted)

        self.assertEqual(
            AgileCard.derive_status_from_project(self.project),
            AgileCard.REVIEW_FEEDBACK,
        )

    def test_untrusted_nyc_after_request_for_review(self):
        self.set_project_start_time()
        self.project.request_review(force_timestamp=timezone.now() - timedelta(days=10))
        review = factories.RecruitProjectReviewFactory(
            status=NOT_YET_COMPETENT, recruit_project=self.project
        )
        self.assertFalse(review.trusted)

        self.assertEqual(
            AgileCard.derive_status_from_project(self.project),
            AgileCard.REVIEW_FEEDBACK,
        )

    def test_trusted_nyc_before_request_for_review(self):
        self.set_project_start_time()
        self.project.request_review(force_timestamp=timezone.now() + timedelta(days=10))
        review = factories.RecruitProjectReviewFactory(
            status=NOT_YET_COMPETENT,
            recruit_project=self.project,
            reviewer_user=self.trusted_user,
        )
        self.assertTrue(review.trusted)

        self.assertEqual(
            AgileCard.derive_status_from_project(self.project), AgileCard.IN_REVIEW
        )

    def test_untrusted_nyc_before_request_for_review(self):
        self.set_project_start_time()
        self.project.request_review(force_timestamp=timezone.now() + timedelta(days=10))
        review = factories.RecruitProjectReviewFactory(
            status=NOT_YET_COMPETENT,
            recruit_project=self.project,
        )

        self.assertFalse(review.trusted)

        self.assertEqual(
            AgileCard.derive_status_from_project(self.project), AgileCard.IN_REVIEW
        )

    def test_trusted_competent_after_request_for_review(self):
        self.set_project_start_time()
        self.project.request_review(force_timestamp=timezone.now() - timedelta(days=10))
        review = factories.RecruitProjectReviewFactory(
            status=COMPETENT,
            recruit_project=self.project,
            reviewer_user=self.trusted_user,
        )

        self.assertTrue(review.trusted)

        self.assertEqual(
            AgileCard.derive_status_from_project(self.project), AgileCard.COMPLETE
        )

    def test_untrusted_competent_after_request_for_review(self):
        self.set_project_start_time()
        self.project.request_review(force_timestamp=timezone.now() - timedelta(days=10))
        review = factories.RecruitProjectReviewFactory(
            status=COMPETENT, recruit_project=self.project
        )

        self.assertFalse(review.trusted)

        derived = AgileCard.derive_status_from_project(self.project)
        self.assertEqual(derived, AgileCard.IN_REVIEW)


class TopicMovementTestCase(TestCase):
    def setUp(self):
        self.card = factories.AgileCardFactory(
            content_item=factories.ContentItemFactory(content_type=ContentItem.TOPIC),
            status=AgileCard.READY,
        )
        self.card.assignees.set([UserFactory()])

    def test_start(self):
        card = self.card
        card.start_topic()
        self.assertEqual(card.status, AgileCard.IN_PROGRESS)
        self.assertEqual(card.topic_progress.user, card.assignees.first())
        self.assertEqual(card.topic_progress.content_item, card.content_item)
        self.assertIsNone(card.topic_progress.complete_time)
        self.assertIsNotNone(card.topic_progress.start_time)

    def test_stop(self):
        self.card.start_topic()
        self.card.stop_topic()

        self.assertEqual(self.card.status, AgileCard.READY)
        self.assertIsNotNone(self.card.topic_progress)
        self.assertIsNone(self.card.topic_progress.start_time)

    def test_finish(self):
        self.card.start_topic()
        self.card.finish_topic()

        self.assertEqual(self.card.status, AgileCard.COMPLETE)
        self.assertEqual(self.card.topic_progress.user, self.card.assignees.first())
        self.assertEqual(self.card.topic_progress.content_item, self.card.content_item)
        self.assertIsNotNone(self.card.topic_progress.complete_time)
        self.assertIsNotNone(self.card.topic_progress.start_time)
        self.assertIsNone(self.card.topic_progress.review_request_time)

    def test_finish_when_review_needed(self):
        content_item = self.card.content_item
        content_item.topic_needs_review = True
        content_item.save()

        self.card.start_topic()
        self.card.finish_topic()

        self.assertIsNone(self.card.topic_progress.complete_time)
        self.assertIsNotNone(self.card.topic_progress.review_request_time)
        self.assertIsNotNone(self.card.topic_progress.start_time)
        self.assertEqual(self.card.status, AgileCard.IN_REVIEW)

    def test_start_topic_when_due_date_already_set(self):
        self.card.set_due_time(timezone.now())

        self.card.start_topic()
        self.assertEqual(self.card.status, AgileCard.IN_PROGRESS)
        self.assertEqual(self.card.topic_progress.user, self.card.assignees.first())
        self.assertEqual(self.card.topic_progress.content_item, self.card.content_item)
        self.assertIsNone(self.card.topic_progress.complete_time)
        self.assertIsNotNone(self.card.topic_progress.start_time)

    def test_add_COMPETENT_review(self):

        self.card.content_item.topic_needs_review = True
        self.card.content_item.save()
        self.card.start_topic()
        self.card.finish_topic()

        self.assertEqual(self.card.status, AgileCard.IN_REVIEW)

        review = TopicReview.objects.create(
            status=COMPETENT,
            topic_progress=self.card.topic_progress,
            reviewer_user=UserFactory(),
        )
        self.card.refresh_from_db()
        self.assertEqual(self.card.status, AgileCard.COMPLETE)

    def test_add_NOT_YET_COMPETENT_review(self):
        self.card.content_item.topic_needs_review = True
        self.card.content_item.save()
        self.card.start_topic()
        self.card.finish_topic()

        self.assertEqual(self.card.status, AgileCard.IN_REVIEW)

        review = TopicReview.objects.create(
            status=NOT_YET_COMPETENT,
            topic_progress=self.card.topic_progress,
            reviewer_user=UserFactory(),
        )
        self.card.refresh_from_db()
        self.assertEqual(self.card.status, AgileCard.REVIEW_FEEDBACK)

    def test_add_EXCELLENT_review(self):
        self.card.content_item.topic_needs_review = True
        self.card.content_item.save()
        self.card.start_topic()
        self.card.finish_topic()

        self.assertEqual(self.card.status, AgileCard.IN_REVIEW)

        review = TopicReview.objects.create(
            status=EXCELLENT,
            topic_progress=self.card.topic_progress,
            reviewer_user=UserFactory(),
        )
        self.card.refresh_from_db()
        self.assertEqual(self.card.status, AgileCard.COMPLETE)

    def test_add_RED_FLAG_review(self):
        self.card.content_item.topic_needs_review = True
        self.card.content_item.save()
        self.card.start_topic()
        self.card.finish_topic()

        self.assertEqual(self.card.status, AgileCard.IN_REVIEW)

        review = TopicReview.objects.create(
            status=RED_FLAG,
            topic_progress=self.card.topic_progress,
            reviewer_user=UserFactory(),
        )
        self.card.refresh_from_db()
        self.assertEqual(self.card.status, AgileCard.REVIEW_FEEDBACK)

    def test_that_start_topic_cant_make_duplicates(self):
        content_item = self.card.content_item
        content_item.topic_needs_review = True
        content_item.save()

        get_count = lambda: TopicProgress.objects.filter(
            content_item=content_item, user=self.card.assignees.first()
        ).count()
        topic_progress_count = get_count()

        self.assertEqual(topic_progress_count, 0)
        self.card.start_topic()

        topic_progress_count = get_count()

        self.assertEqual(topic_progress_count, 1)

        self.card.status = AgileCard.READY
        self.card.start_topic()

        topic_progress_count = get_count()
        self.assertEqual(topic_progress_count, 1)


class WorkshopMovementTests(TestCase):
    def setUp(self):
        self.card = factories.AgileCardFactory(
            content_item=factories.ContentItemFactory(
                content_type=ContentItem.WORKSHOP
            ),
            status=AgileCard.READY,
        )
        self.card.assignees.set([UserFactory()])

    def test_attend_workshop(self):
        self.card.attended_workshop(timezone.now())
        self.assertEqual(self.card.status, AgileCard.COMPLETE)
        self.assertIsNotNone(self.card.workshop_attendance)

    def test_cancel_workshop_attendance(self):
        self.card.attended_workshop(timezone.now())
        self.card.delete_workshop_attendance()
        self.assertIsNone(self.card.workshop_attendance)
        self.assertEqual(WorkshopAttendance.objects.count(), 0)
        self.assertEqual(self.card.status, AgileCard.READY)
