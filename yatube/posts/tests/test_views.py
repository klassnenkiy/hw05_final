import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_author = User.objects.create_user(username='user_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
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
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.user_author)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group', kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.post.author}):
            'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.pk}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.pk}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                cache.clear()
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        self.assertIn('page_obj', response.context)
        self.assertEqual(len(response.context['page_obj'].object_list), 1)
        first_post = response.context['page_obj'][0]
        self.assertEqual(first_post, self.post)
        self.assertEqual(first_post.text, self.post.text)
        self.assertEqual(first_post.author, self.post.author)
        self.assertEqual(first_post.group, self.group)
        self.assertEqual(first_post.image, self.post.image)

    def test_group_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:group', kwargs={'slug': self.group.slug})
        )
        self.assertIn('group', response.context)
        self.assertEqual(response.context['group'], self.group)
        self.assertIn('page_obj', response.context)
        self.assertEqual(len(response.context['page_obj'].object_list), 1)
        first_post = response.context['page_obj'][0]
        self.assertEqual(first_post.text, self.post.text)
        self.assertEqual(first_post.author, self.post.author)
        self.assertEqual(first_post.image, self.post.image)

    def test_profile_show_correct_context(self):
        """Страница profile формируется с корректным контекстом."""
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': self.post.author})
        )
        self.assertIn('author', response.context)
        self.assertEqual(response.context['author'], self.user)
        self.assertIn('page_obj', response.context)
        self.assertEqual(len(response.context['page_obj'].object_list), 1)
        first_post = response.context['page_obj'][0]
        self.assertEqual(first_post.text, self.post.text)
        self.assertEqual(first_post.group, self.post.group)
        self.assertEqual(first_post.pk, self.post.pk)
        self.assertEqual(first_post.image, self.post.image)

    def test_post_detail_show_correct_context(self):
        """Страница post_detail формируется с корректным контекстом."""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        post_object = response.context['post']
        self.assertEqual(post_object, self.post)
        self.assertEqual(post_object.author, self.post.author)
        self.assertEqual(post_object.group, self.post.group)
        self.assertEqual(post_object.pk, self.post.pk)
        self.assertEqual(post_object.image, self.post.image)

    def test_create_n_post_edit_show_correct_context(self):
        """Страницы create и post_edit формируются с корректным контекстом."""
        post_edit = reverse('posts:post_edit',
                            kwargs={'post_id': self.post.pk})
        response_edit = self.authorized_client.get(post_edit)
        self.assertEqual(response_edit.context['post'], self.post)
        self.assertTrue(response_edit.context.get('is_edit'))
        urls = [post_edit, reverse('posts:post_create')]
        for url in urls:
            response = self.authorized_client.get(url)
            form_fields = {
                'text': forms.fields.CharField,
                'group': forms.models.ModelChoiceField,
                'image': forms.fields.ImageField
            }
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context['form'].fields[value]
                    self.assertIsInstance(form_field, expected)
                    self.assertIn('form', response.context)

    def test_new_post_not_in_group_list(self):
        """Новый пост не попал в группу, для которой не был предназначен"""
        another_group = Group.objects.create(
            title='Другая тестовая группа',
            slug='test_slug_2',
            description='С Наступающим Новым Годом!',
        )
        response = self.author_client.get(
            reverse(
                'posts:group', kwargs={'slug': another_group.slug}
            )
        )
        self.assertNotIn(self.post, response.context['page_obj'])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        NUMBER_POSTS = 13
        cls.user = User.objects.create_user(username='auth')
        cls.user_author = User.objects.create_user(username='user_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',)
        cls.posts = Post.objects.bulk_create(
            Post(
                text=f'Тестовый пост номер {i}',
                author=cls.user,
                group=cls.group
            )
            for i in range(NUMBER_POSTS)
        )

    def setUp(self):
        self.guest_client = Client()

    def test_pages_contains_ten_n_three_records(self):
        """Проверка: количество постов на первой странице равно 10
        на второй странице должно быть три поста"""
        urls = [
            reverse(
                'posts:index'
            ),
            reverse(
                'posts:group', kwargs={'slug': self.group.slug}
            ),
            reverse(
                'posts:profile', kwargs={'username': self.user}
            ),
        ]
        pages_posts = [
            (1, 10),
            (2, 3)
        ]
        for url in urls:
            for page, expected_amount in pages_posts:
                with self.subTest(url=url, page=page):
                    self.assertEqual(len(self.guest_client.get(
                        url + '?page=' + str(page)).context.get('page_obj')),
                        expected_amount)
