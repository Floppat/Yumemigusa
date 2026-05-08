from __future__ import annotations
import re
import datetime
import random

from pathlib import Path
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import App


class Tokenizer():
    def __init__(self, app: App, tags: bool) -> None:
        self.app = app
        self.tags = tags
        self.unexpected_cases = {}
        self.the_great_golden_list = []
        self.unexpected_cases_rezero()

    def scan(self) -> tuple[datetime.timedelta, int]:
        self.unexpected_cases_rezero()
        now = datetime.datetime.now()
        self.app.db.open_connection()
        for flag in self.app.data_input.flags.keys():
            flag_id = self.app.db.get_PK('tags', 'tag', flag)
            if not flag_id:
                self.app.db.new_tag(flag, self.app.db.get_PK('types', 'type', 'tag'))
        for path in self.app.data_input.path_picker.selection:
            for cur_dir, _, files in Path(path).walk():
                if any(cur_dir.name.startswith(parent) for parent in self.app.data_input.path_excluder.selection):
                    continue
                flag_id = None
                for flag in self.app.data_input.flags.keys():
                    if any(cur_dir.name.startswith(parent) for parent in self.app.data_input.flags[flag]):
                        flag_id = self.app.db.get_PK('tags', 'tag', flag)
                for file in files:
                    self.clean_path(Path(file), cur_dir, flag_id)
        len_to_return = len(self.the_great_golden_list) if not self.tags else sum([len(self.unexpected_cases[case]) for case in self.unexpected_cases])
        if not self.tags:
            self.the_great_golden_randomizer()
            self.the_great_golden_list.clear()
        self.app.db.close_connection()
        now2 = datetime.datetime.now()
        return now2-now, len_to_return

    def clean_path(self, item: Path, cur_dir: Path, flag_id: int | None) -> None:
        if item.suffix not in ['.png', '.jpg']:
            return
        if '.full.' in item.name:
            tags = self.fetch_zerochan(re.sub(r'.full.\d+.[^.]+', '', item.name.lower()).split('.'))
            source = 'zerochan'
        elif 'yande.re' in item.name:
            tags = self.fetch_yandere([" ".join(tag.split("_")) for tag in item.name.split('.')[1].split(" ")[2:]] or [" ".join(tag.split("_")) for tag in item.name.split('.')[1].split("_")[2:]])
            source = 'yande.re'
        elif re.search('^__', item.name) and len(item.name.split('__')[2].removesuffix(re.sub(r'.*(\.[^.]+)$', r'\1', item.name))) == 32:
            tokens = item.name.split('__')[1]
            if not tokens.startswith('drawn'):
                characters = re.sub(r'_drawn_by[^.]+', '', tokens)
                characters = re.sub(r'_and_\d+_more', '', characters)
                characters = re.sub(r'_and', '', characters)
                tags = self.fetch_danbooru(characters.split('_'))
                artist = ' '.join(tokens.split('_drawn_by_')[-1].split('_'))
                artist_id = self.app.db.get_PK('tags', 'tag', artist)
                if not artist_id:
                    artist_id = self.app.db.new_tag(artist, self.app.db.get_PK('types', 'type', 'artist'))
                if tags:
                    tags.append(artist_id)
                else:
                    tags = [artist_id]
            else:
                artist = ' '.join(tokens.split('drawn_by_')[-1].split('_'))
                artist_id = self.app.db.get_PK('tags', 'tag', artist)
                if not artist_id:
                    artist_id = self.app.db.new_tag(artist, self.app.db.get_PK('types', 'type', 'artist'))
                tags = [artist_id]
            source = 'danbooru'
        elif len(item.name) == 19 and re.match(r'[^0-9]+', item.name):
            tags = None
            source = 'x (probably)'
        elif 'RDT_' in item.name:
            tags = None
            source = 'reddit'
        else:
            tags = None
            source = 'no source'
        if self.tags:
            return
        if flag_id:
            if tags:
                tags.append(flag_id)
            else:
                tags = [flag_id]
        self.add_fetched_image(item, cur_dir, tags, source)

    def add_fetched_image(self, item: Path, cur_dir: Path, tags: list[int] | None, source: str | None) -> None:
        source_id = None
        if source:
            source_id = self.app.db.get_PK('tags', 'tag', source)
        if tags:
            tags.append(source_id) # pyright: ignore[reportArgumentType]
            self.the_great_golden_list.append(((cur_dir / item, tags)))
            return
        self.the_great_golden_list.append(((cur_dir / item, [source_id])))

    def the_great_golden_randomizer(self) -> None:
        random.shuffle(self.the_great_golden_list)
        for data in self.the_great_golden_list:
            self.app.db.new_image(str(data[0]), data[1])

    def fetch_zerochan(self, tokens: list[str] | str) -> list[int] | None:
        for i, item in enumerate(tokens):
            if item.startswith('('):
                tokens = ' '.join(tokens[:i])
        if not isinstance(tokens, str):
            tokens = ' '.join(tokens)
        found_tags = self.app.db.get_PK("tags", "tag", tokens)
        if not found_tags:
            self.unexpected_case(tokens, "zerochan")
        return [found_tags] if found_tags else None

    def fetch_yandere(self, tokens: list[str]) -> list[int] | None:
        found_tags = []
        for candidate in tokens:
            fetch = self.app.db.get_PK('tags', 'tag', candidate) or self.app.db.get_alt(candidate, 'yande.re')
            if not fetch:
                self.unexpected_case(candidate, "yande.re")
                continue
            if fetch not in found_tags:
                found_tags.append(fetch)
        return found_tags if found_tags else None

    def fetch_danbooru(self, tokens:list[str]) -> list[int] | None:
        found_tags = []
        iteration = 0
        while iteration < len(tokens):
            matched = False
            for size in range(min(3, len(tokens) - iteration), 0, -1):
                candidate = ' '.join(tokens[iteration:iteration+size])
                fetch = self.app.db.get_PK('tags', 'tag', candidate) or self.app.db.get_alt(candidate, 'danbooru')
                if not fetch:
                    if size == 1:
                        self.unexpected_case(candidate, "danbooru")
                    continue
                if fetch not in found_tags:
                    found_tags.append(fetch)
                iteration += size
                matched = True
                break
            if not matched:
                iteration += 1
        return found_tags if found_tags else None

    def unexpected_case(self, case: str, source: str) -> None:
            self.unexpected_cases[source][case] = self.unexpected_cases[source].get(case, 0)+1

    def unexpected_cases_rezero(self):
        self.unexpected_cases.clear()
        self.unexpected_cases.setdefault("zerochan", {})
        self.unexpected_cases.setdefault("danbooru", {})
        self.unexpected_cases.setdefault("yande.re", {})

    def change_mode(self) -> None:
        self.tags = not self.tags