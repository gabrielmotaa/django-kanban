from django import forms


class CardEditForm(forms.Form):
    title = forms.CharField(max_length=200, required=False)
    column_id = forms.IntegerField(min_value=0, required=False)
    order = forms.IntegerField(min_value=0, required=False)

    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get("title")
        column_id = cleaned_data.get("column_id")
        order = cleaned_data.get("order")

        if not title and column_id is None and order is None:
            raise forms.ValidationError(
                "Either title or column_id and order must be provided."
            )


class CardCreateForm(forms.Form):
    column_id = forms.IntegerField(min_value=1)
    title = forms.CharField(max_length=200)


class ColumnCreateForm(forms.Form):
    board_id = forms.IntegerField(min_value=1)
    title = forms.CharField(max_length=100)
    color = forms.CharField(max_length=7, required=False)


class ColumnEditForm(forms.Form):
    title = forms.CharField(max_length=100, required=False)
    color = forms.CharField(max_length=7, required=False)
    order = forms.IntegerField(min_value=0, required=False)

    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get("title")
        color = cleaned_data.get("color")
        order = cleaned_data.get("order")

        if not title and not color and order is None:
            raise forms.ValidationError("No title or color provided")


class BoardEditForm(forms.Form):
    title = forms.CharField(max_length=100)
