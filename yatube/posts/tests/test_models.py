from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import FIRST_SYMB_IN_POST, Group, Post

User = get_user_model()
CHECK_CUT_SYMBS_IN_POST = 10


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
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

    def test_models_have_correct_object_names(self):
        """Корректность работы __str__ моделей."""
        post = PostModelTest.post
        expected_object_name = post.text[:FIRST_SYMB_IN_POST]
        self.assertEqual(expected_object_name, str(post))
        group = PostModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))
