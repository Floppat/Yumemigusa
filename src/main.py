import flet as ft
import time

from random import choice
from typing import Optional

from db import DB_Manager
from functional import Tokenizer
from input import InputManager
from tagsearch import TagSearchSuggestion, TagAddSuggestion
from appbar import AppBar
from regulator import TripleRegulator, TriplePaginationRegulator
from artmode import ArtMode
from imagemode import ImageMode
from tagmode import TagMode
from notifications import Notification, ErrorNotification


class App():
    def __init__(self, page: ft.Page, tag_style: dict) -> None:
        self.page = page
        self.tag_style = tag_style
        self.theme = "dark"
        self.banner: Optional[Notification] | None = None
        self.page.on_resize = lambda _: self.window_resize()
        self.page.on_keyboard_event = self.on_keyboard
        # self.page.on_scroll = self.scroll_pos 
        self.scroll_pixes = 0.0
        self.scroll_to = 0.0
        self.sizes = {
            "reimu": 1, 
            "tiny": 2, 
            "small": 3, 
            "normal": 4, 
            "fullscreen": 5}
        self.size = self.sizes["normal"]

        self.db = DB_Manager('db.db')
        self.db.create_tables()

        self.tokenizer = Tokenizer(self, False)
        self.data_input = InputManager(self, False)
        self.searchbar = ft.SearchBar(bar_hint_text = "Search", width = 500)
        self.tag_search = TagSearchSuggestion(self, self.searchbar, 500, 100, 5, True)
        self.tagbar = ft.TextField(hint_text = "введите название тэга", visible = False)
        self.tag_add = TagAddSuggestion(self, self.tagbar, 250, 60, 3, False)
        self.columns_of_arts = TripleRegulator(3)
        self.arts_on_page = TripleRegulator(20)
        self.pagination = TriplePaginationRegulator(self, 1)
        self.art_mode = ArtMode(self)
        self.image_mode = ImageMode(self)
        self.tag_minimum = TripleRegulator(4)
        self.tag_mode = TagMode(self)
        self.appbar = AppBar(self)
        self.error = ErrorNotification(self, '', (('понятно, закрыть', lambda _: self.close_notifications()),))
        
        self.mode = self.art_mode
        self.prev_mode = self.art_mode

        self.tag_search_row = ft.Row([ft.Column([self.tag_search.suggestions]), self.tag_search.padding], alignment = ft.MainAxisAlignment.CENTER, spacing = 0)
        self.label_images_count = ft.Text('0')
        self.row_images_count = ft.Row([ft.Text('entries matching:'), self.label_images_count], alignment = ft.MainAxisAlignment.CENTER)

    def window_resize(self) -> None:
        self.mode.reload()
        if self.mode == self.tag_mode:
            return
        self.tag_mode_padding()
        if self.size == self.sizes['fullscreen']:
            self.appbar.padding.width = 197
            self.appbar.padding.update()
            return
        page_width = int(self.page.width) # pyright: ignore[reportArgumentType]
        if page_width < 778 and self.size > self.sizes["reimu"]:
            self.reimu()
        elif page_width < 957 and self.size > self.sizes["tiny"]:
            self.tiny()
        elif page_width < 1233 and self.size > self.sizes["small"]:
            self.small()
        elif page_width >= 1233 and self.size < self.sizes["normal"]:
            self.not_small()
        elif page_width >= 957 and self.size < self.sizes["small"]:
            self.not_tiny()
        elif page_width >= 778 and self.size < self.sizes["tiny"]:
            self.not_reimu()
        self.appbar.padding.width = 0.4535*(page_width-1362)
        self.appbar.padding.update()
        if not self.page.window.maximized:
            self.tag_search_row.alignment = ft.MainAxisAlignment.END
            self.tag_search_row.update()
            self.tag_search_padding(page_width)
        else:
            self.tag_search_row.alignment = ft.MainAxisAlignment.CENTER
            self.tag_search.padding.width = 0
            self.tag_search.padding.update()
            self.tag_search_row.update()

    def tag_mode_padding(self) -> None:
        if self.size == self.sizes['fullscreen']:
            self.tag_mode.padding.width = 305 # 502
            self.tag_mode.padding.update()
        else:
            self.tag_mode.padding.width = 0.5466*(self.page.width-1362) # pyright: ignore[reportOptionalOperand]
            self.tag_mode.padding.update() #1362 for title # here 305, appbar 253, 558 in total.

    def tag_search_padding(self, page_width: int) -> None:
        padding_width = int(self.appbar.padding.width) # pyright: ignore[reportArgumentType]
        self.tag_search.padding.width = (padding_width if padding_width > 0 else 0) + 450
        if self.size == self.sizes["tiny"]:
            self.tag_search.padding.width = 230
            if page_width >= 780 and page_width <= 820:
                self.tag_search.padding.width += page_width - 780
            else:
                self.tag_search.padding.width += 40
        if self.size == self.sizes["reimu"]:
            self.tag_search.padding.width = padding_width if padding_width > 0 else 0 + 35
            if page_width >= 584 and page_width <= 619:
                self.tag_search.padding.width += page_width - 584
            else:
                self.tag_search.padding.width += 35
        self.tag_search.padding.update()

    def on_keyboard(self, e: ft.KeyboardEvent) -> None:
        if e.key == "F11":
            size = self.sizes["fullscreen"] if not self.size == self.sizes["fullscreen"] else self.sizes["normal"]
            self.not_small()
            self.page.window.full_screen = not self.page.window.full_screen
            self.appbar.close_app.visible = not self.appbar.close_app.visible
            self.size = size
            self.page.update()

    def scroll_pos(self, e: ft.OnScrollEvent):
        self.scroll_pixes = e.pixels

    def invoke_error(self, text: str) -> None:
        self.error.text.value = text
        self.error.visible()

    def close_notifications(self) -> None:
        self.page.pop_dialog()
        self.banner = None

    def softlock(self) -> None | bool:
        if not self.banner:
            return
        if self.banner.lock:
            original_bg = self.banner.notification.bgcolor
            self.banner.notification.bgcolor = ft.Colors.RED
            self.banner.notification.update()
            self.banner.visible()
            time.sleep(0.5)
            self.banner.notification.bgcolor = original_bg
            self.banner.notification.update()
            self.banner.visible()
            return True

    def change_mode(self, mode: ArtMode | ImageMode | TagMode):
        if self.softlock():
            return
        self.close_notifications()
        if self.mode != mode and self.mode != self.prev_mode:
            self.prev_mode = self.mode
        if self.mode != mode:
            self.mode.change_visibility(False)
            self.mode = mode
            self.window_resize()
            mode.change_visibility(True)

    def reload(self):
        match self.mode:
            case self.art_mode:
                self.art_mode.create_page()
            case self.tag_mode:
                self.tag_mode.fetch_cases()

    def small(self) -> None:
        self.page.appbar.title.visible = False # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
        self.page.appbar.leading.visible = False # pyright: ignore[reportOptionalMemberAccess]
        self.page.appbar.update() # pyright: ignore[reportOptionalMemberAccess]
        self.size = self.sizes["small"]

    def not_small(self) -> None:
        self.not_tiny()
        self.page.appbar.title.visible = True # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
        self.page.appbar.leading.visible = True # pyright: ignore[reportOptionalMemberAccess]
        self.page.appbar.update() # pyright: ignore[reportOptionalMemberAccess]
        self.size = self.sizes["normal"]

    def tiny(self) -> None:
        self.small()
        self.appbar.dir_choose.content = "выбрать"
        self.appbar.dir_scan.content = "сканировать"
        self.appbar.dir_choose.update()
        self.appbar.dir_scan.update()
        self.size = self.sizes["tiny"]

    def not_tiny(self) -> None:
        self.not_reimu()
        self.appbar.dir_choose.content = "Выбрать директорию"
        self.appbar.dir_scan.content = "Cканировать директорию"
        self.appbar.dir_choose.update()
        self.appbar.dir_scan.update()
        self.size = self.sizes["small"]

    def reimu(self) -> None:
        self.tiny()
        self.appbar.dir_choose.visible = False
        self.appbar.dir_scan.visible = False
        if not self.appbar.small_presence:
            self.appbar.popupmenu.items = self.appbar.popupmenu.items + self.appbar.small # pyright: ignore[reportOptionalOperand]
            self.appbar.small_presence = True
        self.appbar.dir_choose.update()
        self.appbar.dir_scan.update()
        self.appbar.popupmenu.update()
        self.size = self.sizes["reimu"]

    def not_reimu(self) -> None: # aw that's sad
        self.appbar.dir_choose.visible = True
        self.appbar.dir_scan.visible = True
        if self.appbar.small_presence:
            self.appbar.popupmenu.items.pop(), self.appbar.popupmenu.items.pop(), self.appbar.popupmenu.items.pop() # pyright: ignore[reportOptionalMemberAccess, reportUnusedExpression]
            self.appbar.small_presence = False
        self.appbar.dir_choose.update()
        self.appbar.dir_scan.update()
        self.appbar.popupmenu.update()
        self.size = self.sizes["tiny"]


def main(page: ft.Page) -> None:
    page.title = "Yumemigusa"
    page.window.maximized = True
    page.window.min_width = 600
    page.window.min_height = 200
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.theme_mode = ft.ThemeMode.DARK

    tag_style = { 
        "genre": (ft.Icons.ART_TRACK_SHARP, ft.Colors.GREY_600), 
        "game": (ft.Icons.GAMEPAD, ft.Colors.PURPLE), 
        "anime": (ft.Icons.MOVIE, ft.Colors.BLUE_700), 
        "voicebank": (ft.Icons.HEADPHONES, ft.Colors.BLUE_700), 
        "vtuber": (ft.Icons.PLAY_ARROW, ft.Colors.DEEP_PURPLE), 
        "misc": (ft.Icons.ART_TRACK_SHARP, ft.Colors.GREY_700), 
        "character": (ft.Icons.ACCOUNT_BOX_ROUNDED, ft.Colors.GREEN), 
        "source": (ft.Icons.SOURCE, ft.Colors.LIGHT_BLUE_ACCENT), 
        "tag": (ft.Icons.IMAGE, ft.Colors.GREY), 
        "request": (ft.Icons.ADD_ALERT, ft.Colors.LIGHT_BLUE_ACCENT), 
        "artist": (ft.Icons.ART_TRACK_SHARP, ft.Colors.RED)}

    app = App(page, tag_style)
    page.add(app.tag_search_row)
    page.add(app.row_images_count)
    page.add(ft.Row([app.image_mode.disable, app.image_mode.image, ft.Column([app.image_mode.management_menu.directory, app.tagbar, app.tag_add.suggestions, ft.Row([app.image_mode.management_menu.tags, app.image_mode.manage_tags])])]))
    page.add(ft.Row([app.pagination.decrease_value, app.pagination.value_label, app.pagination.page_limit, app.pagination.increase_value], alignment = ft.MainAxisAlignment.CENTER))
    page.add(app.art_mode.art_grid)
    page.add(app.tag_mode.tag_grid)
    page.add(ft.Row([app.pagination.decrease_value, app.pagination.value_label, app.pagination.page_limit, app.pagination.increase_value], alignment = ft.MainAxisAlignment.CENTER))

    app.art_mode.create_page()

ft.run(main)