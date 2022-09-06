import tempfile
import shutil

from django.conf import settings
from django.urls import reverse
from posts.models import Group, Post
from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='test_user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.user,
            pub_date=date.today(),
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_guest_cant_create_post(self):
        """Гость не может постить"""
        posts_count = Post.objects.all().count()
        response = self.guest_client.post(
            reverse(
                'posts:post_create'),
            data={'text': 'Тестовый пост', 'group': self.group.id},
            follow=True
        )
        self.assertRedirects(response, '/auth/login/?next=/create/')
        self.assertEqual(Post.objects.all().count(), posts_count)

    def test_guest_cant_edit_post(self):
        """Гость не  может редактировать пост"""
        new_post_text = 'Новый текст поста'
        group_2 = Group.objects.create(
            title='Test group',
            slug='new-test-group',
            description='New test discription'
        )
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data={'text': new_post_text, 'group': group_2.id},
            follow=True,
        )
        post_other = Post.objects.get(id=self.post.id)
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotEqual(post_other.text, 'Измененный текст')

    def test_create_post_autorize(self):
        """Авторизованный пользователь может постить"""
        post_count = Post.objects.count()
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
        form_data = {
            'image': uploaded,
            'text': 'Тестовый пост',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse(
                'posts:profile',
                kwargs={'username': self.user}
            )
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group'],
            ).exists()
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post_autorize(self):
        """Авторизованный пользователь может редактировать"""
        post_2 = Post.objects.get(id=self.post.id)
        self.client.get(f'/posts/{self.post.id}/edit/')
        form_data = {
            'text': 'Измененный текст',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        post_2 = Post.objects.get(id=self.post.id)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotEqual(post_2.text, 'Измененный текст2')
