from django.db import models

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
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return self.title
