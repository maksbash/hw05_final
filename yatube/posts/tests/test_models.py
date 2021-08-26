from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names_post(self):
        post = PostModelTest.post
        self.assertEqual(
            str(post)[:15],
            'Тестовый пост',
            'Неправильно работает метов __str__ у post')

    def test_models_have_correct_object_names_group(self):
        group = PostModelTest.group
        self.assertEqual(
            str(group),
            'Тестовая группа',
            'Неправильно работает метод __str__ у group')

    def test_verbose_name(self):
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expectedValue in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name,
                    expectedValue,
                    f'Ошибка в verbose_name поля {field}')

    def test_help_text(self):
        post = PostModelTest.post
        field_verboses = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу',
        }
        for field, expectedValue in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text,
                    expectedValue,
                    f'Ошибка в help_text поля {field}')
