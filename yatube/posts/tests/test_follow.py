from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from posts.models import Follow, Post, User


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_author = User.objects.create_user(
            username='post_author',
        )
        cls.follower = User.objects.create_user(
            username='follower',
        )
        cls.post = Post.objects.create(
            text='тестовый пост',
            author=cls.post_author,
        )

    def setUp(self):
        cache.clear()
        self.author_client = Client()
        self.author_client.force_login(self.follower)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.post_author)

    def test_auth_can_follow(self):
        """Авторизованный пользователь может подписываться на других"""
        count_follow = Follow.objects.count()
        self.authorized_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.follower}))
        follow = Follow.objects.latest('id')
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertEqual(follow.author.id, self.follower.id)
        self.assertEqual(follow.user.id, self.post_author.id)

    def test_auth_can_unfollow(self):
        """Авторизованный пользователь может удалять их из подписок."""
        Follow.objects.create(
            user=self.post_author,
            author=self.follower)
        count_follow = Follow.objects.count()
        self.authorized_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.follower}))
        self.assertEqual(Follow.objects.count(), count_follow - 1)

    def test_new_post_follower(self):
        """Новая запись пользователя появляется в ленте подписчиков"""
        post = Post.objects.create(
            author=self.post_author,
            text='новый тестовый пост')
        Follow.objects.create(
            user=self.follower,
            author=self.post_author)
        response = self.author_client.get(
            reverse('posts:follow_index'))
        self.assertIn(post, response.context['page_obj'])

    def test_new_post_unfollower(self):
        """не появляется в ленте тех, кто не подписан"""
        post = Post.objects.create(
            author=self.post_author,
            text='новый тестовый пост')
        response = self.author_client.get(
            reverse('posts:follow_index'))
        self.assertNotIn(post, response.context['page_obj'])
