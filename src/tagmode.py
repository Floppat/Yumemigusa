from __future__ import annotations
import flet as ft

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import App

from notifications import Notification, SuccessNotification
from tagsearch import TagBondSuggestion


class TagMode():
    def __init__(self, app: App) -> None:
        self.app = app
        self.visible = False
        self.callables = []
        self.tagfield = TagField(app)
        self.tags = ft.Row(vertical_alignment = ft.CrossAxisAlignment.START, spacing=0)
        self.tag_grid = ft.Column([self.tagfield.tagfield, self.tags], alignment = ft.MainAxisAlignment.START, visible=False)
        self.padding = ft.Text(width = 305)
        self.welcome = Notification(self.app, 
                'Добро пожаловать в режим управления тэгами! Функция сканирования в этом режиме ищет только тэги которых нет в базе данных, для того чтобы вы с удобством могли их добавить.', 
                (('выбрать директорию', self.app.data_input.path_picker.select),
                ('понятно, закрыть', lambda _: self.app.close_notifications()),))

    def fetch_cases(self) -> None:
        self.app.change_mode(self)
        if not self.app.tokenizer.unexpected_cases:
            self.welcome.visible()
            return
        self.tags.controls.clear()
        self.create_tagfield("Zerochan Tags", self.fetch_source_cases(self.app.tokenizer.unexpected_cases.get('zerochan', None)))
        self.create_tagfield("Danbooru Tags", self.fetch_source_cases(self.app.tokenizer.unexpected_cases.get('danbooru', None)))
        self.create_tagfield("Yandere Tags", self.fetch_source_cases(self.app.tokenizer.unexpected_cases.get('yande.re', None)))
        if not self.tags.controls:
            self.app.invoke_error("нет тэгов соответствующих параметрам")
            return
        self.tags.update()

    def create_tagfield(self, name: str, cases: dict | None):
        if not cases:
            return
        tagfield = TagGrid(self.app, name, cases)
        self.tags.controls += [tagfield.tag_grid]

    def fetch_source_cases(self, cases: dict | None) -> dict | None:
        if not cases:
            return
        real_cases = {}
        for item, val in cases.items():
            if val >= self.app.tag_minimum.value:
                    real_cases[item] = val
        return real_cases

    def reload(self) -> None:
        self.app.not_small()
        if self.app.size == self.app.sizes['fullscreen']:
            self.padding.width = 1002
            self.padding.update()
            return
        self.padding.width = self.app.page.width-862 # pyright: ignore[reportOptionalOperand]
        if self.app.page.width < 862: # pyright: ignore[reportOptionalOperand]
            self.app.small()
            self.padding.width = self.app.page.width - 504.0 # pyright: ignore[reportOptionalOperand]
        else:
            self.app.not_small()
        self.padding.update()
        for column in self.tags.controls:
            column.width = (self.app.page.width-20)/3 # pyright: ignore[reportOptionalOperand, reportAttributeAccessIssue]
            column.update()

    def change_visibility(self, way: bool):
        if not way:
            self.app.tag_mode_padding()
        self.app.data_input.change_mode()
        self.visible = way
        self.tag_grid.visible = way
        self.app.searchbar.visible = not way
        self.app.appbar.padding.visible = not way
        self.app.appbar.mode_button.icon = ft.Icons.IMAGE if way else ft.Icons.ART_TRACK_SHARP
        self.app.appbar.mode_button.on_click = lambda _: self.app.change_mode(self.app.prev_mode if way else self)
        self.app.page.appbar.leading.name = ft.Icons.ART_TRACK_SHARP if way else ft.Icons.IMAGE # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
        self.tag_grid.update()
        self.app.searchbar.update()
        self.app.appbar.padding.update()
        self.app.appbar.mode_button.update()
        self.app.page.appbar.update() # pyright: ignore[reportOptionalMemberAccess]
        if way:
            self.callables = self.app.appbar.popupmenu.items
            self.app.appbar.popupmenu.items = [
                ft.PopupMenuItem(content = ft.Row(width=145)), 
                ft.PopupMenuItem(content="lower barrier"), 
                ft.PopupMenuItem(
                content = ft.Row([
                        self.app.tag_minimum.decrease_value, 
                        self.app.tag_minimum.value_label, 
                        self.app.tag_minimum.increase_value], 
                    alignment = ft.MainAxisAlignment.CENTER)), 
                ft.PopupMenuItem(), 
                ft.PopupMenuItem(
                content = ft.Row([
                        ft.IconButton(
                            icon = ft.Icons.REPLAY, 
                            icon_color = ft.Colors.GREY, 
                            icon_size = 40, 
                            tooltip = "обновить страницу", 
                            on_click = lambda _: self.fetch_cases())], 
                    alignment = ft.MainAxisAlignment.CENTER))]
        else:
            self.app.appbar.popupmenu.items = self.callables
        self.app.appbar.popupmenu.update()

class TagField():
    def __init__(self, app: App) -> None:
        self.app = app
        self.textfield = ft.TextField(on_submit = self.submit, hint_text = "tag name", width=103)
        self.type = ft.Dropdown(width = 160, label="select type", options=[
            ft.DropdownOption(key=key, text=text) for key, text in self.app.db.read_types()], on_select=self.tagbond_control)
        self.parent = ParentField(app, "parent")
        self.childs = ChildsField(app, 'childs')
        self.tagfield = ft.Column([ft.Text('add tag'), ft.Row([self.textfield, self.type, self.childs.checkbox]), self.parent.field, self.parent.tag_add.suggestions, self.childs.field, self.childs.tag_add.suggestions])
        self.success = SuccessNotification(self.app, 
                'Тэг успешно добавлен.', 
                (('понятно, закрыть', lambda _: (self.app.close_notifications())),))

    def submit(self, _) -> None:
        if not self.textfield.value:
            self.app.invoke_error("не указано имя тэга")
            return
        if not self.type.value:
            self.app.invoke_error("не указан тип тэга")
            return
        meta = []
        if self.parent.field.visible:
            self.parent.field.value = ''
            self.parent.field.update()
            if not self.parent.tag_add.selection:
                self.parent.tag_add.error()
                return
            elif len(self.parent.tag_add.selection) > 1:
                self.app.invoke_error("у тэга может быть только один родительский тэг")
                return
            meta.append(self.parent.tag_add.selection[0])
        else:
            meta.append(None)
        if self.childs.field.visible:
            self.childs.field.value = ''
            self.childs.field.update()
            if not self.childs.tag_add.selection:
                self.childs.tag_add.error()
                return
            meta.append(tuple(self.childs.tag_add.selection) if len(self.childs.tag_add.selection) > 1 else self.childs.tag_add.selection[0])
        else:
            meta.append(None)
        self.app.db.new_tag(self.textfield.value.strip(), int(self.type.value), parent = meta[0], childs = meta[1]) # pyright: ignore[reportOptionalMemberAccess, reportArgumentType]
        self.textfield.value = ''
        self.textfield.update()
        self.success.visible()

    def tagbond_control(self, _):
        self.childs.checkbox.visible = False
        match self.type.value:
            case '1':
                self.parent.change_visibility(False)
                self.childs.checkbox.visible = True
            case '2' | '3':
                self.parent.change_visibility(True)
                self.childs.checkbox.visible = True
            case '4':
                self.parent.change_visibility(True)
                self.childs.change_visibility(False)
            case '5' | '6' | '7' | '8':
                self.parent.change_visibility(False)
                self.childs.change_visibility(False)
        self.childs.checkbox.update()


class ParentField():
    def __init__(self, app: App, hint_text: str) -> None:
        self.app = app
        self.field = ft.TextField(hint_text = f'{hint_text} tag', width = 103, visible = False)
        self.tag_add = TagBondSuggestion(self.app, self.field, 103, 60, 3, False)
        self.visible = False

    def change_visibility(self, way: bool) -> None:
        self.visible = way
        self.field.visible = self.visible
        self.field.value = ''
        self.tag_add.suggestions.visible = not self.tag_add.suggestions.visible if self.tag_add.suggestions.visible else self.tag_add.suggestions.visible
        self.field.update(), self.tag_add.suggestions.update() # pyright: ignore[reportUnusedExpression]


class ChildsField(ParentField):
    def __init__(self, app: App, hint_text: str) -> None:
        super().__init__(app, hint_text)
        self.checkbox = ft.Checkbox(label = hint_text, on_change = self.checkbox_visibility, visible=False)

    def checkbox_visibility(self, _):
        self.visible = not self.visible
        self.change_visibility(self.visible)

class TagGrid():
    def __init__(self, app: App, name: str, tags: dict | None) -> None:
        self.app = app
        self.text = ft.Text(f"{name}")
        self.button = ft.Button("expand", on_click=self.tags_visible)
        self.tags = ft.Column(visible=False)
        if tags:
            self.tags.controls = [
                ft.Button(
                    content = f'{tag} {str(count)}', 
                    on_click = self.add_tag(tag))
                for tag, count in sorted(tags.items(), key=lambda x: x[1], reverse = True)]
        self.tag_grid = ft.Column([self.text, self.button, self.tags], width=(self.app.page.width-20)/3) # pyright: ignore[reportOptionalOperand]

    def add_tag(self, tag: str):
        async def _add_tag(_) -> None:
            self.app.tag_mode.tagfield.textfield.value += f'{' ' if self.app.tag_mode.tagfield.textfield.value else ''}{tag}' # pyright: ignore[reportOperatorIssue]
            self.app.tag_mode.tagfield.textfield.update()
            await self.app.tag_mode.tagfield.textfield.focus()
        return _add_tag

    def tags_visible(self, _) -> None:
        if not self.tags.visible:
            self.tags.visible = True
            self.button.content = "minimize"
        else:
            self.tags.visible = False
            self.button.content = "expand"
        self.tags.update()
        self.button.update()