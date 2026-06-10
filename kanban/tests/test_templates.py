from django.test import TestCase
from django.urls import reverse

from kanban.models import Board, Card, Column


class TemplateTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.board = Board.objects.create(id=1, title="Test Board")
        cls.col_a = Column.objects.create(board=cls.board, title="Col A", order=0)
        cls.col_b = Column.objects.create(board=cls.board, title="Col B", order=1)

    def test_index_template(self):
        response = self.client.get(reverse("templates_index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "kanban/templates/index.html")

    def test_column_move(self):
        # Move Col B to order 0
        response = self.client.post(
            reverse("templates_column_move"),
            {"column_id": self.col_b.pk, "order": 0},
        )
        self.assertEqual(response.status_code, 204)
        self.col_a.refresh_from_db()
        self.col_b.refresh_from_db()
        self.assertEqual(self.col_b.order, 0)
        self.assertEqual(self.col_a.order, 1)

    def test_column_delete(self):
        response = self.client.delete(
            reverse("templates_column_delete", args=[self.col_a.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Column.objects.filter(pk=self.col_a.pk).exists())

    def test_card_delete(self):
        card = Card.objects.create(column=self.col_a, title="Delete Me", order=0)
        response = self.client.delete(reverse("templates_card_delete", args=[card.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Card.objects.filter(pk=card.pk).exists())

    def test_card_create(self):
        response = self.client.post(
            reverse("templates_card_create", args=[self.col_a.pk]),
            {"title": "New Test Card"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "kanban/templates/_card.html")
        new_card = Card.objects.get(title="New Test Card")
        self.assertEqual(new_card.column, self.col_a)
        self.assertEqual(new_card.order, 0)

    def test_column_create(self):
        response = self.client.post(
            reverse("templates_column_create", args=[self.board.pk]),
            {"title": "New Column"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "kanban/templates/_column.html")
        new_col = Column.objects.get(title="New Column")
        self.assertEqual(new_col.board, self.board)
        self.assertEqual(new_col.order, 2)

    def test_column_edit(self):
        response = self.client.post(
            reverse("templates_column_edit", args=[self.col_a.pk]),
            {"title": "Renamed Col A"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "kanban/templates/_column.html")
        self.col_a.refresh_from_db()
        self.assertEqual(self.col_a.title, "Renamed Col A")

    def test_column_create_with_color(self):
        response = self.client.post(
            reverse("templates_column_create", args=[self.board.pk]),
            {"title": "New Green Column", "color": "#10b981"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "kanban/templates/_column.html")
        new_col = Column.objects.get(title="New Green Column")
        self.assertEqual(new_col.board, self.board)
        self.assertEqual(new_col.color, "#10b981")

    def test_column_edit_color(self):
        response = self.client.post(
            reverse("templates_column_edit", args=[self.col_a.pk]),
            {"title": "Col A", "color": "#ec4899"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "kanban/templates/_column.html")
        self.col_a.refresh_from_db()
        self.assertEqual(self.col_a.color, "#ec4899")

    def test_board_edit(self):
        response = self.client.post(
            reverse("templates_board_edit", args=[self.board.pk]),
            {"title": "Renamed Board"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "kanban/templates/_board_title.html")
        self.board.refresh_from_db()
        self.assertEqual(self.board.title, "Renamed Board")

    def test_column_move_invalid(self):
        response = self.client.post(
            reverse("templates_column_move"), {"column_id": "invalid_id", "order": -5}
        )
        self.assertEqual(response.status_code, 400)

    def test_card_create_invalid(self):
        response = self.client.post(
            reverse("templates_card_create", args=[self.col_a.pk]), {"title": ""}
        )
        self.assertEqual(response.status_code, 400)

    def test_column_create_invalid(self):
        response = self.client.post(
            reverse("templates_column_create", args=[self.board.pk]), {"title": ""}
        )
        self.assertEqual(response.status_code, 400)

    def test_column_edit_invalid_empty_fields(self):
        response = self.client.post(
            reverse("templates_column_edit", args=[self.col_a.pk]),
            {"title": "", "color": ""},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode("utf-8"), "No title or color provided")

    def test_board_edit_invalid(self):
        response = self.client.post(
            reverse("templates_board_edit", args=[self.board.pk]),
            {"title": ""},
        )
        self.assertEqual(response.status_code, 400)

    def test_card_edit_get(self):
        card = Card.objects.create(column=self.col_a, title="Original Card", order=0)
        response = self.client.get(reverse("templates_card_edit", args=[card.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "kanban/templates/_card.html")
        self.assertContains(response, "Original Card")

    def test_card_edit_post_success(self):
        card = Card.objects.create(column=self.col_a, title="Original Card", order=0)
        response = self.client.post(
            reverse("templates_card_edit", args=[card.pk]),
            {"title": "Updated Card Title"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "kanban/templates/_card.html")
        card.refresh_from_db()
        self.assertEqual(card.title, "Updated Card Title")

    def test_card_edit_post_invalid(self):
        card = Card.objects.create(column=self.col_a, title="Original Card", order=0)
        response = self.client.post(
            reverse("templates_card_edit", args=[card.pk]),
            {"title": ""},
        )
        self.assertEqual(response.status_code, 400)

    def test_card_move_same_column(self):
        card_1 = Card.objects.create(column=self.col_a, title="Card 1", order=0)
        card_2 = Card.objects.create(column=self.col_a, title="Card 2", order=1)
        response = self.client.post(
            reverse("templates_card_move"),
            {
                "card_id": card_1.pk,
                "column_id": self.col_a.pk,
                "order": 1,
            },
        )
        self.assertEqual(response.status_code, 204)
        card_1.refresh_from_db()
        card_2.refresh_from_db()
        self.assertEqual(card_2.order, 0)
        self.assertEqual(card_1.order, 1)

    def test_card_move_different_column(self):
        card_1 = Card.objects.create(column=self.col_a, title="Card 1", order=0)
        response = self.client.post(
            reverse("templates_card_move"),
            {
                "card_id": card_1.pk,
                "column_id": self.col_b.pk,
                "order": 0,
            },
        )
        self.assertEqual(response.status_code, 204)
        card_1.refresh_from_db()
        self.assertEqual(card_1.column, self.col_b)
        self.assertEqual(card_1.order, 0)

    def test_card_move_invalid(self):
        response = self.client.post(
            reverse("templates_card_move"),
            {
                "card_id": -1,
                "column_id": self.col_b.pk,
                "order": 0,
            },
        )
        self.assertEqual(response.status_code, 400)
