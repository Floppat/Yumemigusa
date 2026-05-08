from __future__ import annotations
import flet as ft

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import App


class TagSuggestionSelector():
    def __init__(self, app: App, field: ft.TextField | ft.SearchBar, width: int, heigth: int, count: int, display_entries_count: bool) -> None:
        self.app = app
        self.field = field
        self.width = width
        self.heigth = heigth
        self.count = count
        self.display_entries_count = display_entries_count
        self.selection = []
        self.suggestions = ft.ListView(
            spacing = 0, 
            padding = ft.Padding.only(left = 10, right = 10), 
            width = width, 
            height = heigth, 
            expand = 1, 
            visible = False)
        self.padding = ft.Text(width = 0)
        self.field.on_submit = lambda _: self.handle_submit() # pyright: ignore[reportAttributeAccessIssue]
        self.field.on_change = self.on_field_change
        self.field.on_blur = lambda _: self.hide_suggestions() # pyright: ignore[reportAttributeAccessIssue]
        if isinstance(self.field, ft.TextField):
            self.field.on_click = self.on_field_change
            self.field.on_tap_outside = lambda _: _
        else:
            self.field.on_tap = self.on_field_change
            self.field.on_tap_outside_bar = lambda _: _

    def handle_submit(self) -> tuple[list, list]:
        self.selection.clear()

        submit_value = str(self.field.value).split(", ")
        if not submit_value[-1]:
            submit_value.pop()

        tag_selection = []
        for val in submit_value:
            val = val.strip()
            if val:
                tag_selection.append(val)
        tag_selection = set(tag_selection)

        tags_hints = []
        tags_blacklist = []
        self.app.db.open_connection()
        for tag in tag_selection:
            if tag.strip()[0] == '-':
                self.tag_work(tags_blacklist, tag.strip().removeprefix("-").strip())
                continue
            self.tag_work(tags_hints, tag)
        self.app.db.close_connection()
        return tags_hints, tags_blacklist

    def tag_work(self, tags: list, tag: str) -> None:
        if tag_pk := self.app.db.get_PK('tags', 'tag', tag):
            tags.append(tag)
            self.selection.append(tag_pk)
            return
        if tag_hint := self.app.db.hint_tag(tag):
            tags.append(tag_hint[0][1])
            self.selection.append(tag_hint[0][0])
        elif search_all := self.app.db.search_hint(tag):
            tags.append(search_all[0][1])
            self.selection.append(search_all[0][0])

    def on_field_change(self, _) -> None:
        print(self.field.value)
        query = str(self.field.value)
        if "," in query:
            query = query.split(",")[-1]
        cur_query = query.strip().removeprefix("-").strip()
        hint_list = self.app.db.search_hint(cur_query)
        self.suggestions.controls = [
            ft.Button(
                content = f'{suggestion[1]}' + (f' ({suggestion[3]})' if self.display_entries_count else ''), 
                icon = self.app.tag_style[suggestion[2]][0], 
                style = ft.ButtonStyle(
                    color = self.app.tag_style[suggestion[2]][1], 
                    bgcolor = ft.Colors.BLACK if self.app.theme == "dark" else ft.Colors.WHITE, 
                    shape = ft.RoundedRectangleBorder()), 
                on_click = self.select_suggestion(suggestion[1]), 
                width = self.width-20, 
                height = self.heigth/self.count)
            for suggestion in hint_list]
        if hint_list:
            self.suggestions.controls[0].style.bgcolor = ft.Colors.GREEN_100 # pyright: ignore[reportAttributeAccessIssue]
            self.suggestions.visible = True
        else:
            self.suggestions.visible = False
        print(self.suggestions.controls)
        self.suggestions.update()

    def select_suggestion(self, sugg_text: str):
        def _select_suggestion(_) -> None:
            query = str(self.field.value)
            if "," in query:
                tag_list = query.split(",")
                tag_list[-1] = ("-" if tag_list[-1].strip() and tag_list[-1].strip()[0] == '-' else '')+sugg_text
                self.field.value = ", ".join(tag_list)+", "
            else:
                self.field.value = ("-" if query and query.strip()[0] == '-' else '')+sugg_text+", "
            self.suggestions.visible = False
            self.suggestions.update()
            self.field.update()
        return _select_suggestion

    def error(self) -> None:
        self.app.invoke_error(f"Отправлена пустая {self.field.hint_text if isinstance(self.field, ft.TextField) else self.field.bar_hint_text} форма")

    def hide_suggestions(self) -> None:
        self.suggestions.visible = False
        self.suggestions.update()


class TagSearchSuggestion(TagSuggestionSelector):
    def __init__(self, app: App, field: ft.TextField | ft.SearchBar, width: int, heigth: int, count: int, display_entries_count: bool) -> None:
        super().__init__(app, field, width, heigth, count, display_entries_count)
        self.previous_selection = []
        self.current_selection = []
        self.new_selection = []
        self.blacklist = []

    def handle_submit(self) -> None:
        tags_hints, tags_blacklist = super().handle_submit()
        if not (tags_hints or tags_blacklist) and self.field.value:
            self.app.invoke_error("указанные тэги не существуют")
            return
        self.new_selection = tags_hints
        self.blacklist = tags_blacklist
        self.app.pagination.value_update(1)


class TagAddSuggestion(TagSuggestionSelector):
    def __init__(self, app: App, field: ft.TextField | ft.SearchBar, width: int, heigth: int, count: int, display_entries_count: bool) -> None:
        super().__init__(app, field, width, heigth, count, display_entries_count)

    def handle_submit(self) -> None:
        super().handle_submit()
        self.app.db.new_image_tags(self.app.image_mode.id, self.selection)
        self.app.image_mode.management_menu.reload()
        self.suggestions.visible = False
        self.suggestions.update()


class TagBondSuggestion(TagSuggestionSelector):
    def __init__(self, app: App, field: ft.TextField | ft.SearchBar, width: int, heigth: int, count: int, display_entries_count: bool) -> None:
        super().__init__(app, field, width, heigth, count, display_entries_count)

    def handle_submit(self) -> None:
        return

    def hide_suggestions(self) -> None:
        super().hide_suggestions()
        if not self.field.value:
            return
        tags_hints, _ = super().handle_submit()
        self.field.value = ", ".join(tags_hints)
        self.field.update()