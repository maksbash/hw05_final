from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from ..models import Comment, Group, Post
from yatube.settings import MAX_POST_ON_PAGE


User = get_user_model()


class PostPageTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.no_user_name = 'noUserName'
        cls.no_user_name_first = 'User'
        cls.no_user_name_last = 'Name'
        cls.test_slug = 'test-slug'
        cls.default_post_id = 1

        cls.user = User.objects.create_user(
            username=cls.no_user_name,
            first_name=cls.no_user_name_first,
            last_name=cls.no_user_name_last)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=cls.test_slug,
            description='Тестовое описание',
        )

        for index in range(1, MAX_POST_ON_PAGE * 2):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост {index}',
                group=cls.group
            )

    def setUp(self):
        self.no_user_name = self.no_user_name
        self.guest_client = Client()
        self.authorized_client = Client()
        user = User.objects.get(username=self.no_user_name)
        self.authorized_client.force_login(user)
        cache.clear()

    def test_pages_uses_correct_template(self):

        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.default_post_id}):
                    'posts/post_detail.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.no_user_name}): 'posts/profile.html',
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.test_slug}): 'posts/group_list.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.default_post_id}):
                    'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:follow_index'): 'posts/follow.html'
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_contains_right_count_of_posts_on_pages_with_paginator(self):
        reverse_names = [
            reverse('posts:index'),
            reverse(
                'posts:profile', kwargs={'username': self.no_user_name}),
            reverse(
                'posts:group_posts', kwargs={'slug': self.test_slug})]
        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                response_page2 = self.authorized_client.get(
                    reverse_name + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']), int(MAX_POST_ON_PAGE))
                self.assertEqual(
                    len(response_page2.context['page_obj']),
                    int(MAX_POST_ON_PAGE) - 1)

    def test_context_index_page(self):
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context['page_obj'][0]
        self.assertEqual(
            post.text, f'Тестовый пост {MAX_POST_ON_PAGE * 2 - 1}')
        self.assertEqual(post.author.username, self.no_user_name)
        self.assertEqual(post.group.title, self.group.title)
        self.assertEqual(post.group.description, self.group.description)
        self.assertEqual(post.group.slug, self.test_slug)
        self.assertIsNotNone(post.pub_date)

    def test_context_post_detail_page(self):
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.default_post_id}))
        title = response.context['title']
        count_of_posts = response.context['count_of_posts']
        post = response.context['post']
        self.assertEqual(title, 'Пост Тестовый пост 1')
        self.assertEqual(count_of_posts, MAX_POST_ON_PAGE * 2 - 1)
        self.assertEqual(post.text, 'Тестовый пост 1')

    def test_context_group_post_page(self):
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.no_user_name}))
        title = response.context['title']
        count_of_posts = response.context['count_of_posts']
        author = response.context['author']
        self.assertEqual(
            title,
            (f'Профайл пользователя {self.no_user_name_first} '
                f'{self.no_user_name_last}'))
        self.assertEqual(count_of_posts, MAX_POST_ON_PAGE * 2 - 1)
        self.assertEqual(author.username, self.no_user_name)

    def test_context_profile_page(self):
        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': self.test_slug}))
        title = response.context['title']
        group = response.context['group']
        self.assertEqual(title, f'Записи сообщества {self.group.title}')
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.description, self.group.description)
        self.assertEqual(group.slug, self.test_slug)

    def test_context_create_post_page(self):
        response = self.authorized_client.get(
            reverse('posts:post_create'))
        form = response.context['form']
        is_edit = response.context['is_edit']
        groups = response.context['groups']

        self.assertFalse(is_edit)
        self.assertEqual(len(groups), 1)
        self.assertIsInstance(form.fields.get('text'), forms.fields.CharField)
        self.assertIsInstance(
            form.fields.get('group'), forms.fields.ChoiceField)

    def test_context_edit_post_page(self):
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.default_post_id}))
        form = response.context['form']
        user_name = response.context['username']
        is_edit = response.context['is_edit']
        groups = response.context['groups']

        self.assertTrue(is_edit)
        self.assertEqual(len(groups), 1)
        self.assertEqual(user_name.username, self.no_user_name)
        self.assertIsInstance(form.fields.get('text'), forms.fields.CharField)
        self.assertIsInstance(
            form.fields.get('group'), forms.fields.ChoiceField)


class PostPageWithImageAndCommentTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.no_user_name = 'noUserName'
        cls.comment_user_name = 'CommentUserName'
        cls.test_slug = 'test-slug'
        cls.comment_text = 'Тестовый комментарий'

        cls.user = User.objects.create_user(
            username=cls.no_user_name)
        cls.comment_user = User.objects.create_user(
            username=cls.comment_user_name)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=cls.test_slug,
        )

        test_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='test_gif.gif',
            content=test_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост с картинкой',
            group=cls.group,
            image=uploaded
        )

        cls.comment = Comment.objects.create(
            text=cls.comment_text,
            post=cls.post,
            author=cls.comment_user
        )

    def setUp(self):
        self.authorized_client = Client()
        user = User.objects.get(username=self.no_user_name)
        self.authorized_client.force_login(user)

        self.comment_client = Client()
        comment_user = User.objects.get(username=self.comment_user_name)
        self.comment_client.force_login(comment_user)
        cache.clear()

    def test_context_image_pages(self):
        reverse_names = {
            reverse('posts:index'): 'page_obj',
            reverse(
                'posts:profile',
                kwargs={'username': self.no_user_name}):
                    'page_obj',
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.test_slug}):
                    'page_obj',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}):
                    'post'
        }

        for reverse_name, obj in reverse_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                post = response.context[obj]
                if not obj == 'post':
                    post = post[0]
                self.assertIsNotNone(
                    post.image, f'Нет картинке на странице {reverse_name}')

    def test_context_comment(self):
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id})
        )
        comment = response.context['comments'].first()
        self.assertIsNotNone(comment, 'Нет комментария')
        self.assertEqual(comment, self.comment)


class PostsFollowTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.username_create_posts = 'userPostCreator'
        cls.username_follower = 'userFollower'
        cls.text_of_post = 'Тестовый пост для подписок'
        cls.url_profile = reverse(
            'posts:profile',
            kwargs={'username': cls.username_create_posts})
        cls.url_follow = reverse(
            'posts:profile_follow',
            kwargs={'username': cls.username_create_posts})
        cls.url_unfollow = reverse(
            'posts:profile_unfollow',
            kwargs={'username': cls.username_create_posts})

        cls.user_create_posts = User.objects.create_user(
            username=cls.username_create_posts)
        cls.user_follower = User.objects.create_user(
            username=cls.username_follower)

        cls.post = Post.objects.create(
            author=cls.user_create_posts,
            text=cls.text_of_post,
        )

    def setUp(self):
        self.client_post_creator = Client()
        user_posts_creator = User.objects.get(
            username=self.username_create_posts)
        self.client_post_creator.force_login(user_posts_creator)

        self.client_follower = Client()
        user_follower = User.objects.get(
            username=self.username_follower)
        self.client_follower.force_login(user_follower)
        cache.clear()

    def test_user_follow_unfollow_redirect(self):
        response = self.client_follower.post(self.url_follow, follow=True)
        self.assertRedirects(response, self.url_profile)
        response = self.client_follower.post(self.url_unfollow, follow=True)
        self.assertRedirects(response, self.url_profile)

    def test_context_follo_page(self):
        self.client_follower.post(self.url_follow)
        response = self.client_follower.get(reverse('posts:follow_index'))
        post = response.context['page_obj'][0]
        self.assertEqual(
            post.text,
            self.text_of_post,
            'Подписка не работает')
        self.client_follower.post(self.url_unfollow)
        response = self.client_follower.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)
