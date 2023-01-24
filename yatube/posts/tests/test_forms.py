import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
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
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
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

    def test_post_create_new_db(self):
        """Валидная форма создает запись"""
        posts_count = Post.objects.count()
        small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                     b'\x01\x00\x80\x00\x00\x00\x00\x00'
                     b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                     b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                     b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                     b'\x0A\x00\x3B')
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый пост Тестовый пост',
            'group': self.group.pk,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post = Post.objects.latest('id')
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group.pk, form_data['group'])
        self.assertEqual(post.image.name.split('/')[1],
                         form_data['image'].name)

    def test_post_edit_change_db(self):
        """Происходит изменение поста с post_id в базе данных"""
        self.post = Post.objects.create(
            text='Текст поста для post_edit',
            author=self.user_author,
            group=PostFormTest.group,
        )
        self.another_group = Group.objects.create(
            title='Другая тестовая группа',
            slug='test_slug_2',
            description='Всё переплетено, но не предопределено',
        )
        form_data = {
            'text': 'Обновленный пост',
            'group': self.another_group.pk,
        }
        response = self.author_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={'post_id': self.post.pk}
            )
        )
        post = Post.objects.latest('id')
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.user_author)
        self.assertEqual(post.group.pk, form_data['group'])

    def test_comments_can_create_only_auth(self):
        """Комментировать посты может только авторизованный пользователь.
        после успешной отправки комментарий появляется на странице поста."""
        count_comments = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий'
        }
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), count_comments)
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), count_comments + 1)
        comment = Comment.objects.latest('id')
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.post, PostFormTest.post)
        self.assertEqual(comment.author, PostFormTest.user)
