from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus
from ..models import Group, Post
from django.core.cache import cache

User = get_user_model()


class PostUrlTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testnick')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group_id=cls.group.id
        )
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.author = Client()
        cls.author.force_login(cls.user)

    def test_everyone_pages(self):
        """Страницы доступные для всех пользователей"""
        everyone_pages = (
            '/',
            '/group/test-slug/',
            '/profile/testnick/',
            '/posts/1/',
        )
        for page in everyone_pages:
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_guest_redirects(self):
        """Редирект гостя при попытке зайти на недопустимые страницы"""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, ('/auth/login/?next=/create/'))

        response = self.guest_client.get(
            '/profile/testnick/follow/', follow=True)
        self.assertRedirects(
            response, ('/auth/login/?next=/profile/testnick/follow/'))

        response = self.guest_client.get(
            '/profile/testnick/unfollow/', follow=True)
        self.assertRedirects(
            response, ('/auth/login/?next=/profile/testnick/unfollow/'))

        response = self.guest_client.get(
            reverse('posts:add_comment', args=(self.post.id,))
        )
        self.assertRedirects(
            response, ('/auth/login/?next=/posts/1/comment/'))

    def test_edit_post_author_only(self):
        """Редактирование поста доступно только автору"""
        response = self.author.get('/posts/1/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_autorize(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        templates_url_names_autorize = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/create/': 'posts/post_create.html',
            '/posts/1/edit/': 'posts/post_create.html',
            '/posts/1/': 'posts/post_detail.html',
            '/profile/testnick/': 'posts/profile.html',
            '/follow/': 'posts/follow.html',
        }
        for url, template in templates_url_names_autorize.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
        cache.clear()
        templates_url_names_guest = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/posts/1/': 'posts/post_detail.html',
            '/profile/testnick/': 'posts/profile.html',
        }
        for url, template in templates_url_names_guest.items():
            with self.subTest(template=template):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_follow_autorized_redirects(self):
        """Редирект авторизованного пользователя
        на /profile/ при подписке/отписке
        """
        response = self.authorized_client.get(
            '/profile/testnick/follow/', follow=True)
        response = self.authorized_client.get(
            '/profile/testnick/unfollow/', follow=True)
        self.assertRedirects(response, ('/profile/testnick/'))

    def test_comment_autorized_redirect(self):
        """Редирект авторизованного пользователя
        на /post_detail/ при комментировании
        """
        response = self.authorized_client.get(
            reverse('posts:add_comment', args=(self.post.id,)))
        self.assertRedirects(response, ('/posts/1/'))
