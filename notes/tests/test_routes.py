# news/tests/test_routes.py
# Импортируем класс HTTPStatus.
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note


User = get_user_model()


class TestRoutes(TestCase):
    """Тестирует маршрутизацию приложения."""

    @classmethod
    def setUpTestData(cls):
        """Подготавливает данные для тестирования."""
        # Создаём двух пользователей с разными именами:
        cls.author = User.objects.create(username="Автор заметки")
        cls.reader = User.objects.create(username="Пользователь")
        # От имени одного пользователя (автора) создаём заметку:
        cls.note = Note.objects.create(
            title="Заголовок",
            text="Текст",
            author=cls.author,
        )

    def test_pages_availability(self):
        """Проверяет доступность страниц."""
        anon = "anonymous_user"
        auth = "authorization_user"
        urls_user = (
            # Страницы для всех пользователей.
            ("notes:home", anon),
            ("users:login", anon),
            ("users:logout", anon),
            ("users:signup", anon),
            # Страницы только для авторизованных пользователей.
            ("notes:list", auth),
            ("notes:add", auth),
            ("notes:success", auth),
        )
        for name, status in urls_user:
            if status == auth:
                self.client.force_login(self.reader)
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_notes_edit_and_delete(self):
        """Проверяет доступность страниц автору и пользователю."""
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in (
                "notes:detail",
                "notes:edit",
                "notes:delete",
            ):
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        """Проверяет переадресацию страниц для анонимных пользователей."""
        login_url = reverse("users:login")
        slug = (self.note.slug,)
        for name, args in (
            ("notes:detail", slug),
            ("notes:edit", slug),
            ("notes:delete", slug),
            ("notes:list", None),
            ("notes:add", None),
            ("notes:success", None),
        ):
            with self.subTest(name=name):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
