import factory
import faker
from django.contrib.auth import get_user_model

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = 'username',

    username = factory.LazyFunction(lambda: faker.Faker().user_name()[:16])
    email = factory.LazyFunction(lambda: faker.Faker().email())
    password = factory.LazyFunction(lambda: faker.Faker().password())
