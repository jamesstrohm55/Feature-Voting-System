import threading
import unittest
import uuid

from django.conf import settings
from django.test import TransactionTestCase
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from .models import FeatureRequest, Vote, Voter


def _using_sqlite():
    return "sqlite" in settings.DATABASES["default"]["ENGINE"]


class VoteIntegrityTests(APITestCase):

    def setUp(self):
        self.client = APIClient()
        # Author who owns the seeded feature — a distinct voter.
        self.author_session = self._make_session_id()
        self.feature = self._seed_feature(self.author_session)

    # ── helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _make_session_id() -> str:
        return str(uuid.uuid4())

    def _seed_feature(self, author_session: str) -> FeatureRequest:
        author, _ = Voter.objects.get_or_create(session_id=author_session)
        return FeatureRequest.objects.create(
            title="Test feature",
            description="A feature created for testing purposes.",
            author=author,
        )

    def _vote(self, feature_id: uuid.UUID, session: str):
        return self.client.post(
            f"/api/features/{feature_id}/vote/",
            HTTP_X_SESSION_ID=session,
        )

    def _unvote(self, feature_id: uuid.UUID, session: str):
        return self.client.delete(
            f"/api/features/{feature_id}/vote/",
            HTTP_X_SESSION_ID=session,
        )

    # ── tests ─────────────────────────────────────────────────────────────

    def test_duplicate_vote_returns_409(self):
        voter_session = self._make_session_id()

        first = self._vote(self.feature.id, voter_session)
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)

        second = self._vote(self.feature.id, voter_session)
        self.assertEqual(second.status_code, status.HTTP_409_CONFLICT)

    def test_self_vote_returns_403(self):
        resp = self._vote(self.feature.id, self.author_session)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_unvote_without_vote_returns_404(self):
        voter_session = self._make_session_id()

        resp = self._unvote(self.feature.id, voter_session)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class VoteCountTests(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.author_session = self._make_session_id()
        self.feature = self._seed_feature(self.author_session)

    # ── helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _make_session_id() -> str:
        return str(uuid.uuid4())

    def _seed_feature(self, author_session: str) -> FeatureRequest:
        author, _ = Voter.objects.get_or_create(session_id=author_session)
        return FeatureRequest.objects.create(
            title="Count feature",
            description="A feature for vote-count testing.",
            author=author,
        )

    def _vote(self, feature_id: uuid.UUID, session: str):
        return self.client.post(
            f"/api/features/{feature_id}/vote/",
            HTTP_X_SESSION_ID=session,
        )

    def _unvote(self, feature_id: uuid.UUID, session: str):
        return self.client.delete(
            f"/api/features/{feature_id}/vote/",
            HTTP_X_SESSION_ID=session,
        )

    # ── tests ─────────────────────────────────────────────────────────────

    def test_vote_increments_count_to_one(self):
        voter = self._make_session_id()
        self._vote(self.feature.id, voter)

        self.feature.refresh_from_db()
        self.assertEqual(self.feature.vote_count, 1)

    def test_unvote_decrements_count_to_zero(self):
        voter = self._make_session_id()
        self._vote(self.feature.id, voter)
        self._unvote(self.feature.id, voter)

        self.feature.refresh_from_db()
        self.assertEqual(self.feature.vote_count, 0)

    def test_two_voters_yields_count_of_two(self):
        voter_a = self._make_session_id()
        voter_b = self._make_session_id()
        self._vote(self.feature.id, voter_a)
        self._vote(self.feature.id, voter_b)

        self.feature.refresh_from_db()
        self.assertEqual(self.feature.vote_count, 2)


class MiddlewareAndSerializerTests(APITestCase):

    def setUp(self):
        self.client = APIClient()

    @staticmethod
    def _make_session_id() -> str:
        return str(uuid.uuid4())

    # ── middleware rejection tests ────────────────────────────────────────

    def test_missing_session_header_returns_401(self):
        resp = self.client.get("/api/features/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_malformed_session_header_returns_400(self):
        resp = self.client.get(
            "/api/features/",
            HTTP_X_SESSION_ID="not-a-uuid",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # ── serializer ignores spoofed fields ────────────────────────────────

    def test_author_set_from_session_not_request_body(self):
        session = self._make_session_id()
        spoofed_author = str(uuid.uuid4())

        resp = self.client.post(
            "/api/features/",
            data={
                "title": "Legit feature",
                "description": "This description is long enough to pass validation.",
                "author": spoofed_author,
            },
            format="json",
            HTTP_X_SESSION_ID=session,
        )

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["author_session_id"], session)

        feature = FeatureRequest.objects.get(id=resp.data["id"])
        self.assertEqual(feature.author.session_id, session)

    def test_injected_vote_count_is_ignored(self):
        session = self._make_session_id()

        resp = self.client.post(
            "/api/features/",
            data={
                "title": "Another feature",
                "description": "Description that is definitely long enough.",
                "vote_count": 9999,
            },
            format="json",
            HTTP_X_SESSION_ID=session,
        )

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        feature = FeatureRequest.objects.get(id=resp.data["id"])
        self.assertEqual(feature.vote_count, 0)


class RankingTests(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.viewer_session = str(uuid.uuid4())

    def _make_feature(self, title, vote_count=0):
        """Create a feature with a unique author and a preset vote_count."""
        author = Voter.objects.create(session_id=str(uuid.uuid4()))
        return FeatureRequest.objects.create(
            title=title,
            description=f"Description for {title} is long enough.",
            author=author,
            vote_count=vote_count,
        )

    def _add_votes(self, feature, count):
        """Cast `count` votes from distinct voters."""
        for _ in range(count):
            voter = Voter.objects.create(session_id=str(uuid.uuid4()))
            Vote.objects.create(voter=voter, feature_request=feature)

    def _list_ids(self):
        resp = self.client.get(
            "/api/features/",
            HTTP_X_SESSION_ID=self.viewer_session,
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        return [f["id"] for f in resp.data]

    # ── tests ─────────────────────────────────────────────────────────────

    def test_ordered_by_vote_count_descending(self):
        fa = self._make_feature("A")
        fb = self._make_feature("B")
        fc = self._make_feature("C")

        self._add_votes(fa, 3)
        self._add_votes(fb, 1)
        self._add_votes(fc, 2)

        # Sync the denormalized column with actual vote rows.
        FeatureRequest.objects.filter(pk=fa.pk).update(vote_count=3)
        FeatureRequest.objects.filter(pk=fb.pk).update(vote_count=1)
        FeatureRequest.objects.filter(pk=fc.pk).update(vote_count=2)

        ids = self._list_ids()
        self.assertEqual(ids, [str(fa.id), str(fc.id), str(fb.id)])

    def test_tiebreaker_is_most_recent_first(self):
        # Both features have the same vote_count; the newer one should rank first.
        f_old = self._make_feature("Old")
        f_new = self._make_feature("New")

        ids = self._list_ids()
        self.assertEqual(ids[0], str(f_new.id))
        self.assertEqual(ids[1], str(f_old.id))

    # ── search tests ─────────────────────────────────────────────────────

    def _search_ids(self, query):
        resp = self.client.get(
            "/api/features/",
            {"search": query},
            HTTP_X_SESSION_ID=self.viewer_session,
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        return [f["id"] for f in resp.data]

    def test_search_filters_by_title(self):
        self._make_feature("Dark mode support")
        fb = self._make_feature("Export to CSV")

        ids = self._search_ids("csv")
        self.assertEqual(ids, [str(fb.id)])

    def test_search_filters_by_description(self):
        fa = FeatureRequest.objects.create(
            title="Alpha",
            description="Integrate with Slack for notifications.",
            author=Voter.objects.create(session_id=str(uuid.uuid4())),
        )
        FeatureRequest.objects.create(
            title="Beta",
            description="Generic description that is long enough.",
            author=Voter.objects.create(session_id=str(uuid.uuid4())),
        )

        ids = self._search_ids("slack")
        self.assertEqual(ids, [str(fa.id)])

    def test_search_preserves_ranking(self):
        fa = self._make_feature("Dark mode widget")
        fb = self._make_feature("Dark mode toggle")
        FeatureRequest.objects.filter(pk=fa.pk).update(vote_count=1)
        FeatureRequest.objects.filter(pk=fb.pk).update(vote_count=5)

        ids = self._search_ids("dark mode")
        # fb has more votes, should come first.
        self.assertEqual(ids, [str(fb.id), str(fa.id)])

    def test_empty_search_returns_all(self):
        self._make_feature("One")
        self._make_feature("Two")

        ids_no_param = self._list_ids()
        ids_empty = self._search_ids("")

        self.assertEqual(ids_no_param, ids_empty)


@unittest.skipIf(
    _using_sqlite(),
    "SQLite shared-cache in-memory DB ignores busy_timeout on table-level "
    "locks, so concurrent writes deadlock instantly. This test runs against "
    "Postgres (the production database) where real row-level locking works.",
)
class RaceConditionTests(TransactionTestCase):
    """Prove the UniqueConstraint catches a true concurrent double-vote.

    Requires Postgres — SQLite's in-memory shared-cache mode cannot handle
    simultaneous writes from two threads.  TransactionTestCase is used so
    each thread's writes are actually committed (TestCase wraps the whole
    test in an uncommitted transaction invisible to other connections).
    """

    def setUp(self):
        self.author_session = str(uuid.uuid4())
        author, _ = Voter.objects.get_or_create(session_id=self.author_session)
        self.feature = FeatureRequest.objects.create(
            title="Race feature",
            description="A feature for race-condition testing.",
            author=author,
        )
        # Pre-create the voter so both threads resolve to the same row.
        self.voter_session = str(uuid.uuid4())
        Voter.objects.get_or_create(session_id=self.voter_session)

    def test_concurrent_duplicate_vote_creates_exactly_one(self):
        barrier = threading.Barrier(2, timeout=5)
        results: list[int] = []

        def fire():
            from django.db import connection

            client = APIClient()
            barrier.wait()
            resp = client.post(
                f"/api/features/{self.feature.id}/vote/",
                HTTP_X_SESSION_ID=self.voter_session,
            )
            results.append(resp.status_code)
            connection.close()

        t1 = threading.Thread(target=fire)
        t2 = threading.Thread(target=fire)
        t1.start()
        t2.start()
        t1.join(timeout=10)
        t2.join(timeout=10)

        # Exactly one 201 and one 409, in either order.
        self.assertCountEqual(results, [201, 409])

        # Database state: one Vote row, vote_count == 1.
        self.assertEqual(
            Vote.objects.filter(feature_request=self.feature).count(), 1
        )
        self.feature.refresh_from_db()
        self.assertEqual(self.feature.vote_count, 1)
