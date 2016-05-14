from __future__ import division
from core.utils import *
from core.errors import *

attrs = {"+":"adds","?":"needs","?!":"unneeds"}

class Item:
    def __init__(self,name):
        self.name = name

class Character:
    def __init__(self, screen):
        self.reset()
        self.screen = screen

    def reset(self):
        self.inventory = []
        self.name = ""

    def _add_item(self, item):
        self.inventory.append(Item(item))

    def add_items(self, items):
        for item in items:
            self._add_item(item)

    def has(self, item):
        if type(item) == list:
            for a in item:
                if a not in self.inventory_ids():
                    return False
            return True
        else:
            return item in self.inventory_ids()

    def unhas(self, item):
        if type(item) == list:
            for a in item:
                if a in self.inventory_ids():
                    return False
            return True
        else:
            return item not in self.inventory_ids()

    def show_inventory(self):
        self.screen.show_inventory(self.inventory)

    def inventory_ids(self):
        return [item.name for item in self.inventory]

class AVE:
    def __init__(self, folder="games"):
        from screen import Screen
        self.screen = Screen()
        self.character = Character(self.screen)
        self.games = Games(folder, self.screen, self.character)

    def start(self):
        self.screen.print_titles()
        game_to_load = self.screen.menu(self.games.titles(), 8)
        self.games[game_to_load].load()
        again = True
        while again:
            again = False
            try:
                self.games[game_to_load].begin()
            except AVEGameOver:
                next = self.screen.gameover()
                if next == 0:
                    again = True
                if next == 2:
                    raise AVEQuit
                

    def exit(self):
        self.screen.close()

class Games:
    def __init__(self, folder, screen, character):
        import os
        self.screen = screen
        self.character = character
        self.path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.join("..",folder))
        self.games = []
        for game in os.listdir(self.path):
            if ".ave" in game:
                g = Game(os.path.join(self.path,game), self.screen, self.character)
                if g.active:
                    self.games.append(Game(os.path.join(self.path,game), self.screen, self.character))

    def titles(self):
        return [g.title for g in self.games]

    def descriptions(self):
        return [g.description for g in self.games]

    def titles_and_descriptions(self):
        return zip(self.titles(),self.descriptions())

    def game(self,n):
        return self.games[n]

    def __getitem__(self,n):
        return self.games[n]

class Game:
    def __init__(self, path, screen, character):
        self.screen = screen
        self.character = character
        self.path = path
        self.title = ""
        self.description = ""
        self.active = True
        self.rooms = {}
        with open(path) as f:
            for line in f.readlines():
                line = clean(line)
                if len(line) > 0 and line[0] == "#":
                    break
                if line[:2] == "==" == line[-2:]:
                    self.title = clean(line[2:-2])
                if line[:2] == "--" == line[-2:]:
                    self.description = clean(line[2:-2])
                if line[:2] == "~~" == line[-2:]:
                    if clean(line[2:-2]) == "off":
                        self.active = False

    def load(self):
        self.screen.clear()
        rooms = {}
        preamb = True
        with open(self.path) as f:
            for line in f.readlines() + ["#"]:
                if line[0]=="#":
                    if not preamb:
                        rooms[c_room] = Room(c_room, c_txt, c_options, self.screen, self.character)
                    preamb = False
                    while len(line) > 0 and line[0] in ["#"]:
                        line = line[1:]
                    c_room = clean(line)
                    c_txt = []
                    c_options = []
                elif not preamb and clean(line) != "":
                    if "=>" in line:
                        lsp = line.split("=>")
                        next_option = {'id':"",'option':"",'needs':[],'unneeds':[],'adds':[]}
                        next_option['option'] = clean(lsp[0])
                        lsp = clean(lsp[1]).split()
                        next_option['id'] = clean(lsp[0])
                        for i in range(1,len(lsp),2):
                            for a,b in attrs.items():
                                if lsp[i] == a:
                                    next_option[b].append(lsp[i+1])
                        c_options.append(next_option)
                    else:
                        next_line = {'text':"",'needs':[],'unneeds':[],'adds':[]}
                        text = line
                        for a in attrs:
                            text = text.split(" "+a)[0]
                        next_line['text'] = clean(text)
                        lsp = line.split()
                        for i in range(len(lsp)-1):
                            for a,b in attrs.items():
                                if lsp[i] == a:
                                    next_line[b].append(lsp[i+1])
                        c_txt.append(next_line)
        self.rooms = rooms

    def __getitem__(self, id):
        return self.load_room(id)

    def load_room(self, id):
        if id == "__GAMEOVER__":
            raise AVEGameOver
        try:
            return self.rooms[id]
        except KeyError:
            return self.fail_room()

    def begin(self):
        room = self['start']
        while True:
            self.screen.clear()
            next = room.show()
            room = self[next]

    def fail_room(self):
        return Room("fail", "You fall off the edge of the game. GAME OVER", {"__GAMEOVER__":"Continue"}, self.screen)


class Room:
    def __init__(self, id, text, options, screen, character):
        self.id = id
        self.text = text
        self.options = options
        self.screen = screen
        self.character = character

    def __str__(self):
        return "Room with id " + self.id

    def show(self):
        from core.screen import WIDTH
        stuff = []
        included_lines = []
        for line in self.text:
            if self.character.has(line['needs']) and self.character.unhas(line['unneeds']):
                self.character.add_items(line['adds'])
                included_lines.append(line['text'])
        for i,c in enumerate(" ".join(included_lines)):
            stuff.append((i // (WIDTH-22), i % (WIDTH-22), c))
        self.screen.type(stuff)

        opts = []
        adds = []
        ids = []
        for option in self.options:
            if self.character.has(option['needs']) and self.character.unhas(option['unneeds']):
                opts.append(option['option'])
                adds.append(option['adds'])
                ids.append(option['id'])
        self.character.show_inventory()
        num = self.screen.menu(opts, add=adds, y=min(8,len(self.options)), character=self.character)
        return ids[num]
