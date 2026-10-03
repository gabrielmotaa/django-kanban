from django import forms

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
