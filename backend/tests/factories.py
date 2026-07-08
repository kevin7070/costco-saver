"""factory_boy factories for tests."""

import factory
from factory.django import DjangoModelFactory

from apps.users.models import User, UserType


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    user_type = UserType.USER
    is_active = True
    email_verified = True

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if not create:
            return
        self.set_password(extracted or "testpass123")
        self.save()
