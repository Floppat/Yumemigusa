from __future__ import annotations
import flet as ft

from copy import deepcopy
from math import ceil
import imagesize
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import App


class ArtMode():
    def __init__(self, app: App) -> None:
        self.app = app
        self.images, self.count = None, 0
        self.strict_mode = False
        self.reverse_strict = False
        self.visible = True
        self.art_grid = ft.Row(vertical_alignment = ft.CrossAxisAlignment.START, spacing = 5)

    def create_page(self) -> None:
        self.app.change_mode(self)
        # self.app.page.scroll_to(0)

        if self.app.tag_search.current_selection != self.app.tag_search.new_selection and self.app.tag_search.current_selection != self.app.tag_search.previous_selection:
            self.app.tag_search.previous_selection = self.app.tag_search.current_selection
            if self.strict_mode:
                self.strict_mode = False
                self.reverse_strict = False
        self.app.tag_search.current_selection = deepcopy(self.app.tag_search.new_selection)

        self.app.tag_search.field.value = ", ".join(self.app.tag_search.current_selection) + ((", -" if self.app.tag_search.current_selection else '-') + ", -".join(self.app.tag_search.blacklist) if self.app.tag_search.blacklist else '')
        self.app.tag_search.field.update()

        try:
            self.images, self.count = self.app.db.filter(tuple(self.app.tag_search.current_selection), tuple(self.app.tag_search.blacklist), self.app.pagination.value, self.app.arts_on_page.value, self.strict_mode, self.reverse_strict)
            self.display_images()
            self.app.label_images_count.value = f'{self.count}'
            self.app.label_images_count.update()
            self.app.pagination.limit = ceil(self.count/self.app.arts_on_page.value)
            self.app.pagination.page_limit.value = f'/{self.app.pagination.limit}'
            self.app.pagination.page_limit.update()
        except ValueError:
            self.app.invoke_error("в базе данных нет записей соответствующих заданным параметрам")

    def display_images(self) -> None:
        if not self.images:
            return
        columns = [[[],0] for _ in range(self.app.columns_of_arts.value)]
        width_value = (self.app.page.width-20-5*(self.app.columns_of_arts.value-1))/self.app.columns_of_arts.value # pyright: ignore[reportOptionalOperand]
        for path, img_id in self.images:
            width, height = imagesize.get(path)
            index = min(range(len(columns)), key=lambda i: columns[i][1])
            columns[index][0].append(ft.MenuItemButton(
                content = ft.Image(
                    src = path, 
                    fit = ft.BoxFit.CONTAIN, 
                    border_radius = ft.BorderRadius.all(10), 
                    width = width_value), 
                style = ft.ButtonStyle(
                    padding = 0, 
                    shape = ft.RoundedRectangleBorder(radius = 10)), 
                on_click = self.app.image_mode.fullscreen(path, width, height, img_id), 
                width = width_value, 
                height = (width_value/width)*height))
            columns[index][1]+=height/width
        self.art_grid.controls = [ft.Column(controls=column[0], spacing=0) for column in sorted(columns, key=lambda i: i[1], reverse=True)]
        self.art_grid.update()

    def change_mode(self, _):
        tags = self.app.db.get_tag_info(self.app.tag_search.current_selection)
        if tags and (tags.count("character") > 0 and tags.count("title") > 0) or (tags.count("character") != 1 and tags.count("title") != 1):
            self.app.invoke_error("строгий режим работает либо только с одним персонажем, либо только с одной франшизой")
            return
        self.strict_mode = not self.strict_mode
        self.create_page()

    def reverse_mode(self, _):
        if not self.strict_mode:
            self.change_mode(_)
        self.reverse_strict = not self.reverse_strict
        self.create_page()

    def reload(self) -> None:
        self.display_images()

    def change_visibility(self, way: bool) -> None:
        self.visible = way
        self.art_grid.visible = self.visible
        self.app.row_images_count.visible = self.visible
        self.art_grid.update(), self.app.row_images_count.update() # pyright: ignore[reportUnusedExpression]
        self.app.pagination.change_visibility(way)
        self.app.tag_search.hide_suggestions()