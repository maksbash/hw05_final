import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from yatube.settings import BASE_DIR

from ..models import Group, Post


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPageTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.no_user_name = 'noUserName'
        cls.user = User.objects.create_user(
            username=cls.no_user_name, first_name='User', last_name='Name')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',)
        test_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='test_gif.gif',
            content=test_gif,
            content_type='image/gif')
        cls.post = Post.objects.create(
            text='Тестовый пост 1',
            group=cls.group,
            author=cls.user)

    def setUp(self):
        self.authorized_client = Client()
        user = User.objects.get(username=self.no_user_name)
        self.authorized_client.force_login(user)
        self.unauthorised_client = Client()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_unauthorized_client_create_page(self):
        form_data = {
            'text': 'Тестовый пост неавторизованного пользователя',
            'group': self.group.id
        }

        response = self.unauthorised_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        redirect_address = reverse('users:login')
        next_address = reverse('posts:post_create')
        self.assertRedirects(
            response, f'{redirect_address}?next={next_address}')

    def test_form_create_post_page(self):
        form_data = {
            'text': 'Тестовый пост create_post',
            'group': self.group.id,
            'image': self.uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.no_user_name}))

        post = Post.objects.filter(text=form_data['text'])
        self.assertEqual(
            post.count(), 1, 'Создано более одного поста')
        post = post.first()
        self.assertEqual(
            post.text,
            form_data['text'],
            'Неверный текст у поста')
        self.assertEqual(
            post.group.title, self.group.title, 'Неверная группа у поста')
        self.assertEqual(
            post.author.username, self.no_user_name, 'Неверный автор у поста')
        self.assertEqual(
            post.image, 'posts/test_gif.gif', 'Неверная картинка у поста')

    def test_form_post_edit_page(self):
        form_data = {
            'text': 'Тестовый пост edit_page',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.group.id}),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.group.id}))
        post = Post.objects.filter(text=form_data['text'])
        self.assertEqual(
            post.count(), 1, 'Создано более одного поста')
        post = post.first()
        self.assertEqual(
            post.text, form_data['text'], 'Неверный текст у поста')
        self.assertEqual(
            post.group.title, self.group.title, 'Неверная группа у поста')
        self.assertEqual(
            post.author.username,
            self.no_user_name,
            'Неверный автор у поста')

    def test_form_add_comment(self):
        form_data = {
            'text': 'Добавленный тестовый коммент',
            'author': self.user
        }
        url = reverse(
            'posts:add_comment',
            kwargs={'post_id': self.post.id})

        response = self.authorized_client.post(
            url,
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))

        comment = response.context['comments'].first()
        self.assertEqual(
            comment.text, form_data['text'], 'Неверный текст у комментария')
        self.assertEqual(
            comment.author.username,
            self.no_user_name,
            'Неверный автор у комментария')

    def test_unauthorized_client_create_comment(self):
        form_data = {
            'text': 'Добавленный тестовый коммент',
            'author': self.user
        }
        url = reverse(
            'posts:add_comment',
            kwargs={'post_id': self.post.id})

        response = self.unauthorised_client.post(
            url,
            data=form_data,
            follow=True
        )
        redirect_address = reverse('users:login')
        self.assertRedirects(
            response, f'{redirect_address}?next={url}')
