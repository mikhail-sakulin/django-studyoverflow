import pytest

from posts.models import Comment, Like, LowercaseTag


@pytest.mark.django_db
class TestLowercaseTagModel:
    def test_tag_name_normalization_on_save(self, mocker):
        """Имя тега нормализуется при сохранении."""
        mock_norm = mocker.patch("posts.models.normalize_tag_name", return_value="django")
        tag = LowercaseTag.objects.create(name="  Django  ")

        mock_norm.assert_called_once_with("  Django  ")
        assert tag.name == "django"


@pytest.mark.django_db
class TestPostModel:
    def test_slug_generated_on_creation(self, post_factory, mocker):
        """Slug генерируется автоматически только при создании поста."""
        mock_gen_slug = mocker.patch("posts.models.generate_slug", return_value="test-title")
        post = post_factory(title="Test Title", slug="")

        mock_gen_slug.assert_called_once()
        assert post.slug == "test-title"

    def test_markdown_rendered_only_when_content_changes(self, post_factory, mocker):
        """Markdown рендерится только при создании или изменении контента."""
        mock_render = mocker.patch("posts.models.render_markdown_safe", return_value="<p>HTML</p>")

        # Создание поста — вызывается рендер
        post = post_factory(content="Initial content")
        assert mock_render.call_count == 1

        # Изменение не-content поля — рендер не вызывается повторно
        post.title = "New Title Test"
        post.save()
        assert mock_render.call_count == 1

        # Изменение content — вызывается рендер
        post.content = "New content"
        post.save()
        assert mock_render.call_count == 2


@pytest.mark.django_db
class TestCommentModelAndQuerySet:
    def test_roots_and_children_queryset(self, post_factory, comment_factory):
        """Фильтрация корневых и дочерних комментариев через CommentQuerySet."""
        post = post_factory()
        root = comment_factory(post=post, parent_comment=None)
        child = comment_factory(post=post, parent_comment=root)

        roots = Comment.objects.roots()
        children = Comment.objects.children()

        assert root in roots and child not in roots
        assert child in children and root not in children


@pytest.mark.django_db
class TestLikeManager:
    def test_is_liked_helper(self, user_factory, post_factory, like_factory):
        """Проверка метода is_liked менеджера LikeManager."""
        user = user_factory()
        post = post_factory()

        assert Like.objects.is_liked(user, post) is False

        like_factory(user=user, content_object=post)
        assert Like.objects.is_liked(user, post) is True
