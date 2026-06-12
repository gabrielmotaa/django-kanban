import pytest

from kanban.models import Board, Card, Column

pytestmark = pytest.mark.django_db


@pytest.fixture
def board() -> Board:
    return Board.objects.create(title="Test Board")


@pytest.fixture
def col_a(board: Board) -> Column:
    return Column.objects.create(board=board, title="Col A", order=1)


@pytest.fixture
def col_b(board: Board) -> Column:
    return Column.objects.create(board=board, title="Col B", order=0)


@pytest.fixture
def column(board: Board) -> Column:
    return Column.objects.create(board=board, title="Test Column", order=0)


@pytest.fixture
def card_a(column: Column) -> Card:
    return Card.objects.create(column=column, title="Card A", order=2)


@pytest.fixture
def card_b(column: Column) -> Card:
    return Card.objects.create(column=column, title="Card B", order=1)


class TestBoard:
    def test_str(self, board: Board) -> None:
        assert str(board) == "Test Board"

    def test_created_at_auto_populated(self, board: Board) -> None:
        assert board.created_at is not None

    def test_columns_related_name(self, board: Board) -> None:
        column = Column.objects.create(board=board, title="Col", order=0)
        assert column in board.columns.all()


class TestColumn:
    def test_str(self, col_a: Column) -> None:
        assert str(col_a) == "Col A"

    def test_board_fk(self, col_a: Column, board: Board) -> None:
        assert col_a.board == board

    def test_ordering_by_order_field(
        self, board: Board, col_a: Column, col_b: Column
    ) -> None:
        columns = list(board.columns.all())
        assert columns == [col_b, col_a]

    def test_cascade_delete_from_board(self) -> None:
        board = Board.objects.create(title="Temp Board")
        Column.objects.create(board=board, title="Orphan", order=0)
        board.delete()
        assert not Column.objects.filter(title="Orphan").exists()

    def test_default_color(self, col_a: Column) -> None:
        assert col_a.color == "#64748b"

    def test_color_choices(self, col_a: Column) -> None:
        choices = col_a.COLOR_CHOICES
        assert isinstance(choices, list)
        assert len(choices) == 8
        assert ("#64748b", "Cinza") in choices
        assert ("#f59e0b", "Âmbar") in choices

    def test_fg_color(self, col_a: Column, board: Board) -> None:
        assert col_a.fg_color == "#ffffff"

        col_amber = Column.objects.create(
            board=board, title="Amber Col", order=2, color="#f59e0b"
        )
        assert col_amber.fg_color == "#1e293b"


class TestCard:
    def test_str(self, card_a: Card) -> None:
        assert str(card_a) == "Card A"

    def test_column_fk(self, card_a: Card, column: Column) -> None:
        assert card_a.column == column

    def test_order_default_is_zero(self, column: Column) -> None:
        card = Card.objects.create(column=column, title="Default Order")
        assert card.order == 0

    def test_created_at_and_updated_at_auto_populated(self, card_a: Card) -> None:
        assert card_a.created_at is not None
        assert card_a.updated_at is not None

    def test_ordering_by_order_then_created_at(
        self, column: Column, card_a: Card, card_b: Card
    ) -> None:
        cards = list(column.cards.filter(title__in=["Card A", "Card B"]))
        assert cards == [card_b, card_a]

    def test_cards_related_name(self, card_a: Card, column: Column) -> None:
        assert card_a in column.cards.all()

    def test_cascade_delete_from_column(self) -> None:
        board = Board.objects.create(title="Temp Board")
        col = Column.objects.create(board=board, title="Temp Col", order=0)
        Card.objects.create(column=col, title="Orphan Card")
        col.delete()
        assert not Card.objects.filter(title="Orphan Card").exists()

    def test_cascade_delete_from_board(self) -> None:
        board = Board.objects.create(title="Temp Board 2")
        col = Column.objects.create(board=board, title="Temp Col", order=0)
        Card.objects.create(column=col, title="Deep Orphan")
        board.delete()
        assert not Card.objects.filter(title="Deep Orphan").exists()
