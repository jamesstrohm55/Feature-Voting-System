import threading
import unittest

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TransactionTestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from .models import FeatureRequest, Vote


def _using_sqlite():
    return "sqlite" in settings.DATABASES["default"]["ENGINE"]


def _make_user(username=None, password="testpass123"):
    """Create a user with a unique username and return (user, token)."""
    if username is None:
        import uuid
        username = f"user-{uuid.uuid4().hex[:8]}"
    user = User.objects.create_user(username=username, password=password)
    token, _ = Token.objects.get_or_create(user=user)
    return user, token


def _auth_header(token):
    """Return the HTTP_AUTHORIZATION kwarg for APIClient."""
    return {"HTTP_AUTHORIZATION": f"Token {token.key}"}


class VoteIntegrityTests(APITestCase):

    def setUp(self):
        self.client = APIClient()
        from django.core.cache import cache
        cache.clear()
        self.author, self.author_token = _make_user()
        self.feature = FeatureRequest.objects.create(
            title="Test feature",
            description="A feature created for testing purposes.",
            author=self.author,
        )

    def _vote(self, feature_id, token):
        return self.client.post(
            f"/api/features/{feature_id}/vote/",
            **_auth_header(token),
        )

    def _unvote(self, feature_id, token):
        return self.client.delete(
            f"/api/features/{feature_id}/vote/",
            **_auth_header(token),
        )

    def test_duplicate_vote_returns_409(self):
        _, voter_token = _make_user()
        first = self._vote(self.feature.id, voter_token)
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)

        second = self._vote(self.feature.id, voter_token)
        self.assertEqual(second.status_code, status.HTTP_409_CONFLICT)

    def test_self_vote_returns_403(self):
        resp = self._vote(self.feature.id, self.author_token)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_unvote_without_vote_returns_404(self):
        _, voter_token = _make_user()
        resp = self._unvote(self.feature.id, voter_token)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class VoteCountTests(APITestCase):

    def setUp(self):
        self.client = APIClient()
        from django.core.cache import cache
        cache.clear()
        self.author, self.author_token = _make_user()
        self.feature = FeatureRequest.objects.create(
            title="Count feature",
            description="A feature for vote-count testing.",
            author=self.author,
        )

    def _vote(self, feature_id, token):
        return self.client.post(
            f"/api/features/{feature_id}/vote/",
            **_auth_header(token),
        )

    def _unvote(self, feature_id, token):
        return self.client.delete(
            f"/api/features/{feature_id}/vote/",
            **_auth_header(token),
        )

    def test_vote_increments_count_to_one(self):
        _, token = _make_user()
        self._vote(self.feature.id, token)
        self.feature.refresh_from_db()
        self.assertEqual(self.feature.vote_count, 1)

    def test_unvote_decrements_count_to_zero(self):
        _, token = _make_user()
        self._vote(self.feature.id, token)
        self._unvote(self.feature.id, token)
        self.feature.refresh_from_db()
        self.assertEqual(self.feature.vote_count, 0)

    def test_two_voters_yields_count_of_two(self):
        _, token_a = _make_user()
        _, token_b = _make_user()
        self._vote(self.feature.id, token_a)
        self._vote(self.feature.id, token_b)
        self.feature.refresh_from_db()
        self.assertEqual(self.feature.vote_count, 2)


class AuthAndSerializerTests(APITestCase):

    def setUp(self):
        self.client = APIClient()
        from django.core.cache import cache
        cache.clear()

    def test_unauthenticated_request_returns_401(self):
        resp = self.client.get("/api/features/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_register_and_login(self):
        # Register
        resp = self.client.post(
            "/api/auth/register/",
            data={"username": "newuser", "password": "pass1234"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("token", resp.data)
        self.assertEqual(resp.data["username"], "newuser")

        # Login with same credentials
        resp = self.client.post(
            "/api/auth/login/",
            data={"username": "newuser", "password": "pass1234"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("token", resp.data)

    def test_duplicate_register_returns_409(self):
        self.client.post(
            "/api/auth/register/",
            data={"username": "taken", "password": "pass1234"},
            format="json",
        )
        resp = self.client.post(
            "/api/auth/register/",
            data={"username": "taken", "password": "pass1234"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)

    def test_login_bad_password_returns_401(self):
        self.client.post(
            "/api/auth/register/",
            data={"username": "user1", "password": "pass1234"},
            format="json",
        )
        resp = self.client.post(
            "/api/auth/login/",
            data={"username": "user1", "password": "wrongpass"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_author_set_from_token_not_request_body(self):
        user, token = _make_user()
        resp = self.client.post(
            "/api/features/",
            data={
                "title": "Legit feature",
                "description": "This description is long enough to pass validation.",
                "author": 9999,
            },
            format="json",
            **_auth_header(token),
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["author_username"], user.username)

        feature = FeatureRequest.objects.get(id=resp.data["id"])
        self.assertEqual(feature.author, user)

    def test_injected_vote_count_is_ignored(self):
        _, token = _make_user()
        resp = self.client.post(
            "/api/features/",
            data={
                "title": "Another feature",
                "description": "Description that is definitely long enough.",
                "vote_count": 9999,
            },
            format="json",
            **_auth_header(token),
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        feature = FeatureRequest.objects.get(id=resp.data["id"])
        self.assertEqual(feature.vote_count, 0)

    def test_feature_create_throttled_after_5(self):
        _, token = _make_user()
        for i in range(5):
            resp = self.client.post(
                "/api/features/",
                data={
                    "title": f"Feature {i}",
                    "description": "This description is long enough to pass validation.",
                },
                format="json",
                **_auth_header(token),
            )
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        resp = self.client.post(
            "/api/features/",
            data={
                "title": "Feature 6",
                "description": "This description is long enough to pass validation.",
            },
            format="json",
            **_auth_header(token),
        )
        self.assertEqual(resp.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn("Rate limit exceeded", resp.data["detail"])

    def test_vote_throttled_after_30(self):
        _, voter_token = _make_user()
        author, _ = _make_user()

        features = [
            FeatureRequest.objects.create(
                title=f"Votable {i}",
                description="Long enough description for validation.",
                author=author,
            )
            for i in range(31)
        ]

        for i in range(30):
            resp = self.client.post(
                f"/api/features/{features[i].id}/vote/",
                **_auth_header(voter_token),
            )
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED, f"Vote {i} failed")

        resp = self.client.post(
            f"/api/features/{features[30].id}/vote/",
            **_auth_header(voter_token),
        )
        self.assertEqual(resp.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn("Rate limit exceeded", resp.data["detail"])


class RankingTests(APITestCase):

    def setUp(self):
        self.client = APIClient()
        from django.core.cache import cache
        cache.clear()
        self.viewer, self.viewer_token = _make_user()

    def _make_feature(self, title, vote_count=0):
        author, _ = _make_user()
        return FeatureRequest.objects.create(
            title=title,
            description=f"Description for {title} is long enough.",
            author=author,
            vote_count=vote_count,
        )

    def _add_votes(self, feature, count):
        for _ in range(count):
            user, _ = _make_user()
            Vote.objects.create(user=user, feature_request=feature)

    def _list_ids(self):
        resp = self.client.get(
            "/api/features/",
            **_auth_header(self.viewer_token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        return [f["id"] for f in resp.data]

    def test_ordered_by_vote_count_descending(self):
        fa = self._make_feature("A")
        fb = self._make_feature("B")
        fc = self._make_feature("C")

        self._add_votes(fa, 3)
        self._add_votes(fb, 1)
        self._add_votes(fc, 2)

        FeatureRequest.objects.filter(pk=fa.pk).update(vote_count=3)
        FeatureRequest.objects.filter(pk=fb.pk).update(vote_count=1)
        FeatureRequest.objects.filter(pk=fc.pk).update(vote_count=2)

        ids = self._list_ids()
        self.assertEqual(ids, [str(fa.id), str(fc.id), str(fb.id)])

    def test_tiebreaker_is_most_recent_first(self):
        f_old = self._make_feature("Old")
        f_new = self._make_feature("New")

        ids = self._list_ids()
        self.assertEqual(ids[0], str(f_new.id))
        self.assertEqual(ids[1], str(f_old.id))

    def _search_ids(self, query):
        resp = self.client.get(
            "/api/features/",
            {"search": query},
            **_auth_header(self.viewer_token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        return [f["id"] for f in resp.data]

    def test_search_filters_by_title(self):
        self._make_feature("Dark mode support")
        fb = self._make_feature("Export to CSV")

        ids = self._search_ids("csv")
        self.assertEqual(ids, [str(fb.id)])

    def test_search_filters_by_description(self):
        author, _ = _make_user()
        fa = FeatureRequest.objects.create(
            title="Alpha",
            description="Integrate with Slack for notifications.",
            author=author,
        )
        FeatureRequest.objects.create(
            title="Beta",
            description="Generic description that is long enough.",
            author=author,
        )

        ids = self._search_ids("slack")
        self.assertEqual(ids, [str(fa.id)])

    def test_search_preserves_ranking(self):
        fa = self._make_feature("Dark mode widget")
        fb = self._make_feature("Dark mode toggle")
        FeatureRequest.objects.filter(pk=fa.pk).update(vote_count=1)
        FeatureRequest.objects.filter(pk=fb.pk).update(vote_count=5)

        ids = self._search_ids("dark mode")
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
    """Prove the UniqueConstraint catches a true concurrent double-vote."""

    def setUp(self):
        self.author, _ = _make_user()
        self.feature = FeatureRequest.objects.create(
            title="Race feature",
            description="A feature for race-condition testing.",
            author=self.author,
        )
        self.voter, self.voter_token = _make_user()

    def test_concurrent_duplicate_vote_creates_exactly_one(self):
        barrier = threading.Barrier(2, timeout=5)
        results: list[int] = []

        def fire():
            from django.db import connection

            client = APIClient()
            barrier.wait()
            resp = client.post(
                f"/api/features/{self.feature.id}/vote/",
                **_auth_header(self.voter_token),
            )
            results.append(resp.status_code)
            connection.close()

        t1 = threading.Thread(target=fire)
        t2 = threading.Thread(target=fire)
        t1.start()
        t2.start()
        t1.join(timeout=10)
        t2.join(timeout=10)

        self.assertCountEqual(results, [201, 409])
        self.assertEqual(
            Vote.objects.filter(feature_request=self.feature).count(), 1
        )
        self.feature.refresh_from_db()
        self.assertEqual(self.feature.vote_count, 1)
