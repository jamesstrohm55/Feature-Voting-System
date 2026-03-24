"""
Replace the Voter model with Django's built-in User model.

This migration:
1. Drops the Vote table (has FK to both Voter and FeatureRequest)
2. Drops the Voter table
3. Removes the old author FK on FeatureRequest
4. Adds new author FK pointing to auth.User
5. Recreates Vote table with user FK instead of voter FK
6. Re-adds constraints

Existing seed data will be lost — re-run `seed_demo --flush` after migrating.
"""

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("features", "0003_add_status_to_featurerequest"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 1. Drop Vote table (depends on both Voter and FeatureRequest)
        migrations.DeleteModel(name="Vote"),
        # 2. Drop Voter model
        migrations.DeleteModel(name="Voter"),
        # 3. Remove old author FK
        migrations.RemoveField(model_name="featurerequest", name="author"),
        # 4. Add new author FK to auth.User
        migrations.AddField(
            model_name="featurerequest",
            name="author",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="feature_requests",
                to=settings.AUTH_USER_MODEL,
            ),
            preserve_default=False,
        ),
        # 5. Recreate Vote with user FK
        migrations.CreateModel(
            name="Vote",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("feature_request", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="votes", to="features.featurerequest")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="votes", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        # 6. Add unique constraint
        migrations.AddConstraint(
            model_name="vote",
            constraint=models.UniqueConstraint(
                fields=["user", "feature_request"],
                name="unique_vote_per_user_per_feature",
            ),
        ),
    ]
