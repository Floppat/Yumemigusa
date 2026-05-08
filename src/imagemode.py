from __future__ import annotations
import flet as ft

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import App


class ImageMode():
    def __init__(self, app: App) -> None:
        self.app = app
        self.id = 0
        self.width = 0
        self.heigth = 0
        self.page_width, self.page_height  = self.app.page.width-self.app.page.width/5, self.app.page.height-106 # pyright: ignore[reportOptionalOperand]
        self.visible = False    
        self.app.page.height
        self.management_menu = TagManager(app)
        self.image = ft.Image(
            src='',
            fit = ft.BoxFit.CONTAIN, 
            border_radius = ft.BorderRadius.all(10), 
            visible = False)
        self.disable = ft.IconButton(
            icon = ft.Icons.ARROW_BACK, 
            icon_color = ft.Colors.GREY, 
            icon_size = 40, 
            tooltip = "go back", 
            on_click = self.close_image_mode, 
            visible = False)
        self.manage_tags = ft.Button(
            content="manage tags", 
            style = ft.ButtonStyle(bgcolor = ft.Colors.BLACK), 
            on_click = lambda _: self.management_menu.open_menu(), 
            visible = False)

    def fullscreen(self, path: str, width: int, height: int, img_id: int):
        def _fullscreen(_) -> None:
            self.app.scroll_to = self.app.scroll_pixes
            self.image.src = path
            self.id = img_id     
            self.width = width
            self.heigth = height
            self.image.height, self.image.width = (None, min(self.page_width, self.width)) if self.heigth/self.width < (self.page_height)/(self.page_width) else (min(self.page_height, self.heigth), None)
            self.management_menu.tags.controls = self.process_tags()
            self.app.change_mode(self)
        return _fullscreen

    def process_tags(self) -> list:
        self.manage_tags.style = ft.ButtonStyle(bgcolor = ft.Colors.BLACK if self.app.theme == "dark" else ft.Colors.WHITE)
        metadata = self.app.db.get_tags(self.id)
        controls = []
        for tag in metadata:
            controls.append(
                ft.Button(
                    content= tag[0], 
                    icon = self.app.tag_style[tag[1] if tag[1] != 'title' else tag[2]][0], 
                    style = ft.ButtonStyle(
                        color = self.app.tag_style[tag[1] if tag[1] != 'title' else tag[2]][1], 
                        bgcolor = ft.Colors.BLACK if self.app.theme == "dark" else ft.Colors.WHITE), 
                    on_click = self.filter_by_tag(tag[0])))
        return controls

    def filter_by_tag(self, tag: str):
        async def _filter_by_tag(_) -> None:
            await self.close_image_mode(_)
            self.app.tag_search.new_selection = [tag]
            self.app.tag_search.blacklist.clear()
            self.app.pagination.value_update(1)
        return _filter_by_tag

    async def close_image_mode(self, _):
        self.app.change_mode(self.app.art_mode)
        await self.app.page.scroll_to(self.app.scroll_to)

    def reload(self) -> None:
        self.page_width, self.page_height  = self.app.page.width-self.app.page.width/5, self.app.page.height-106 # pyright: ignore[reportOptionalOperand]
        self.image.height, self.image.width = (None, min(self.page_width, self.width)) if self.heigth/self.width < (self.page_height)/(self.page_width) else (min(self.page_height, self.heigth), None)
        self.image.update()

    def change_visibility(self, way: bool) -> None:
        self.visible = way
        if self.management_menu.callables:
            self.management_menu.hide_menu()
        self.image.visible, self.disable.visible, self.management_menu.tags.visible, self.manage_tags.visible = [self.visible]*4
        self.image.update(), self.disable.update(), self.management_menu.tags.update(), self.manage_tags.update() # pyright: ignore[reportUnusedExpression]


class TagManager():
    def __init__(self, app: App) -> None:
        self.app = app
        self.directory = ft.Text(visible = False, selectable = True)
        self.visible = False
        self.tags = ft.Column(visible = False)
        self.callables = []

    def open_menu(self) -> None:
        self.app.db.open_connection()
        for button in self.tags.controls:
            if type(button) is ft.Button:
                self.callables.append(button.on_click)
                tag_id = self.app.db.get_PK("tags", "tag", str(button.content))
                button.on_click = self.delete_tag(self.app.image_mode.id, tag_id)
                button.update()
        self.app.db.close_connection()
        path = str(self.app.image_mode.image.src).strip().split("\\")
        self.directory.value = ""
        for i in range(len(path)):
            self.directory.value += str(" "*i+path[i]+"\\\n")
        self.directory.value = self.directory.value.removesuffix("\\\n")
        self.app.image_mode.manage_tags.content = "hide managment"
        self.app.image_mode.manage_tags.on_click = lambda _: self.hide_menu()
        self.app.image_mode.manage_tags.update()
        self.change_visibility()

    def hide_menu(self) -> None:
        if not self.callables:
            return
        for i, button in enumerate(self.tags.controls):
            if type(button) is ft.Button:
                button.on_click = self.callables[i]
                button.update()
        self.callables.clear()
        self.app.image_mode.manage_tags.content = "manage tags"
        self.app.image_mode.manage_tags.on_click = lambda _: self.open_menu()
        self.app.image_mode.manage_tags.update()
        self.change_visibility()

    def delete_tag(self, img_id: int, tag_id: int):
        def _delete_tag(_) -> None:
            self.app.db.remove_tag(img_id, tag_id)
            self.reload()
        return _delete_tag

    def reload(self) -> None:
        self.hide_menu()
        self.tags.controls = self.app.image_mode.process_tags()
        self.tags.update()
        self.open_menu()

    def change_visibility(self) -> None:
        self.visible = not self.visible
        self.directory.visible, self.app.tag_add.field.visible = [self.visible]*2
        self.app.tag_add.field.value = ''
        self.app.tag_add.suggestions.visible = not self.app.tag_add.suggestions.visible if self.app.tag_add.suggestions.visible else self.app.tag_add.suggestions.visible
        self.directory.update(), self.app.tag_add.field.update(), self.app.tag_add.suggestions.update() # pyright: ignore[reportUnusedExpression]