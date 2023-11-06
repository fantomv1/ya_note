from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from notes.models import Note


User = get_user_model()


class TestListNotes(TestCase):
    NUMBER_OF_NOTES = 10
    LIST_URL = reverse("notes:list")

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username="Автор заметки")
        all_notes = [
            Note(
                title=f"Заметка{index}",
                text="Просто текст.",
                author=cls.author,
                slug=f"test{index}",
            )
            for index in range(cls.NUMBER_OF_NOTES)
        ]
        Note.objects.bulk_create(all_notes)

    def test_notes_order(self):
        self.client.force_login(self.author)
        response = self.client.get(self.LIST_URL)
        object_list = response.context["object_list"]
        # Получаем даты заметок в том порядке, как они выведены на странице.
        all_dates = [news.id for news in object_list]
        # Сортируем полученный список по возрастанию.
        sorted_dates = sorted(all_dates,)
        # Проверяем, что исходный список был отсортирован правильно.
        self.assertEqual(all_dates, sorted_dates)
