"""
Populate the database with realistic demo data for presentations and reviews.
Idempotent — safe to run multiple times; skips if data already exists.

Usage:
    python manage.py seed_demo
    python manage.py seed_demo --flush   # wipe and re-seed
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from features.models import FeatureRequest, Vote, Voter

# Realistic feature requests for a product feedback board.
SEED_FEATURES = [
    {
        "title": "Dark mode support",
        "description": (
            "Add a system-aware dark mode toggle. Many users work late and the "
            "bright UI causes eye strain. Should respect prefers-color-scheme and "
            "allow manual override."
        ),
        "votes": 14,
    },
    {
        "title": "Export data to CSV",
        "description": (
            "Allow exporting the feature list with vote counts to CSV for product "
            "review meetings. Include title, description, vote count, and submission "
            "date as columns."
        ),
        "votes": 9,
    },
    {
        "title": "Keyboard shortcuts",
        "description": (
            "Power users should be able to navigate and vote using keyboard shortcuts. "
            "J/K to move between features, U to upvote, N to open the new feature form."
        ),
        "votes": 7,
    },
    {
        "title": "Slack integration for new submissions",
        "description": (
            "Post a notification to a configurable Slack channel whenever a new feature "
            "request is submitted. Include the title, description preview, and a link "
            "back to the voting page."
        ),
        "votes": 5,
    },
    {
        "title": "Feature request status labels",
        "description": (
            "Allow admins to tag feature requests with statuses like 'Under Review', "
            "'Planned', 'In Progress', or 'Shipped'. Helps close the feedback loop "
            "with voters."
        ),
        "votes": 4,
    },
    {
        "title": "Markdown support in descriptions",
        "description": (
            "Let users write descriptions with basic Markdown formatting — bold, "
            "italic, code blocks, and bullet lists. Renders inline on the card. "
            "Sanitize output to prevent XSS."
        ),
        "votes": 3,
    },
    {
        "title": "Email digest of top features",
        "description": (
            "Weekly email summarizing the top 10 features by vote count, with deltas "
            "from the previous week. Useful for stakeholders who don't check the board "
            "regularly."
        ),
        "votes": 1,
    },
    {
        "title": "Public API for integrations",
        "description": (
            "Expose a read-only public API so teams can pull feature request data into "
            "their own dashboards or Notion databases. Authenticate with a simple "
            "API key per workspace."
        ),
        "votes": 0,
    },
]


class Command(BaseCommand):
    help = "Seed the database with realistic demo data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete all existing data before seeding.",
        )

    def handle(self, *args, **options):
        if options["flush"]:
            count = FeatureRequest.objects.count()
            Vote.objects.all().delete()
            FeatureRequest.objects.all().delete()
            Voter.objects.all().delete()
            self.stdout.write(f"Flushed {count} features and all related data.")

        if FeatureRequest.objects.exists():
            self.stdout.write(
                self.style.WARNING("Data already exists. Use --flush to re-seed.")
            )
            return

        with transaction.atomic():
            # Create distinct voters — one author per feature, plus a pool of voters.
            authors = [
                Voter.objects.create(session_id=f"seed-author-{i}")
                for i in range(len(SEED_FEATURES))
            ]
            voters = [
                Voter.objects.create(session_id=f"seed-voter-{i}")
                for i in range(20)
            ]

            for i, spec in enumerate(SEED_FEATURES):
                feature = FeatureRequest.objects.create(
                    title=spec["title"],
                    description=spec["description"],
                    author=authors[i],
                    vote_count=spec["votes"],
                )

                # Distribute votes across the voter pool. Each voter votes at most
                # once per feature (enforced by the unique constraint).
                for v in range(spec["votes"]):
                    Vote.objects.create(
                        voter=voters[v % len(voters)],
                        feature_request=feature,
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(SEED_FEATURES)} features with votes."
            )
        )
