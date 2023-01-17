from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from posts.models import Post, User


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
        )

    def test_cache_index_page(self):
        """тест для проверки кеширования главной страницы"""
        response = self.authorized_client.get(reverse('posts:index'))
        cache_content = response.content
        Post.objects.all().delete()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(cache_content, response.content)
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        self.assertNotEqual(cache_content, response.content)
