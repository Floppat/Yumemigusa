import sqlite3
import datetime
import threading


class DB_Manager:
    def __init__(self, database_name: str) -> None:
        self.database = database_name
        self._local = threading.local()

    def create_tables(self) -> None:
        con = self.open_connection()
        con.execute('''
            CREATE TABLE IF NOT EXISTS images(
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                image TEXT UNIQUE NOT NULL );''')
        con.execute('''
            CREATE TABLE IF NOT EXISTS types(
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                type TEXT UNIQUE NOT NULL );''')
        con.execute('''
            CREATE TABLE IF NOT EXISTS tags(
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                tag TEXT UNIQUE NOT NULL, 
                type_id INTEGER NOT NULL, 
                FOREIGN KEY(type_id) REFERENCES types(id) ON DELETE CASCADE );''')
        con.execute('''
            CREATE TABLE IF NOT EXISTS tags_alts(
                tag_id INTEGER NOT NULL, 
                alt TEXT NOT NULL, 
                source_id INTEGER NOT NULL, 
                FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE, 
                FOREIGN KEY(source_id) REFERENCES tags(id) ON DELETE CASCADE, 
                UNIQUE(tag_id, alt, source_id) );''')
        con.execute('''
            CREATE TABLE IF NOT EXISTS tags_parents(
                tag_id INTEGER UNIQUE NOT NULL, 
                parent_id INTEGER NOT NULL, 
                FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE, 
                FOREIGN KEY(parent_id) REFERENCES tags(id) ON DELETE CASCADE );''')
        con.execute('''
            CREATE TABLE IF NOT EXISTS tags_childs(
                tag_id INTEGER NOT NULL, 
                child_id INTEGER NOT NULL, 
                FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE, 
                FOREIGN KEY(child_id) REFERENCES tags(id) ON DELETE CASCADE, 
                UNIQUE(tag_id, child_id) );''')
        con.execute('''
            CREATE TABLE IF NOT EXISTS images_tags(
                image_id INTEGER NOT NULL, 
                tag_id INTEGER NOT NULL, 
                FOREIGN KEY(image_id) REFERENCES images(id) ON DELETE CASCADE, 
                FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE, 
                UNIQUE(image_id, tag_id) );''')
        con.execute('''
            CREATE TABLE IF NOT EXISTS images_tags_primary(
                image_id INTEGER UNIQUE NOT NULL, 
                tag_id INTEGER NOT NULL, 
                FOREIGN KEY(image_id) REFERENCES images(id) ON DELETE CASCADE, 
                FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE );''')
        con.commit()
        self.close_connection()

    def open_connection(self) -> sqlite3.Connection:
        self.threading_connection()
        self._local._depth+=1
        if self._local.connection:
            return self._local.connection
        self._local.connection = sqlite3.connect(self.database)
        return self._local.connection

    def close_connection(self) -> None:
        self.threading_connection()
        if self._local._depth == 0:
            return
        self._local._depth-=1 
        if self._local.connection and self._local._depth == 0:
            self._local.connection.close()
            self._local.connection = None

    def threading_connection(self)-> None:
        if not hasattr(self._local, 'connection'):
            self._local.connection = None
            self._local._depth = 0
            self._local._recur = 0

    def new_image(self, image: str, tags: list[int]) -> None: 
        cur_img_id = None
        con = self.open_connection()
        try:
            cursor = con.execute('INSERT INTO images (image) VALUES(?);', (image,))
            con.commit()
            cur_img_id = cursor.lastrowid
        except sqlite3.IntegrityError as e:
            print(f"Log:{datetime.datetime.now()}; unable to add image '{image}' to libary: already added\n{e}")
        if not cur_img_id:
            cur_img_id = self.get_PK('images', 'image', image)
        if tags:
            self.new_image_tags(cur_img_id, tags)
            image_tags = self.get_tags(cur_img_id)
            tags_tags = [tag[0] for tag in image_tags]
            tags_types = [tag[1] for tag in image_tags]
            if "no source" in tags_tags:
                return
            if "artist" not in tags_types:
                self.new_image_tags(cur_img_id, [self.get_PK('tags', 'tag', 'artist request')])
            if "character" not in tags_types:
                self.new_image_tags(cur_img_id, [self.get_PK('tags', 'tag', 'character request')])
                if "title" not in tags_types:
                    self.new_image_tags(cur_img_id, [self.get_PK('tags', 'tag', 'misc')])
            self.update_primary(cur_img_id, image_tags)
        self.close_connection()

    def new_type(self, type: str) -> None:
        con = self.open_connection()
        con.execute('INSERT INTO types (type) VALUES(?);', (type,))
        con.commit()
        self.close_connection()

    def new_tag(self, tag: str, type_id: int, **kwargs) -> int:
        parent_id = kwargs.get('parent', None)
        childs_id = kwargs.get('childs', None)
        cur_tag_id = None

        con = self.open_connection()
        try:
            cursor = con.execute('INSERT INTO tags (tag, type_id) VALUES(?, ?);', (tag, type_id))
            con.commit()
            cur_tag_id = cursor.lastrowid
        except sqlite3.IntegrityError as e:
            print(f"Log:{datetime.datetime.now()}; unable to create tag '{tag}': already created\n{e}")
        if kwargs:
            if not cur_tag_id:
                cur_tag_id = self.get_PK('tags', 'tag', tag)
            if parent_id:
                self.new_tag_parent(cur_tag_id, parent_id)
            if childs_id:
                self.new_tag_childs(cur_tag_id, childs_id)
            elif not parent_id and not childs_id:
                print(f"Log:{datetime.datetime.now()}; unable add to {tag} tag bond {kwargs}: tags are supplied not correctly")
        self.close_connection()
        return cur_tag_id if cur_tag_id else False

    def new_tag_alt(self, tag_id: int, alt: str, source_id: int) -> None:
        con = self.open_connection()
        try:
            con.execute('INSERT INTO tags_alts VALUES(?, ?, ?);', (tag_id, alt, source_id))
            con.commit()
        except sqlite3.IntegrityError as e:
            print(f"Log:{datetime.datetime.now()}; unable to assign alt tag '{alt}' for source with id '{source_id}' to tag with id '{tag_id}': already assigned\n{e}")
        self.close_connection()

    def new_tag_parent(self, tag_id: int, parent_id: int) -> None:
        con = self.open_connection()
        try:
            con.execute('INSERT INTO tags_parents VALUES(?, ?);', (tag_id, parent_id))
            con.execute('INSERT INTO tags_childs VALUES(?, ?);', (parent_id, tag_id))
            con.commit()
        except sqlite3.IntegrityError as e:
            print(f"Log:{datetime.datetime.now()}; unable to assign parent tag '{parent_id}' to '{tag_id}': some parent tag already assigned\n{e}")
        self.close_connection()

    def new_tag_childs(self, tag_id: int, childs: list[int]) -> None:
        con = self.open_connection()
        for child in childs:
            try:
                con.execute('INSERT INTO tags_childs VALUES(?, ?);', (tag_id, child))
            except sqlite3.IntegrityError as e:
                print(f"Log:{datetime.datetime.now()}; unable to assign child tag '{child}' to tag with id '{tag_id}': already assigned\n{e}")
        con.commit()
        self.close_connection()

    def new_image_tags(self, image_id: int, tags: list[int]) -> None:
        self._local._recur += 1
        con = self.open_connection()
        for tag in tags:
            try:
                con.execute('INSERT INTO images_tags VALUES(?, ?);', (image_id, tag))
            except sqlite3.IntegrityError as e:
                pass # print(f"Log:{datetime.datetime.now()}; unable to assign tag '{tag}' to image '{image}': already assigned\n{e}")
        for tag in tags:
            if parent := con.execute('SELECT parent_id FROM tags_parents WHERE tag_id = ?;', (tag,)).fetchall():
                if con.execute('SELECT type_id FROM tags WHERE id = ?;', (tag,)).fetchall()[0][0] == self.get_PK('types', 'type', 'meta'):
                    continue
                self.new_image_tags(image_id, [parent[0][0]])
        if self._local._recur == 1:
            self.update_primary(image_id)
            con.commit()
        self.close_connection()
        self._local._recur -= 1

    def new_primary(self, image_id: int, primary: int) -> None:
        con = self.open_connection()
        result = con.execute(f'SELECT tag_id FROM images_tags_primary WHERE image_id = ?;', (image_id,)).fetchall()
        if result:
            con.execute('UPDATE images_tags_primary SET tag_id = ? WHERE image_id = ?;', (primary, image_id))
        else:
            con.execute('INSERT INTO images_tags_primary VALUES(?, ?);', (image_id, primary))
        con.commit()
        self.close_connection()

    def remove_tag(self, image_id: int, tag_id: int) -> None:
        con = self.open_connection()
        con.execute(f'DELETE FROM images_tags WHERE image_id = ? AND tag_id = ?;', (image_id, tag_id))
        con.commit()
        self.close_connection()

    def read(self, table: str, col_name: str, PK: str | int, *columns: str) -> list:
        con = self.open_connection()
        result = ((con.execute(f'SELECT {', '.join(columns)} FROM {table} WHERE {col_name} = ?;', (PK,))).fetchall())[0]
        self.close_connection()
        return result

    def read_types(self) -> list:
        con = self.open_connection()
        result = con.execute('SELECT * from types').fetchall()
        self.close_connection()
        return result

    def get_PK(self, table: str, col_name: str, col_content: int | str, *pk_col: str) -> int | bool:
        con = self.open_connection()
        result = con.execute(f'SELECT {'id' if not pk_col else pk_col[0]} FROM {table} WHERE {col_name} = ?;', (col_content,)).fetchall()
        self.close_connection()
        return result[0][0] if len(result) > 0 else False

    def get_alt(self, candidate: str, source: str) -> int | bool:
        con = self.open_connection()
        source_id = self.get_PK('tags', 'tag', source)
        result = con.execute(f'SELECT tag_id FROM tags_alts WHERE alt = ? AND source_id = ?;', (candidate, source_id)).fetchall()
        self.close_connection()
        return result[0][0] if len(result) > 0 else False

    def get_tags(self, image: int) -> list[tuple[str, str, str, int]]:
        con = self.open_connection()
        result = con.execute('''
        SELECT tags_master.tag, types.type, tags_parent.tag, tags_master.id
        FROM tags tags_master
        JOIN images_tags ON images_tags.tag_id = tags_master.id
        JOIN images ON images.id = images_tags.image_id
        JOIN types ON types.id = tags_master.type_id
        LEFT JOIN tags_parents ON tags_parents.tag_id = tags_master.id
        LEFT JOIN tags tags_parent ON tags_parent.id = tags_parents.parent_id
        WHERE images.id =?;''', (image,)).fetchall()
        self.close_connection()
        return result

    def get_tag_info(self, tags: list):
        con = self.open_connection()
        result = []
        for tag in tags:
            result.append(con.execute('''
                SELECT types.type
                FROM tags
                JOIN types ON types.id = tags.type_id
                WHERE tags.tag = ?;''', (tag,)).fetchall()[0][0])
        self.close_connection()
        return result

    def filter(self, tags: tuple[str, ...], blacklist: tuple[str, ...], page: int, page_size: int, strict_mode: bool, reverse_strict: bool) -> tuple[list, int]:
        current_page = []
        offset = page*page_size - page_size
        strict_join = ''
        strict_condition = ''
        tags_query = ''
        blacklist_query = ''
        
        if len(tags) > 0:
            if strict_mode:
                tag = sorted([tag if self.read("tags", "tag", tag, "type_id")[0] in (self.get_PK("types", "type", "title"), self.get_PK("types", "type", "character")) else '' for tag in tags], reverse=True)
                strict_join = '''LEFT JOIN images_tags_primary on images_tags_primary.tag_id = tags.id'''
                strict_condition = f'''
                    AND images_tags.image_id {"NOT" if reverse_strict else ''} IN (SELECT images_tags_primary.image_id
                        FROM images_tags_primary 
                        WHERE images_tags_primary.tag_id = (
                            SELECT tags.id
                            FROM tags
                            WHERE tags.tag = "{tag[0]}"))'''
            tags_query = f'''
            JOIN tags ON tags.id = images_tags.tag_id
            {strict_join}
            WHERE tags.tag IN {tags if len(tags) > 1 else f'("{tags[0]}")'}
            {strict_condition}
            GROUP BY images_tags.image_id
            HAVING COUNT(DISTINCT images_tags.tag_id) = {len(tags)}'''
        if len(blacklist) > 0:
            blacklist_query = f'''
            images_tags.image_id NOT IN (
                SELECT images_tags.image_id
                FROM images_tags
                JOIN tags on tags.id = images_tags.tag_id
                WHERE tags.tag IN {blacklist if len(blacklist) > 1 else f'("{blacklist[0]}")'})'''
        SQL_query = f'''
        SELECT images.image, images.id
        FROM images
        JOIN images_tags ON images_tags.image_id = images.id
        {tags_query}
        {"AND" if tags_query and blacklist else "WHERE" if blacklist else ""}
        {blacklist_query}
        {"GROUP BY images_tags.image_id" if not tags_query else ""}
        ORDER BY images.id DESC
        LIMIT {page_size}
        OFFSET {offset};'''
        con = self.open_connection()
        for row in con.execute(SQL_query):
            current_page.append((row[0], row[1]))
        if not current_page:
            self.close_connection()
            raise ValueError
        count = con.execute(f'''
        SELECT COUNT(*) 
        FROM(SELECT images_tags.image_id
            FROM images_tags 
            {tags_query}
            {"AND" if tags_query and blacklist else "WHERE" if blacklist else ""}
            {blacklist_query}
            {"GROUP BY images_tags.image_id" if not tags_query else ""});''').fetchall()[0][0]
        self.close_connection()
        return current_page, int(count)

    def search_hint(self, input: str) -> list:
        con = self.open_connection()
        exact_tag = con.execute(self.get_tag_query(f'= "{input}"', 1)).fetchall()
        tag_hint = self.hint_tag(input)
        tags = con.execute(self.get_tag_query(f'LIKE "%{"%".join(input)}%"', 30)).fetchall()
        if tag_hint and tag_hint[0] in tags:
            tags.remove(tag_hint[0])
        tags = (exact_tag if exact_tag and exact_tag[0] not in tag_hint else [])+tag_hint+tags
        hint = []
        for tag in tags:
            if tag[2] == 'title':
                hint.append((tag[0], tag[1], self.read('tags', 'id', self.get_PK('tags_parents', 'tag_id', tag[0], 'parent_id'), 'tag')[0], tag[3]))
            else:
                hint.append(tag)
        self.close_connection()
        return hint

    def hint_tag(self, tag: str) -> list:
        con = self.open_connection()
        result = con.execute(self.get_tag_query(f'LIKE "%{tag}%"', 1)).fetchall()
        self.close_connection()
        return result

    def get_tag_query(self, param: str, limit: int):
        return f'''
        SELECT tags.id, tags.tag, types.type, COUNT(images_tags.tag_id)
        FROM tags
        JOIN types ON types.id = tags.type_id
        LEFT JOIN images_tags ON images_tags.tag_id = tags.id 
        WHERE tag {param}
        GROUP BY tags.id
        ORDER BY COUNT(images_tags.tag_id) DESC
        LIMIT {limit};'''

    def update_primary(self, image_id: int, *tags: list):
        primary_type = ''
        image_tags = tags[0] if tags else self.get_tags(image_id)
        tags_tags = [tag[0] for tag in image_tags]
        tags_types = [tag[1] for tag in image_tags]
        if "request" in tags_types:
            if 'character' in tags_types and 'character request' in tags_tags:
                self.remove_tag(image_id, self.get_PK("tags", "tag", "character request"))
            if 'artist' in tags_types and 'artist request' in tags_tags:
                self.remove_tag(image_id, self.get_PK("tags", "tag", "artist request"))
        if tags_types.count('character') == 1:
            primary_type = 'character'
        elif tags_types.count('title') == 1:
            primary_type = 'title'
        if not primary_type:
            return
        for tag in image_tags:
            if tag[1] == primary_type:
                self.new_primary(image_id, tag[3])

    def export_characters(self) -> tuple[list, ...]:
        con = self.open_connection()
        types = con.execute('SELECT type FROM types').fetchall()
        tags = con.execute('SELECT tag, type_id FROM tags').fetchall()
        alts = con.execute('SELECT * FROM tags_alts').fetchall()
        parents = con.execute('SELECT * FROM tags_parents').fetchall()
        self.close_connection()
        return types, tags, alts, parents

    def import_characters(self, types: list, tags: list, alts: list, parents: list) -> None:
        con = self.open_connection()
        con.executemany('INSERT INTO types (type) VALUES(?)', types)
        con.executemany('INSERT INTO tags (tag, type_id) VALUES(?, ?)', tags)
        con.executemany('INSERT INTO tags_alts VALUES(?, ?, ?)', alts)
        con.commit()
        self.close_connection()
        for i in parents:
            self.new_tag_parent(i[0], i[1])


if __name__ == '__main__':
    database= 'db.db'
    def main():
        db = DB_Manager('temp/db_new.db')
        # db.create_tables()
        types, tags, alts, parents = db.export_characters()

        db2 = DB_Manager(database)
        db2.create_tables()
        db2.import_characters(types, tags, alts, parents)

        with open('logs/character_data_newsys.txt', 'w') as f:
            f.write(str((types, tags, parents)))
    main()