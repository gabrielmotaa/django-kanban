"""Card activity: what happened to a card, as data plus one pt-BR rendering.

``record_activity`` is the only place that writes the history; the message of
an entry is rendered from ``kind`` + ``data`` here, so both UI versions show
exactly the same text. Entries are impersonal: the app has no authentication.
"""

import datetime as dt

KIND_CHOICES = [
    ("card_created", "Card criado"),
    ("card_moved", "Card movido"),
    ("title_renamed", "Título alterado"),
    ("description_changed", "Descrição alterada"),
    ("label_added", "Etiqueta adicionada"),
    ("label_removed", "Etiqueta removida"),
    ("due_set", "Data de entrega definida"),
    ("due_removed", "Data de entrega removida"),
    ("due_completed", "Data de entrega concluída"),
    ("checklist_item_completed", "Item de checklist concluído"),
]

MESSAGES = {
    "card_created": lambda d: f"Card criado em “{d['column']}”",
    "card_moved": lambda d: f"Card movido de “{d['from']}” para “{d['to']}”",
    "title_renamed": lambda d: f"Título alterado de “{d['old']}” para “{d['new']}”",
    "description_changed": lambda d: "Descrição alterada",
    "label_added": lambda d: f"Etiqueta “{d['name']}” adicionada",
    "label_removed": lambda d: f"Etiqueta “{d['name']}” removida",
    "due_set": lambda d: (
        "Data de entrega definida para "
        f"{dt.date.fromisoformat(d['date']).strftime('%d/%m/%Y')}"
    ),
    "due_removed": lambda d: "Data de entrega removida",
    "due_completed": lambda d: "Data de entrega marcada como concluída",
    "checklist_item_completed": lambda d: (
        f"Item “{d['text']}” concluído em “{d['checklist']}”"
    ),
}


def render_message(kind: str, data: dict) -> str:
    return MESSAGES[kind](data)


def record_activity(card, kind: str, **data):
    """Store one history entry for ``card`` and return it."""
    if kind not in MESSAGES:
        raise ValueError(f"Unknown activity kind: {kind!r}")
    from kanban.models import Activity

    return Activity.objects.create(card=card, kind=kind, data=data)
