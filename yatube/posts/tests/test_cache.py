from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from ..models import Post


User = get_user_model()


class TaskURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.no_user_name = 'noUserName'
        cls.user = User.objects.create_user(username=cls.no_user_name)
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()

    def test_cache_index_page(self):
        content = self.guest_client.get(reverse('posts:index')).content
        Post.objects.filter(id=self.post.id).delete()
        content_cache = self.guest_client.get(reverse('posts:index')).content
        self.assertEqual(content, content_cache, 'Не работает cache страницы')
