"""Seed dev/test accounts — idempotent.

LOCAL / DEV ONLY. These are throwaway credentials; never use them in production.

Run inside the web container's Django shell (stdin):

    docker compose exec -T web python manage.py shell < backend/scripts/seed_dev.py

Or flush + re-seed in one go with scripts/reset-dev.sh.
"""

from apps.users.models import User

# (email, password, first_name, last_name)
ADMIN = ("test@costco.local", "TestPass123!", "Test", "User")
REGULAR_USERS = [
    ("user@costco.local", "UserPass123!", "Alice", "Wong"),
    ("user2@costco.local", "UserPass123!", "Bob", "Chan"),
    ("user3@costco.local", "UserPass123!", "Carol", "Lee"),
]


def _seed(email, password, first_name, last_name, *, admin=False):
    defaults = {"first_name": first_name, "last_name": last_name}
    defaults["user_type"] = "admin" if admin else "user"
    if admin:
        defaults["is_staff"] = True
        defaults["is_superuser"] = True
    user, created = User.objects.get_or_create(email=email, defaults=defaults)
    if created:
        user.set_password(password)
        user.save()
    role = "admin" if admin else "user"
    print(f"{'created' if created else 'exists ':7} {email}  ({role})")


_seed(*ADMIN, admin=True)
for row in REGULAR_USERS:
    _seed(*row)
print("Seed complete.")
