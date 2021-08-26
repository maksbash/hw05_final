# from typing import Text
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.cache import cache

from http import HTTPStatus

from ..models import Group, Post


User = get_user_model()


class TaskURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.no_user_name = 'noUserName'
        cls.test_slug = 'test-slug'

        cls.url_index = '/'
        cls.url_group_slag = f'/group/{cls.test_slug }/'
        cls.url_profile_noUserName = f'/profile/{cls.no_user_name}/'
        cls.url_post1 = '/posts/1/'
        cls.url_post1_edit = '/posts/1/edit/'
        cls.url_create = '/create/'

        cls.user = User.objects.create_user(username=cls.no_user_name)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=cls.test_slug,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        user = User.objects.get(username=self.no_user_name)
        self.authorized_client.force_login(user)
        cache.clear()

    def test_unauthorized_pages(self):
        url_names = [
            self.url_index,
            self.url_group_slag,
            self.url_profile_noUserName,
            self.url_post1
        ]
        for url in url_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f'Недоступна страница {url}')

    def test_unexisting_page(self):
        response = self.guest_client.get('unexist-page')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post_edit_url_redirect_anonymous_on_login_page(self):
        url_names = [
            self.url_post1_edit,
            self.url_create
        ]
        for url in url_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(
                    response, f'/auth/login/?next={url}'
                )

    def test_authorized_client_pages(self):
        url_names = [
            self.url_post1_edit,
            self.url_create
        ]
        for url in url_names:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    'Для авторизованного пользователя'
                    f' недоступна страница {url}')

    def test_urls_posts_correct_templates(self):
        templates_url_names = {
            self.url_index: 'posts/index.html',
            self.url_group_slag: 'posts/group_list.html',
            self.url_profile_noUserName: 'posts/profile.html',
            self.url_post1: 'posts/post_detail.html',
            self.url_post1_edit: 'posts/create_post.html',
            self.url_create: 'posts/create_post.html'
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(
                    response,
                    template,
                    f'Шаблон {template} не соответствует адресу {adress}')
