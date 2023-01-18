from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Post(models.Model):
    text = models.TextField('Текст поста', help_text='Введите текст поста')
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        db_index=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        "Group",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ('-pub_date',)
        default_related_name = 'posts'
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:15]


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=100)
    description = models.TextField(max_length=400)

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name='Пост c комментарием'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name='Автор комментария',
    )
    text = models.TextField(
        verbose_name='Текст',
        help_text='Текст нового комментария'
    )
    created = models.DateTimeField(
        verbose_name='Дата комментария',
        auto_now_add=True
    )

    class Meta:
        ordering = ('-created',)
        default_related_name = 'comments'

    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(User, related_name='follower',
                             on_delete=models.CASCADE,
                             verbose_name='Подписчик')
    author = models.ForeignKey(User, related_name='following',
                               on_delete=models.CASCADE,
                               verbose_name='Автор')
