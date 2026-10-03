from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from kanban.models import (
    Board,
    Card,
    Checklist,
    ChecklistItem,
    Column,
    Label,
)


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "created_at")
    search_fields = ("title",)


@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    list_display = ("id", "board_link", "title", "order", "color_preview")
    list_filter = ("board",)
    search_fields = ("title",)

    @admin.display(description="Board")
    def board_link(self, obj):
        url = reverse("admin:kanban_board_change", args=[obj.board.pk])
        return format_html('<a href="{}">{}</a>', url, obj.board.title)

    @admin.display(description="Color")
    def color_preview(self, obj):
        return format_html(
            '<div style="display: flex; align-items: center; gap: 8px;">'
            '<div style="width: 16px; height: 16px; background-color: {}; border-radius: 4px; border: 1px solid rgba(0,0,0,0.15);"></div>'
            "<span>{}</span>"
            "</div>",
            obj.color,
            obj.color,
        )


class ChecklistInline(admin.TabularInline):
    model = Checklist
    extra = 0
    show_change_link = True


class ChecklistItemInline(admin.TabularInline):
    model = ChecklistItem
    extra = 0


@admin.register(Checklist)
class ChecklistAdmin(admin.ModelAdmin):
    list_display = ("id", "card", "title", "order")
    list_filter = ("card__column__board",)
    search_fields = ("title", "card__title")
    inlines = [ChecklistItemInline]


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    inlines = [ChecklistInline]
    list_display = (
        "id",
        "column_link",
        "board_link",
        "title",
        "order",
        "due_date",
        "completed",
        "created_at",
        "updated_at",
    )
    list_filter = ("column__board", "column", "due_date", "completed")
    search_fields = ("title", "description")
    filter_horizontal = ("labels",)

    @admin.display(description="Column")
    def column_link(self, obj):
        url = reverse("admin:kanban_column_change", args=[obj.column.pk])
        return format_html('<a href="{}">{}</a>', url, obj.column.title)

    @admin.display(description="Board")
    def board_link(self, obj):
        board = obj.column.board
        url = reverse("admin:kanban_board_change", args=[board.pk])
        return format_html('<a href="{}">{}</a>', url, board.title)


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ("id", "board", "name", "color_preview")
    list_filter = ("board",)
    search_fields = ("name",)

    @admin.display(description="Color")
    def color_preview(self, obj):
        return format_html(
            '<div style="display: flex; align-items: center; gap: 8px;">'
            '<div style="width: 16px; height: 16px; background-color: {}; border-radius: 4px; border: 1px solid rgba(0,0,0,0.15);"></div>'
            "<span>{}</span>"
            "</div>",
            obj.color,
            obj.color,
        )
