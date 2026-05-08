from __future__ import annotations
import flet as ft

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import App


class AppBar():
    def __init__(self, app: App) -> None:
        self.app = app
        self.mode_button = ft.IconButton(icon = ft.Icons.ART_TRACK_SHARP, on_click = lambda _: self.app.change_mode(self.app.tag_mode))
        self.padding = ft.Text(width = 0.4535*(self.app.page.width-1362)) # pyright: ignore[reportOptionalOperand]
        self.popupmenu = ft.PopupMenuButton(items=[
            ft.PopupMenuItem(content = ft.Row(width=145)), 
            ft.PopupMenuItem(content = "column count"), 
            ft.PopupMenuItem(content = ft.Row([self.app.columns_of_arts.decrease_value, self.app.columns_of_arts.value_label, self.app.columns_of_arts.increase_value], alignment=ft.MainAxisAlignment.CENTER)), 
            ft.PopupMenuItem(), 
            ft.PopupMenuItem(content = "arts count"), 
            ft.PopupMenuItem(content = ft.Row([self.app.arts_on_page.decrease_value, self.app.arts_on_page.value_label, self.app.arts_on_page.increase_value], alignment = ft.MainAxisAlignment.CENTER)), 
            ft.PopupMenuItem(), 
            ft.PopupMenuItem(
                content = ft.Row([
                    ft.IconButton(
                        icon = ft.Icons.REPLAY, 
                        icon_color = ft.Colors.GREY, 
                        icon_size = 40, 
                        tooltip = "обновить страницу", 
                        on_click = lambda _: self.app.art_mode.create_page()), 
                    ft.IconButton(
                        icon = ft.Icons.ARROW_BACK, 
                        icon_color = ft.Colors.GREY, 
                        icon_size = 40, 
                        tooltip = "прошлый набор тэгов", 
                        on_click = self.last_selection)], 
                alignment = ft.MainAxisAlignment.CENTER)),
            ft.PopupMenuItem(
                content = ft.Row([
                    ft.Button("strict mode", on_click=self.app.art_mode.change_mode),
                    ft.Button("reverse mode", on_click=self.app.art_mode.reverse_mode)],
                    alignment = ft.MainAxisAlignment.CENTER,
                    width=145))])
        self.dir_choose = ft.Button(
                    "Выбрать директорию", 
                    icon = ft.Icons.FOLDER_OPEN, 
                    on_click = self.app.data_input.path_picker.select)
        self.dir_scan = ft.Button("Cканировать директорию", on_click=self.app.data_input.scan_directory)
        self.theme_button = ft.IconButton(ft.Icons.MODE_NIGHT, on_click = self.change_theme)
        self.close_app = ft.Button("exit", on_click = self.app.page.window.close)
        self.small_dir = ft.PopupMenuItem()
        self.small_dir_choose = ft.Button(
                    "Выбрать директорию", 
                    icon = ft.Icons.FOLDER_OPEN, 
                    on_click = lambda _: self.app.data_input.path_picker.select("Выберите директорию для сканирования"))
        self.small_dir_scan = ft.Button("Cканировать директорию", on_click=self.app.data_input.scan_directory)
        self.small = [self.small_dir, ft.PopupMenuItem(content = self.small_dir_choose), ft.PopupMenuItem(content = self.small_dir_scan)]
        self.small_presence = False

        self.app.page.appbar = ft.AppBar(
            leading = ft.Icon(ft.Icons.IMAGE), 
            leading_width = 40, 
            title = ft.Text("Yumemigusa"), 
            center_title = False, 
            bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST, 
            actions = [
                self.mode_button, 
                app.tag_mode.padding, 
                app.searchbar, 
                self.padding, 
                self.popupmenu, 
                self.dir_choose, 
                self.dir_scan, 
                self.theme_button, 
                self.close_app])

    def change_theme(self, _) -> None:
        if self.app.page.theme_mode == ft.ThemeMode.DARK:
            self.app.page.theme_mode = ft.ThemeMode.LIGHT
            self.theme_button.icon = ft.Icons.WB_SUNNY_OUTLINED
            self.app.theme = "light"
        else:
            self.app.page.theme_mode = ft.ThemeMode.DARK
            self.theme_button.icon = ft.Icons.MODE_NIGHT
            self.app.theme = "dark"
        if self.app.image_mode.visible:
            self.app.image_mode.management_menu.tags.controls = self.app.image_mode.process_tags()
        if self.app.tag_search.suggestions.visible:
            self.app.tag_search.on_field_change(_)
        self.app.page.update()
        self.theme_button.update()

    def last_selection(self, _) -> None:
        self.app.searchbar.value = ", ".join(self.app.tag_search.previous_selection)
        self.app.searchbar.update()