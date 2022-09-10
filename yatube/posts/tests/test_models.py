from multiprocessing.connection import Client
from tabnanny import verbose
from turtle import title
from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import FIRST_SYMB_IN_POST, Group, Post, Comment, Follow

User = get_user_model()
CHECK_CUT_SYMBS_IN_POST = 10


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.user_2 = User.objects.create_user(username='user')
        # cls.author = Client()
        # cls.author.force_login
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост' * CHECK_CUT_SYMBS_IN_POST,
            group=cls.group
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text='Текст комментария',
        )
        cls.follow = Follow.objects.create(
            author=cls.user,
            user=cls.user_2,
        )

    def test_models_have_correct_object_names(self):
        """Корректность работы __str__ моделей."""
        post = PostModelTest.post
        expected_object_name = post.text[:FIRST_SYMB_IN_POST]
        self.assertEqual(expected_object_name, str(post))
        group = PostModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))
        comment = PostModelTest.comment
        expected_object_name = comment.text
        self.assertEqual(expected_object_name, str(comment))
        follow = PostModelTest.follow
        expected_object_name = follow.user.username
        self.assertEqual(expected_object_name, str(follow))
