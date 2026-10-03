from datetime import timedelta

from django.db import models
from django.utils import timezone

FG_OVERRIDES = {
    "#f59e0b": "#1e293b",  # Âmbar
}


def foreground_for(color: str) -> str:
    """Readable text color on top of one of the palette colors."""
    return FG_OVERRIDES.get(color, "#ffffff")


class Board(models.Model):
    """Represents a Kanban board."""

    title = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Column(models.Model):
    """Represents a column (swimlane) in a Kanban board."""

    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="columns")
    title = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    color = models.CharField(max_length=7, default="#64748b")

    class Meta:
        ordering = ["order"]

    COLOR_CHOICES = [
        ("#64748b", "Cinza"),
        ("#ef4444", "Vermelho"),
        ("#f97316", "Laranja"),
        ("#f59e0b", "Âmbar"),
        ("#10b981", "Esmeralda"),
        ("#3b82f6", "Azul"),
        ("#8b5cf6", "Roxo"),
        ("#ec4899", "Rosa"),
    ]

    @property
    def fg_color(self):
        return foreground_for(self.color)

    def __str__(self):
        return self.title


class Label(models.Model):
    """A colored label defined per board and attached to cards."""

    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="labels")
    name = models.CharField(max_length=30, blank=True)
    color = models.CharField(
        max_length=7, choices=Column.COLOR_CHOICES, default="#64748b"
    )

    class Meta:
        ordering = ["name", "pk"]

    @property
    def fg_color(self):
        return foreground_for(self.color)

    @property
    def color_name(self):
        return dict(Column.COLOR_CHOICES).get(self.color, self.color)

    def __str__(self):
        return self.name or self.color_name


class Card(models.Model):
    """Represents a task card inside a column."""

    column = models.ForeignKey(Column, on_delete=models.CASCADE, related_name="cards")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    labels = models.ManyToManyField("Label", blank=True, related_name="cards")
    due_date = models.DateField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "created_at"]

    DUE_LABELS = {
        "complete": "Concluído",
        "overdue": "Atrasado",
        "soon": "Vence em breve",
        "ok": "Data de entrega",
    }
    DUE_CHIPS = {"overdue": "Atrasado", "soon": "Vence em breve"}

    @property
    def checklist_done(self):
        return sum(c.done_count for c in self.checklists.all())

    @property
    def checklist_total(self):
        return sum(c.total_count for c in self.checklists.all())

    @property
    def checklist_status(self):
        total = self.checklist_total
        if not total:
            return ""
        return "complete" if self.checklist_done == total else "ok"

    @property
    def checklist_label(self):
        """Accessible name of the checklist badge (empty without items)."""
        total = self.checklist_total
        return f"Checklist {self.checklist_done} de {total}" if total else ""

    @property
    def due_status(self):
        """`complete`, `overdue`, `soon` (today or tomorrow), `ok` or None.

        Computed on the server for both UI versions, in the local time zone, so
        Python and the browser never disagree around midnight.
        """
        if self.due_date is None:
            return None
        if self.completed:
            return "complete"
        today = timezone.localdate()
        if self.due_date < today:
            return "overdue"
        if self.due_date <= today + timedelta(days=1):
            return "soon"
        return "ok"

    @property
    def due_label(self):
        """Accessible name of the due badge."""
        return self.DUE_LABELS.get(self.due_status, "")

    @property
    def due_chip(self):
        """Short status text shown in the dialog (empty when not noteworthy)."""
        return self.DUE_CHIPS.get(self.due_status, "")

    def __str__(self):
        return self.title


class Checklist(models.Model):
    """A named checklist inside a card."""

    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name="checklists")
    title = models.CharField(max_length=100, default="Checklist")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "pk"]

    @property
    def done_count(self):
        return sum(1 for item in self.items.all() if item.done)

    @property
    def total_count(self):
        return len(self.items.all())

    @property
    def percent(self):
        """Completion as an integer, rounded half up (same rule in the browser)."""
        total = self.total_count
        return int(100 * self.done_count / total + 0.5) if total else 0

    def __str__(self):
        return self.title


class ChecklistItem(models.Model):
    """One entry of a checklist."""

    checklist = models.ForeignKey(
        Checklist, on_delete=models.CASCADE, related_name="items"
    )
    text = models.CharField(max_length=200)
    done = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "pk"]

    def __str__(self):
        return self.text
