from datetime import datetime
import tempfile
import shutil

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from http import HTTPStatus

from ..models import Group, Post, Comment, Follow
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.user = User.objects.create_user(username='testnick')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            id=11111,
            group=cls.group,
            image=uploaded,
        )
        cls.templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': cls.group.slug}): (
                'posts/group_list.html'
            ),
            reverse('posts:profile', kwargs={'username': cls.post.author}): (
                'posts/profile.html'
            ),
            reverse('posts:post_detail', kwargs={'post_id': cls.post.id}): (
                'posts/post_detail.html'
            ),
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('posts:post_edit', kwargs={'post_id': cls.post.id}): (
                'posts/post_create.html'
            )
        }
        cls.author = Client()
        cls.author.force_login(cls.user)
        cls.guest_client = Client()

        cache.clear()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_views_use_correct_template_guest(self):
        """Проверка namespaces"""
        for namespace, template in self.templates_pages_names.items():
            with self.subTest(template):
                response = self.author.get(namespace)
                self.assertTemplateUsed(response, template)
                response = self.guest_client.get(reverse('posts:post_create'))
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_correct_context_in_create_or_edit(self):
        """Шаблоны создания и редактирования поста сформированы с правильным
        контекстом."""
        form_urls = (
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for url in form_urls:
            with self.subTest(value=url):
                response = self.author.get(url)
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context['form'].fields[value]
                        self.assertIsInstance(form_field, expected)

    def test_index_context_is_posts_list(self):
        """На главную страницу передаётся спиcок постов"""
        response = self.guest_client.get(reverse("posts:index"))
        response_post = response.context.get('page_obj').object_list[0]
        post_image = response_post.image
        self.assertEqual(
            len(response.context.get("page_obj")), 1, "Это не список"
        )
        self.assertEqual(post_image, self.post.image)

    def test_created_post_with_selected_group_on_right_pages(self):
        """Созданный пост с группой показан на нужных страницах."""
        group = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-2',
            description='Тестовое описание 2'
        )
        post = Post.objects.create(
            author=self.user,
            text='Тестовый текст поста 2',
            id=999,
            group=group,
        )
        urls = (
            reverse('posts:index'),
            reverse(
                'posts:profile',
                kwargs={'username': post.author.username}
            ),
            reverse('posts:group_list', kwargs={'slug': group.slug}))
        for url in urls:
            with self.subTest(value=url):
                response = self.author.get(url)
                self.assertIn(post, response.context['page_obj'])
        other_group_response = self.author.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertNotIn(post, other_group_response.context['page_obj'])

    def test_created_post_not_in_other_group(self):
        """Созданный пост не должен попасть в чужую группу"""
        Group.objects.create(
            title="another group",
            slug="another_group_slug",
            description="another group description",
        )
        response = self.guest_client.get(
            reverse("posts:group_list", kwargs={"slug": "another_group_slug"})
        )
        another_group_post_list = response.context.get("page_obj").object_list
        self.assertFalse(self.post in another_group_post_list)

    def test_index_cache(self):
        """Тест работы кэширования"""
        Post.objects.create(
            text='new-post-with-cache',
            author=self.user,
            group=self.group,
        )
        response = self.guest_client.get('/')
        page = response.content.decode()
        self.assertNotIn('new-post-with-cache', page)
        cache.clear()
        response = self.guest_client.get('/')
        page = response.content.decode()
        self.assertIn('new-post-with-cache', page)


class PaginatorViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super(PaginatorViewsTests, cls).setUpClass()
        cls.user = User.objects.create_user(username="HasNoName")
        cls.group = Group.objects.create(
            title="Test group",
            slug="test_group_slug",
            description="Test group description",
        )
        cls.posts = [Post(author=cls.user,
                     group=cls.group,
                     pub_date=timezone.now(),
                     text='Тестовый текст' + str(i)) for i in range(13)]
        Post.objects.bulk_create(cls.posts)
        cls.guest_client = Client()

    def test_first_page_contains_ten_records(self):
        """Paginator | index: На первой странице 10 постов"""
        response = self.guest_client.get(reverse("posts:index"))
        self.assertEqual(len(response.context["page_obj"]), 10)

    def test_second_page_contains_three_records(self):
        """Paginator  |  index: на второй странице 3 поста"""
        response = self.guest_client.get(reverse("posts:index") + "?page=2")
        self.assertEqual(len(response.context["page_obj"]), 3)

    def test_group_list_contains_ten_records(self):
        """Paginator  |  group_list: На первой странице 10 постов"""
        response = self.guest_client.get(
            reverse("posts:group_list", kwargs={"slug": self.group.slug})
        )
        self.assertEqual(len(response.context["page_obj"]), 10, "Не десять!")

    def test_group_list_second_page_contains_three_records(self):
        """Paginator  |  group_list: На второй странице 3 поста"""
        response = self.guest_client.get(
            reverse("posts:group_list", kwargs={"slug": self.group.slug})
            + "?page=2"
        )
        self.assertEqual(len(response.context["page_obj"]), 3, "Не три!")


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class CommentViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.author = User.objects.create_user(username='author')
        cls.guest_client = Client()
        cls.autorized_client = Client()
        cls.autorized_client.force_login(cls.user)
        cls.autorized_author = Client()
        cls.autorized_author.force_login(cls.user)

        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.author,
            pub_date=datetime.now(),
        )
        cls.comment = Comment.objects.create(
            text='Тестовый коммент',
            author=cls.author,
            post=cls.post
        )

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_autorized_client_can_comment(self):
        """Авторизованный юзер может комментить"""
        self.autorized_client.post(reverse(
            'posts:add_comment',
            kwargs={'post_id': self.post.id}
        ),
            {'text': 'Тестовый комментарий', },
            follow=True
        )
        response = self.autorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id}
        ),
        )
        self.assertContains(response, 'Тестовый комментарий')

    def test_guest_cant_comment(self):
        """Неавторизованный юзер не может комментить"""
        self.guest_client.post(reverse(
            'posts:add_comment',
            kwargs={'post_id': self.post.id}
        ),
            {'text': '2 Тестовый комментарий 2', },
            follow=True
        )
        response = self.guest_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id}
        ),
        )
        self.assertNotContains(response, 'Тестовый комментарий 2')

    def test_comment_shown_in_post_deatail(self):
        """После отправки коммент виден на странице поста"""
        response = self.autorized_author.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertIn(self.comment, response.context['comments'])


class FollowViewTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user_author = User.objects.create(username='user_author')
        cls.user_follower = User.objects.create(username='user_follower')

        cls.guest_client = Client()
        cls.autorized_author = Client()
        cls.autorized_follower = Client()

        cls.autorized_author.force_login(cls.user_author)
        cls.autorized_follower.force_login(cls.user_follower)

        cls.group = Group.objects.create(
            title='test title 1',
            slug='test_slug_1',
            description='test description 1'
        )
        cls.post = Post.objects.create(
            text='Test text',
            author=cls.user_author,
            group=cls.group
        )

    def test_autorized_follow(self):
        """Авторизованный пользователь может подписаться"""
        self.autorized_follower.get(reverse('posts:profile_follow', kwargs={
                                    'username': self.user_author}))
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_guest_cant_follow(self):
        """Гость не может подписаться"""
        self.guest_client.get(reverse('posts:profile_follow', kwargs={
                              'username': self.user_author}))
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_unfollow(self):
        """Авторизованный пользователь может отписаться"""
        self.autorized_follower.get(
            reverse('posts:profile_unfollow', kwargs={
                    'username': self.user_author}))
        self.guest_client.get(reverse('posts:profile_unfollow', kwargs={
                              'username': self.user_author}))
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_new_post_in_feed_follower(self):
        Follow.objects.create(
            author=self.user_author,
            user=self.user_follower
        )
        response = self.autorized_follower.get('/follow/')
        response = self.autorized_follower.get('/follow/')
        post_text_1 = response.context['page_obj'][0].text
        self.assertEqual(post_text_1, self.post.text)
        response = self.autorized_author.get('/follow/')
        self.assertNotContains(response, self.post.text)
