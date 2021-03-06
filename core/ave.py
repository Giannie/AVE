from __future__ import division
from core.utils import *
from core.errors import *

attrs = {"+":"adds","?":"needs","?!":"unneeds","~":"rems"}

class Item:
    def __init__(self, name, character):
        self.name = name
        self.character = character

    def get_name(self):
        if self.name in self.character.items:
            name = []
            for line in self.character.items[self.name][0]:
                if self.character.has(line['needs']) and self.character.unhas(line['unneeds']):
                    #self.character.add_items(line['adds'])
                    #self.character.remove_items(line['rems'])
                    name.append(line['name'])
            name = " ".join(name)
            if name != "":
                return name
        return self.name

    def is_hidden(self):
        if self.name in self.character.items:
            return self.character.items[self.name][1]
        return False

class Character:
    def __init__(self, screen):
        self.reset()
        self.screen = screen
        self.items = []

    def reset(self):
        self.inventory = []
        self.name = ""

    def _add_item(self, item):
        self.inventory.append(Item(item,self))

    def _remove_item(self, item):
        if item in self.inventory_ids():
            for a,b in enumerate(self.inventory):
                if b.name == item:
                    self.inventory = self.inventory[:a] + self.inventory[a+1:]
                    break

    def add_items(self, items):
        for item in items:
            self._add_item(item)

    def remove_items(self, items):
        for item in items:
            self._remove_item(item)

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
        inv = []
        for i in self.inventory:
            if not i.is_hidden():
                inv.append(i.get_name())
        self.screen.show_inventory(inv)

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
        game_to_load = self.screen.menu(self.games.titles(), 8, titles=True)
        self.games[game_to_load].load()
        again = True
        while again:
            again = False
            try:
                self.games[game_to_load].begin()
            except AVEGameOver:
                next = self.screen.gameover()
                self.character.reset()
                if next == 0:
                    again = True
                if next == 2:
                    raise AVEQuit
            except AVEWinner:
                next = self.screen.winner()
                self.character.reset()
                if next == 0:
                    again = True
                if next == 2:
                    raise AVEQuit
            except AVEToMenu:
                pass

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
        self.author = ""
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
                if line[:2] == "**" == line[-2:]:
                    self.author = clean(line[2:-2])
                if line[:2] == "~~" == line[-2:]:
                    if clean(line[2:-2]) == "off":
                        self.active = False

    def load(self):
        self.screen.clear()
        rooms = {}
        items = {}
        preamb = True
        firstitem = True
        mode = "PREA"
        with open(self.path) as f:
            for line in f.readlines() + ['#']:
                if line[0]=="#" or line[0] == '%':
                    if not preamb and mode == "ROOM" and len(c_options) > 0:
                        rooms[c_room] = Room(c_room, c_txt, c_options, self.screen, self.character)
                    if not firstitem and mode == "ITEM":
                        items[c_item] = [c_texts, c_hidden]
                    if line[0] == "#":
                        mode = "ROOM"
                        preamb = False
                        while len(line) > 0 and line[0] == "#":
                            line = line[1:]
                        c_room = clean(line)
                        c_txt = []
                        c_options = []
                    elif line[0]=="%":
                        mode = "ITEM"
                        firstitem = False
                        while len(line) > 0 and line[0] == "%":
                            line = line[1:]
                        c_item = clean(line)
                        c_hidden = False
                        c_texts = []
                elif mode == "ITEM":
                    if clean(line) == "__HIDDEN__":
                        c_hidden = True
                    elif clean(line) != "":
                        next_item = {'name':"",'needs':[],'unneeds':[],'adds':[],'rems':[]}
                        text = line
                        for a in attrs:
                            text = text.split(" "+a)[0]
                        next_item['name'] = clean(text)
                        lsp = line.split()
                        for i in range(len(lsp)-1):
                            for a,b in attrs.items():
                                if lsp[i] == a:
                                    next_item[b].append(lsp[i+1])
                        c_texts.append(next_item)
                elif mode == "ROOM":
                    if "=>" in line:
                        lsp = line.split("=>")
                        next_option = {'id':"",'option':"",'needs':[],'unneeds':[],'adds':[],'rems':[]}
                        next_option['option'] = clean(lsp[0])
                        lsp = clean(lsp[1]).split()
                        next_option['id'] = clean(lsp[0])
                        for i in range(1,len(lsp),2):
                            for a,b in attrs.items():
                                if lsp[i] == a:
                                    next_option[b].append(lsp[i+1])
                        c_options.append(next_option)
                    elif clean(line) != "":
                        next_line = {'text':"",'needs':[],'unneeds':[],'adds':[],'rems':[]}
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
        self.character.items = items

    def __getitem__(self, id):
        return self.load_room(id)

    def load_room(self, id):
        if id == "__GAMEOVER__":
            raise AVEGameOver
        if id == "__WINNER__":
            raise AVEWinner
        if id in self.rooms:
            return self.rooms[id]
        else:
            return self.fail_room()

    def begin(self):
        import curses
        self.show_title()
        room = self['start']
        while True:
            self.screen.clear()
            self.screen.put_ave_logo()
            next = room.show()
            room = self[next]

    def fail_room(self):
        options = [{'id':"__GAMEOVER__",'option':"Continue",'needs':[],'unneeds':[],'adds':[],'rems':[]}]
        text = [{'text':"You fall off the edge of the game... (404 Error)",'needs':[],'unneeds':[],'adds':[],'rems':[]}]
        return Room("fail", text, options, self.screen, self.character)

    def show_title(self):
        self.screen.show_titles(self.title, self.description, self.author)

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
        included_lines = []
        for line in self.text:
            if self.character.has(line['needs']) and self.character.unhas(line['unneeds']):
                self.character.add_items(line['adds'])
                self.character.remove_items(line['rems'])
                included_lines.append(line['text'])
        y = 0
        x = 0
        stuff = []
        text = " ".join(included_lines)
        for word in text.split():
            if x+len(word) > WIDTH-22:
                y += 1
                x = 0
            for i,c in enumerate(word):
                stuff.append((y,x,c))
                x += 1
            stuff.append((y,x," "))
            x += 1
        self.screen.type(stuff)

        opts = []
        adds = []
        rems = []
        ids = []
        for option in self.options:
            if self.character.has(option['needs']) and self.character.unhas(option['unneeds']):
                opts.append(option['option'])
                adds.append(option['adds'])
                rems.append(option['rems'])
                ids.append(option['id'])
        self.character.show_inventory()
        num = self.screen.menu(opts, add=adds, rem=rems, y=min(8,len(opts)), character=self.character)
        return ids[num]

