import io

import pytest
from PIL import Image
from users.services import (
    generate_gif,
    generate_image,
    generate_static_image,
)


def create_static_image(size=(400, 400), fmt: str | None = "PNG", mode="RGB"):
    """Создает тестовую статическую картинку."""
    image = Image.new(mode, size, color="red")
    image.format = fmt
    return image


def create_gif(size=(300, 300), frames=3):
    """Создает тестовую гифку."""
    images = [
        Image.new("RGBA", size, color="red" if frame % 2 == 0 else "green")
        for frame in range(frames)
    ]

    buffer = io.BytesIO()

    images[0].save(
        buffer,
        format="GIF",
        save_all=True,
        append_images=images[1:],
        duration=120,
        loop=0,
    )

    buffer.seek(0)

    return Image.open(buffer)


class TestGenerateImage:
    @pytest.mark.parametrize(
        "create_image_or_gif_func, ext, expected_format, expected_animated",
        [
            (create_static_image, "", "PNG", False),
            (create_static_image, ".jpeg", "JPEG", False),
            (create_static_image, ".jpg", "JPEG", False),
            (create_static_image, ".gif", "GIF", False),
            (create_gif, ".gif", "GIF", True),
        ],
    )
    def test_routing_and_formats(
        self, create_image_or_gif_func, ext, expected_format, expected_animated
    ):
        image = create_image_or_gif_func()

        result = generate_image(image, ext, (100, 100))

        result.seek(0)
        generated = Image.open(result)

        assert generated.format == expected_format
        assert getattr(generated, "is_animated", False) == expected_animated


class TestGenerateStaticImage:
    @pytest.mark.parametrize(
        "fmt, mode",
        [
            ("PNG", "RGBA"),
            ("JPEG", "RGB"),
            ("WEBP", "RGB"),
        ],
    )
    def test_correct_format_and_resizes(self, fmt, mode):
        image = create_static_image(fmt=fmt, mode=mode)
        buffer = io.BytesIO()

        generate_static_image(image, fmt, buffer, (100, 100))
        buffer.seek(0)
        generated = Image.open(buffer)

        assert generated.format == fmt
        assert generated.width <= 100
        assert generated.height <= 100


class TestGenerateGif:
    def test_generate_and_resize_gif(self):
        gif = create_gif(frames=5)
        buffer = io.BytesIO()

        generate_gif(gif, buffer, (100, 100))
        buffer.seek(0)
        generated = Image.open(buffer)

        assert getattr(generated, "is_animated", False)
        assert getattr(generated, "n_frames", 1) == 5
        assert generated.width <= 100
        assert generated.height <= 100

    def test_limits_frames_to_100(self):
        gif = create_gif(frames=105)
        buffer = io.BytesIO()

        generate_gif(gif, buffer, (100, 100))
        buffer.seek(0)
        generated = Image.open(buffer)

        assert getattr(generated, "n_frames", 1) == 100
