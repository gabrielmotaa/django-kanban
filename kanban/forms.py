from django import forms


class CardMoveForm(forms.Form):
    card_id = forms.IntegerField(min_value=1)
    column_id = forms.IntegerField(min_value=1)
    order = forms.IntegerField(min_value=0)


class CardEditForm(forms.Form):
    title = forms.CharField(max_length=200)


class ColumnMoveForm(forms.Form):
    column_id = forms.IntegerField(min_value=1)
    order = forms.IntegerField(min_value=0)


class CardCreateForm(forms.Form):
    title = forms.CharField(max_length=200)


class ColumnCreateForm(forms.Form):
    title = forms.CharField(max_length=100)
    color = forms.CharField(max_length=7, required=False)


class ColumnEditForm(forms.Form):
    title = forms.CharField(max_length=100, required=False)
    color = forms.CharField(max_length=7, required=False)


class BoardEditForm(forms.Form):
    title = forms.CharField(max_length=100)
