from __future__ import annotations
import flet as ft

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import App


class TripleRegulator():
    def __init__(self, default_value: int, *limit: int) -> None:
        self.default_value = default_value
        self.value = default_value
        self.limit = limit[0] if limit else False
        self.visible = True

        self.decrease_value = ft.IconButton(
            icon = ft.Icons.ARROW_BACK, 
            icon_color = ft.Colors.GREY, 
            icon_size = 40, 
            tooltip = "-", 
            on_click=self.decrease)
        self.value_label = ft.TextField(
            value = f"{self.value}", 
            width = 55, 
            on_change = self.change_value, 
            on_blur = self.set_value)
        self.increase_value = ft.IconButton(
            icon = ft.Icons.ARROW_FORWARD, 
            icon_color = ft.Colors.GREY, 
            icon_size = 40, 
            tooltip = "+", 
            on_click=self.increase)

    def decrease(self, _) -> None:
        if self.value == 1:
            return
        self.value_update(self.value-1)

    def change_value(self, _) -> None:
        if not self.value_label.value:
            return
        try:
            self.value = int(self.value_label.value)
            if self.value < 1:
                self.value_update(1)
            elif self.limit and self.value > self.limit:
                self.value_update(self.limit)
        except ValueError:
            self.value_update(self.value)

    def set_value(self, _) -> None:
        if not self.value_label.value:
            self.value_update(self.default_value)

    def increase(self, _) -> None:
        if self.limit and self.value == self.limit:
            return
        self.value_update(self.value+1)

    def value_update(self, value: int) -> None:
        self.value = value
        self.value_label.value = f'{self.value}'
        self.value_label.update()

    def change_visibility(self, way: bool) -> None:
        self.visible = way
        self.decrease_value.visible, self.value_label.visible, self.increase_value.visible = [self.visible]*3
        self.decrease_value.update(), self.value_label.update(), self.increase_value.update() # pyright: ignore[reportUnusedExpression]


class TriplePaginationRegulator(TripleRegulator):
    def __init__(self, app: App, default_value: int, *limit: int) -> None:
        super().__init__(default_value, *limit)
        self.app = app
        self.page_limit = ft.Text(value = f'/{limit if limit else 1}')

    def change_value(self, _) -> None:
        super().change_value(_)
        self.app.art_mode.create_page() 

    def value_update(self, value: int) -> None:
        super().value_update(value)
        self.app.art_mode.create_page()   

    def change_visibility(self, way: bool) -> None:
        super().change_visibility(way)
        self.page_limit.visible = self.visible
        self.page_limit.update()