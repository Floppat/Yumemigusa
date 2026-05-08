from __future__ import annotations
import flet as ft

from typing import Callable
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import App


class Notification():
    def __init__(self, app: App, text: str, buttons: tuple[tuple[str, Callable], ...], lock: bool = False) -> None:
        self.app = app
        self.text = ft.Text(value = text, color = ft.Colors.WHITE)
        self.notification = ft.Banner(
            content = self.text, 
            actions = [], 
            leading = ft.Icon(ft.Icons.INFO_OUTLINED, color=ft.Colors.PRIMARY))
        for button in buttons:
            self.notification.actions.append(
                ft.TextButton(content = button[0], style = ft.ButtonStyle(color = ft.Colors.BLUE), on_click = button[1]))
        self.lock = lock

    def visible(self) -> None:
        banner = self.app.page.pop_dialog()
        if banner:
            self.app.page._dialogs.controls.clear()
        self.app.page.show_dialog(self.notification)
        self.app.banner = self


class SuccessNotification(Notification):
    def __init__(self, app: App, text: str, buttons: tuple[tuple[str, Callable], ...]) -> None:
        super().__init__(app, text, buttons)
        self.text.color = ft.Colors.BLACK
        self.notification.bgcolor = ft.Colors.GREEN_100
        self.notification.leading = ft.Icon(ft.Icons.CHECK_BOX, color = ft.Colors.GREEN)


class ErrorNotification(Notification):
    def __init__(self, app: App, text: str, buttons: tuple[tuple[str, Callable], ...]) -> None:
        super().__init__(app, text, buttons)
        self.text.color = ft.Colors.BLACK
        self.notification.bgcolor = ft.Colors.AMBER_100
        self.notification.leading = ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color = ft.Colors.AMBER)