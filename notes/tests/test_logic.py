from http import HTTPStatus
from pytils.translit import slugify

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):
    """Тестирует возможность создания заметки."""

    NOTE_TITLE = "Заголовок заметки"
    NOTE_TEXT = "Текст заметки"

    @classmethod
    def setUpTestData(cls):
        """Подготавливает данные для тестирования."""
        cls.user = User.objects.create(username="Пользователь")
        cls.url = reverse("notes:add")
        cls.redirect_url = reverse("notes:success")
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        # Данные для POST-запроса при создании заметки.
        cls.form_data = {
            "title": cls.NOTE_TITLE,
            "text": cls.NOTE_TEXT
        }

    def test_anonymous_user_cant_create_note(self):
        """Создание заметки анонимным пользователем."""
        self.client.post(self.url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_can_create_note(self):
        """Создание заметки авторизованным пользователем."""
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, self.redirect_url)
        comments_count = Note.objects.count()
        self.assertEqual(comments_count, 1)
        note = Note.objects.get()
        self.assertEqual(note.title, self.NOTE_TITLE)
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.author, self.user)

    def test_user_cant_use_unique_slug(self):
        """Создание не уникального слага"""
        response = self.auth_client.post(self.url, data=self.form_data)
        # Создаём заметку с одикаковым слагом.
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertFormError(
            response,
            form="form",
            field="slug",
            errors=slugify(self.form_data.get("title"))[:100] + WARNING
        )
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)


class TestNoteEditDelete(TestCase):
    """Тестирует возможность редактирования и удаления заметки."""

    NOTE_TITLE = "Заметка"
    NOTE_TEXT = "Просто текст"
    NEW_NOTE_TITLE = "Текст комментария"
    NEW_NOTE_TEXT = "Обновлённый текст"

    @classmethod
    def setUpTestData(cls):
        """Подготавливает данные для тестирования."""
        cls.author = User.objects.create(username="Автор заметки")
        cls.note = Note.objects.create(
            title=cls.NOTE_TITLE,
            text=cls.NOTE_TEXT,
            author=cls.author,
            slug="test",
        )
        cls.redirect_url = reverse("notes:success")
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username="Читатель")
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.edit_url = reverse("notes:edit", args=(cls.note.slug,))
        cls.delete_url = reverse("notes:delete", args=(cls.note.slug,))
        cls.form_data = {
            "title": cls.NEW_NOTE_TITLE,
            "text": cls.NEW_NOTE_TEXT
        }

    def test_author_can_delete_note(self):
        """Удаление заметки автором."""
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.redirect_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_cant_delete_note_of_another_user(self):
        """Удаление заметки другим пользователем."""
        response = self.reader_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_author_can_edit_note(self):
        """Редактирование заметки автором."""
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.redirect_url)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.NEW_NOTE_TITLE)
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)

    def test_user_cant_edit_note_of_another_user(self):
        """Редактирование заметки другим пользователем."""
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.NOTE_TITLE)
        self.assertEqual(self.note.text, self.NOTE_TEXT)
