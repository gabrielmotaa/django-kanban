from django import forms

from kanban.models import Column

TITLE_MESSAGES = {"required": "O título é obrigatório."}
INVALID_REQUEST = "Requisição inválida."
ID_MESSAGES = {
    "required": INVALID_REQUEST,
    "invalid": INVALID_REQUEST,
    "min_value": INVALID_REQUEST,
}
COLOR_MESSAGES = {"max_length": "Cor inválida."}


def title_field(max_length: int, **kwargs) -> forms.CharField:
    return forms.CharField(
        max_length=max_length,
        error_messages={
            **TITLE_MESSAGES,
            "max_length": f"O título deve ter no máximo {max_length} caracteres.",
        },
        **kwargs,
    )


class CardEditForm(forms.Form):
    title = title_field(200, required=False)
    column_id = forms.IntegerField(
        min_value=0, required=False, error_messages=ID_MESSAGES
    )
    order = forms.IntegerField(min_value=0, required=False, error_messages=ID_MESSAGES)

    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get("title")
        column_id = cleaned_data.get("column_id")
        order = cleaned_data.get("order")

        if not title and (column_id is None or order is None):
            raise forms.ValidationError("Informe um título ou a nova posição do card.")


DESCRIPTION_MAX_LENGTH = 5000


class CardDescriptionForm(forms.Form):
    description = forms.CharField(
        required=False,
        max_length=DESCRIPTION_MAX_LENGTH,
        error_messages={
            "max_length": f"A descrição deve ter no máximo {DESCRIPTION_MAX_LENGTH} caracteres."
        },
    )


class CardCreateForm(forms.Form):
    column_id = forms.IntegerField(min_value=1, error_messages=ID_MESSAGES)
    title = title_field(200)


class ColumnCreateForm(forms.Form):
    board_id = forms.IntegerField(min_value=1, error_messages=ID_MESSAGES)
    title = title_field(100)
    color = forms.CharField(max_length=7, required=False, error_messages=COLOR_MESSAGES)


class ColumnEditForm(forms.Form):
    title = title_field(100, required=False)
    color = forms.CharField(max_length=7, required=False, error_messages=COLOR_MESSAGES)
    order = forms.IntegerField(min_value=0, required=False, error_messages=ID_MESSAGES)

    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get("title")
        color = cleaned_data.get("color")
        order = cleaned_data.get("order")

        if not title and not color and order is None:
            raise forms.ValidationError(
                "Informe um título, uma cor ou a nova posição da coluna."
            )


class BoardEditForm(forms.Form):
    title = title_field(100)


class LabelForm(forms.Form):
    name = forms.CharField(
        max_length=30,
        required=False,
        error_messages={"max_length": "O nome deve ter no máximo 30 caracteres."},
    )
    color = forms.ChoiceField(
        choices=Column.COLOR_CHOICES,
        error_messages={"required": "Cor inválida.", "invalid_choice": "Cor inválida."},
    )


class LabelCreateForm(LabelForm):
    board_id = forms.IntegerField(min_value=1, error_messages=ID_MESSAGES)
    card_id = forms.IntegerField(min_value=1, error_messages=ID_MESSAGES)


class LabelEditForm(LabelForm):
    card_id = forms.IntegerField(min_value=1, error_messages=ID_MESSAGES)


class LabelContextForm(forms.Form):
    """The card whose dialog sent a label request (used to render the reply)."""

    card_id = forms.IntegerField(min_value=1, error_messages=ID_MESSAGES)


class CardLabelForm(forms.Form):
    label_id = forms.IntegerField(min_value=1, error_messages=ID_MESSAGES)


class CardDueDateForm(forms.Form):
    due_date = forms.DateField(
        required=False, error_messages={"invalid": "Data inválida."}
    )
    completed = forms.BooleanField(required=False)


class ChecklistCreateForm(forms.Form):
    title = forms.CharField(
        max_length=100,
        required=False,
        error_messages={"max_length": "O título deve ter no máximo 100 caracteres."},
    )


class ChecklistRenameForm(forms.Form):
    title = title_field(100)


class ChecklistItemCreateForm(forms.Form):
    text = forms.CharField(
        max_length=200,
        error_messages={
            "required": "O texto do item é obrigatório.",
            "max_length": "O texto deve ter no máximo 200 caracteres.",
        },
    )


class ChecklistItemEditForm(forms.Form):
    """Edit the text and/or the done state; an absent field means "unchanged"."""

    text = forms.CharField(
        max_length=200,
        required=False,
        error_messages={"max_length": "O texto deve ter no máximo 200 caracteres."},
    )
    done = forms.NullBooleanField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        if "text" in self.data and not cleaned_data.get("text"):
            if "text" not in self.errors:
                raise forms.ValidationError("O texto do item é obrigatório.")
        elif "text" not in self.data and cleaned_data.get("done") is None:
            raise forms.ValidationError("Informe o texto ou o estado do item.")
        return cleaned_data


class CommentForm(forms.Form):
    text = forms.CharField(
        max_length=5000,
        error_messages={
            "required": "O comentário é obrigatório.",
            "max_length": "O comentário deve ter no máximo 5000 caracteres.",
        },
    )
