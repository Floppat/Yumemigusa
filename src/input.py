from __future__ import annotations
import flet as ft
import threading

from datetime import timedelta as td
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import App

from notifications import Notification, SuccessNotification, ErrorNotification


class InputManager():
        def __init__(self, app: App, tags: bool) -> None:
            self.app = app
            self.tags = tags
            self.estimated = 2 if self.tags else 20
            self.path_picker = PathSelector(app, self, "Что просканировать?")
            self.path_excluder = PathSelector(app, self, "Что добавить в чёрный список?")
            self.path_flagger = PathSelector(app, self, "Чему добавить флаг?")
            self.flags = {}

            self.error = ErrorNotification(self.app, 
                "прежде выберите директорию", 
                (('закрыть', lambda _: self.app.close_notifications()), 
                ('выбрать директорию', self.path_picker.select)))
            self.flag = ft.TextField(hint_text="флаг", width=250, on_submit=self.path_flagger.select)
            self.flag_dialog = Notification(self.app,
                "какой флаг назначить пути?",
                (('добавить флаг', self.path_flagger.select),
                ("отмена", lambda _: (self.path_flagger.selection.clear(), self.status.visible()))))
            self.flag_dialog.notification.actions.insert(0, self.flag)
            self.status = Notification(self.app, 
                "", 
                (("добавить в чёрный список", self.path_excluder.select),
                ("добавить флаг", lambda _: self.flag_dialog.visible()),
                ('начать сканирование', self.scan_directory),
                ('отмена', lambda _: (self.clear_selections(), self.app.close_notifications()))),
                True)
            self.info = Notification(self.app, 
                f"сканирование началось. имейте ввиду что на каждую тысячу записей необходимо примерно {self.estimated} секунд обработки. мы уведомим вас когда закончим", 
                (("понятно, закрыть", lambda _: self.app.close_notifications()),))
            self.success = SuccessNotification(self.app, 
                "", 
                (("обновить страницу", lambda _: self.app.reload()),
                ("понятно, закрыть", lambda _: self.app.close_notifications())))

        def scan_directory(self, _) -> None:
            if not self.path_picker.selection:
                self.error.visible()
                return
            threading.Thread(target=self.scan_thread).start()

        def scan_thread(self) -> None:
            self.info.visible()
            time, found = self.app.tokenizer.scan()
            found = found if found > 0 else 1
            self.success.text.value = f"сканирование завершено. сканирование заняло: {td(seconds=round(time.total_seconds()))}, добавлено {found} записей. всего то {round(time/td(seconds=(found/1000)*self.estimated), 2)} раз(а) ожидания от того что мы предсказали."
            self.success.visible()
            self.clear_selections()

        def clear_selections(self):
            self.path_picker.selection.clear()
            self.path_excluder.selection.clear()
            self.path_flagger.selection.clear()
            self.flags.clear()
            self.flag.value = ''

        def create_status(self) -> None:
            excluded = f'\nПропускаем: {"; ".join(self.path_excluder.selection)}' if self.path_excluder.selection else ''
            flagged = '\nФлаги:' if self.flags else ''
            for flag in self.flags.keys():
                flagged+= f'  \n{flag}: {"; ".join(self.flags[flag])}'
            self.status.text.value = f"Выбрана директория {"; ".join(self.path_picker.selection)}"+excluded+flagged
            self.status.visible()

        def selected(self) -> None:
            if self.flag.value and self.path_flagger.selection:
                if self.flag.value not in self.flags.keys():
                    self.flags[self.flag.value] = []
                if self.path_flagger.selection[-1] not in self.flags[self.flag.value]:
                    self.flags[self.flag.value].append(self.path_flagger.selection[-1])
            self.create_status()

        def change_mode(self) -> None:
            self.tags = not self.tags
            self.app.tokenizer.tags = not self.app.tokenizer.tags 
            self.estimated = 2 if self.tags else 20
            self.info.text.value = f"сканирование началось. имейте ввиду что на каждую тысячу записей необходимо примерно {self.estimated} секунд обработки. мы уведомим вас когда закончим"

class PathSelector():
    def __init__(self, app: App, input_manager: InputManager, dialog_title: str) -> None:
        self.app = app
        self.input_manager = input_manager
        self.dialog_title = dialog_title
        self.dialog_window = ft.FilePicker()
        self.selection = []

    async def select(self, _) -> None:
        path = await self.dialog_window.get_directory_path(self.dialog_title)
        if not path:
            return
        if path not in self.selection:
            self.selection.append(path)
        self.input_manager.selected()