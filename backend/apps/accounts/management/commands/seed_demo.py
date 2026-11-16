from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import Brand, Profile
from apps.integrations.services import run_sync

User = get_user_model()


class Command(BaseCommand):
    help = "Create (or refresh) the demo brand and user, then run a marketplace sync. Safe to run repeatedly."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="demo")
        parser.add_argument("--password", default="shelfsense-demo")
        parser.add_argument("--brand", default="Evergreen Home")

    def handle(self, *args, **opts):
        with transaction.atomic():
            brand, _ = Brand.objects.get_or_create(name=opts["brand"], defaults={"slug": "evergreen-home"})
            user, created = User.objects.get_or_create(username=opts["username"])
            if created:
                user.set_password(opts["password"])
                user.save()
            Profile.objects.update_or_create(user=user, defaults={"brand": brand, "role": Profile.Role.OWNER})

        job = run_sync(brand, triggered_by=user)
        self.stdout.write(
            self.style.SUCCESS(
                f"Demo ready: login '{opts['username']}' / '{opts['password']}' — sync {job.status}, "
                f"{job.products_upserted} products, {job.metrics_upserted} metric rows, "
                f"{job.recommendations_created} new recommendations."
            )
        )
