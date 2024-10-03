import factory
import faker
from django.contrib.auth import get_user_model

from posts.models import Post, Comment

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = 'username',

    username = factory.LazyFunction(lambda: faker.Faker().user_name()[:16])
    email = factory.LazyFunction(lambda: faker.Faker().email())
    password = factory.LazyFunction(lambda: faker.Faker().password())


class PostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Post

    signature = factory.LazyFunction(lambda: faker.Faker().user_name())


class CommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Comment

    comment = factory.LazyFunction(lambda: faker.Faker().text(max_nb_chars=1024))
