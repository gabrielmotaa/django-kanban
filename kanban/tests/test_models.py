from django.test import TestCase

from kanban.models import Board, Card, Column


class BoardTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.board = Board.objects.create(title="Test Board")

    def test_str(self):
        self.assertEqual(str(self.board), "Test Board")

    def test_created_at_auto_populated(self):
        self.assertIsNotNone(self.board.created_at)

    def test_columns_related_name(self):
        column = Column.objects.create(board=self.board, title="Col", order=0)
        self.assertIn(column, self.board.columns.all())


class ColumnTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.board = Board.objects.create(title="Test Board")
        cls.col_a = Column.objects.create(board=cls.board, title="Col A", order=1)
        cls.col_b = Column.objects.create(board=cls.board, title="Col B", order=0)

    def test_str(self):
        self.assertEqual(str(self.col_a), "Test Board / Col A")

    def test_board_fk(self):
        self.assertEqual(self.col_a.board, self.board)

    def test_ordering_by_order_field(self):
        columns = list(self.board.columns.all())
        self.assertListEqual(columns, [self.col_b, self.col_a])

    def test_cascade_delete_from_board(self):
        board = Board.objects.create(title="Temp Board")
        Column.objects.create(board=board, title="Orphan", order=0)
        board.delete()
        self.assertFalse(Column.objects.filter(title="Orphan").exists())

    def test_default_color(self):
        self.assertEqual(self.col_a.color, "#64748b")

    def test_color_choices(self):
        choices = self.col_a.color_choices
        self.assertIsInstance(choices, list)
        self.assertEqual(len(choices), 8)
        self.assertIn(("#64748b", "Cinza"), choices)
        self.assertIn(("#f59e0b", "Âmbar"), choices)

    def test_fg_color(self):
        # Default or other colors should fall back to #ffffff
        self.assertEqual(self.col_a.fg_color, "#ffffff")

        # Specific color #f59e0b (Âmbar) should map to #1e293b
        col_amber = Column.objects.create(
            board=self.board, title="Amber Col", order=2, color="#f59e0b"
        )
        self.assertEqual(col_amber.fg_color, "#1e293b")


class CardTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.board = Board.objects.create(title="Test Board")
        cls.column = Column.objects.create(
            board=cls.board, title="Test Column", order=0
        )
        cls.card_a = Card.objects.create(column=cls.column, title="Card A", order=2)
        cls.card_b = Card.objects.create(column=cls.column, title="Card B", order=1)

    def test_str(self):
        self.assertEqual(str(self.card_a), "Card A")

    def test_column_fk(self):
        self.assertEqual(self.card_a.column, self.column)

    def test_description_defaults_to_empty_string(self):
        self.assertEqual(self.card_a.description, "")

    def test_description_stored_correctly(self):
        card = Card.objects.create(
            column=self.column, title="With Desc", description="Hello"
        )
        self.assertEqual(card.description, "Hello")

    def test_order_default_is_zero(self):
        card = Card.objects.create(column=self.column, title="Default Order")
        self.assertEqual(card.order, 0)

    def test_created_at_and_updated_at_auto_populated(self):
        self.assertIsNotNone(self.card_a.created_at)
        self.assertIsNotNone(self.card_a.updated_at)

    def test_ordering_by_order_then_created_at(self):
        cards = list(self.column.cards.filter(title__in=["Card A", "Card B"]))
        self.assertEqual(cards, [self.card_b, self.card_a])

    def test_cards_related_name(self):
        self.assertIn(self.card_a, self.column.cards.all())

    def test_cascade_delete_from_column(self):
        board = Board.objects.create(title="Temp Board")
        col = Column.objects.create(board=board, title="Temp Col", order=0)
        Card.objects.create(column=col, title="Orphan Card")
        col.delete()
        self.assertFalse(Card.objects.filter(title="Orphan Card").exists())

    def test_cascade_delete_from_board(self):
        board = Board.objects.create(title="Temp Board 2")
        col = Column.objects.create(board=board, title="Temp Col", order=0)
        Card.objects.create(column=col, title="Deep Orphan")
        board.delete()
        self.assertFalse(Card.objects.filter(title="Deep Orphan").exists())
