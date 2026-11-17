import secrets
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from authentication.models import Profile, RoleChoices, TechChoices


def demo_profiles():
    roles = [
        (f"coordinator{number}", "Coordinator", number, RoleChoices.COORDINATOR, None)
        for number in range(1, 4)
    ]
    developer_types = (
        ("backend", TechChoices.BACKEND),
        ("frontend", TechChoices.FRONTEND),
        ("fullstack", TechChoices.FULLSTACK),
        ("ui_ux", TechChoices.UI_UX),
    )
    developers = [
        (f"{prefix}_developer{number}", prefix.replace("_", " ").title(), number,
         RoleChoices.DEVELOPER, tech)
        for prefix, tech in developer_types
        for number in range(1, 4)
    ]
    return roles + developers


class Command(BaseCommand):
    help = "Create 15 demo profiles and write their generated passwords to a local credentials file."

    def add_arguments(self, parser):
        default_path = Path(__file__).resolve().parents[2] / "credentials.txt"
        parser.add_argument(
            "--credentials-file",
            default=str(default_path),
            help="Path for the plaintext credentials file (default: authentication/credentials.txt).",
        )

    def handle(self, *args, **options):
        profiles = demo_profiles()
        usernames = [profile[0] for profile in profiles]
        existing_usernames = list(
            Profile.objects.filter(username__in=usernames).values_list("username", flat=True)
        )
        if existing_usernames:
            raise CommandError(
                "Refusing to overwrite existing demo accounts: "
                + ", ".join(sorted(existing_usernames))
            )

        credentials = [
            (profile, secrets.token_urlsafe(24))
            for profile in profiles
        ]
        credentials_path = Path(options["credentials_file"])
        credential_file = "".join(
            f"username={username} | role={role} | "
            f"tech={tech or 'N/A'} | password={password}\n"
            for (username, _first_name, _number, role, tech), password in credentials
        )

        with transaction.atomic():
            for (username, first_name, number, role, tech), password in credentials:
                Profile.objects.create_user(
                    username=username,
                    password=password,
                    first_name=first_name,
                    last_name=str(number),
                    email=f"{username}@example.invalid",
                    role=role,
                    tech=tech,
                )

        try:
            credentials_path.write_text(credential_file, encoding="utf-8")
        except OSError as exc:
            raise CommandError(
                f"Profiles were created, but credentials could not be written to "
                f"{credentials_path}: {exc}"
            ) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(credentials)} profiles. Credentials saved to {credentials_path}."
            )
        )
