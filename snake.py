import random
import threading
import time
from queue import Queue

import wx

body_str = "富强、民主、文明、和谐、自由、平等、公正、法治、爱国、敬业、诚信、友善      "
wall_str = "@"
food_str = "肉"
can_win = False
size = (600, 600)
speed = 0.25
pixel_size = 20
become_harder_per_score = 500
lock = threading.Lock()
event_lock = threading.Lock()
running_flag = True
dead = False
won = False
key_press_available = True


class Level:
    EASY = (3, 0.2)
    MEDIUM = (2, 0.15)
    HARD = (1, 0.1)
    NIGHTMARE = (0, 0.05)

    @classmethod
    def get(cls, i):
        if i == 0:
            return cls.NIGHTMARE
        elif i == 1:
            return cls.HARD
        elif i == 2:
            return cls.MEDIUM
        elif i == 3:
            return cls.EASY


level = Level.NIGHTMARE


class Menu(wx.Frame):
    def __init__(self):
        super().__init__(None, 1, "贪吃蛇", pos=(400, 400))
        self.SetSize((600, 600))
        self.SetMaxSize((600, 600))
        self.__init_ui()
        self.Show()

    def __init_ui(self):
        global body_str, food_str, wall_str, speed, can_win, size, level
        self.panel = wx.Panel(self)
        sizer = wx.GridBagSizer(0, 0)

        self.text = wx.StaticText(self.panel, label="墙体构成")
        sizer.Add(self.text, pos=(0, 0), flag=wx.ALL, border=5)

        self.tc = wx.TextCtrl(self.panel, value=wall_str)
        sizer.Add(self.tc, pos=(0, 1), span=(1, 10), flag=wx.EXPAND | wx.ALL, border=5)

        self.text1 = wx.StaticText(self.panel, label="食物构成")
        sizer.Add(self.text1, pos=(1, 0), flag=wx.ALL, border=5)

        self.tc1 = wx.TextCtrl(self.panel, value=food_str)
        sizer.Add(self.tc1, pos=(1, 1), span=(1, 10), flag=wx.EXPAND | wx.ALL, border=5)

        self.text2 = wx.StaticText(self.panel, label="难度")
        sizer.Add(self.text2, pos=(2, 0), flag=wx.ALL, border=5)

        self.tc2 = wx.Choice(self.panel, choices=["噩梦", "难", "一般", "简单"])
        self.tc2.Select(level[0])
        sizer.Add(self.tc2, pos=(2, 1), flag=wx.ALL, border=5)

        self.text3 = wx.StaticText(self.panel, label="可以获胜")
        sizer.Add(self.text3, pos=(2, 2), flag=wx.ALIGN_CENTER | wx.ALL, border=5)

        self.can_win = wx.RadioButton(self.panel, label="是")
        self.cannot_win = wx.RadioButton(self.panel, label="否")
        if can_win:
            self.can_win.SetValue(True)
        else:
            self.cannot_win.SetValue(True)
        sizer.Add(self.can_win, pos=(2, 3), span=(1, 1), flag=wx.EXPAND | wx.ALL, border=5)
        sizer.Add(self.cannot_win, pos=(2, 4), span=(1, 1), flag=wx.EXPAND | wx.ALL, border=5)

        self.size_choose = wx.StaticText(self.panel, label="场景大小")
        size_str = "x".join((str(item) for item in size))
        self.size_choose_choices = wx.ComboBox(self.panel, value=size_str,
                                               choices=["1200x1200", "800x800", "600x600", "400x400"])
        sizer.Add(self.size_choose, pos=(2, 5), flag=wx.ALIGN_CENTER | wx.ALL, border=5)
        sizer.Add(self.size_choose_choices, pos=(2, 6), span=(1, 3), flag=wx.EXPAND | wx.ALL, border=5)

        text4 = wx.StaticText(self.panel, label="蛇体构成")
        sizer.Add(text4, pos=(3, 0), flag=wx.ALL, border=5)

        self.tc4 = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE, value=body_str)
        sizer.Add(self.tc4, pos=(3, 1), span=(1, 10), flag=wx.EXPAND | wx.ALL, border=5)
        sizer.AddGrowableRow(3, 1)

        self.buttonOk = wx.Button(self.panel, label="开始游戏")
        sizer.Add(self.buttonOk, pos=(5, 4), flag=wx.ALL, border=5)

        def bind_stuff():
            prev = ""

            def common_focus(event):
                event_lock.acquire(1)
                global prev
                prev = event.EventObject.GetValue()
                event.Skip()
                event_lock.release()

            def one_char_blur(event):
                event_lock.acquire(1)
                global prev
                temp = prev
                event_lock.release()
                text = event.EventObject.GetValue()
                if text == "" or len(text) > 1:
                    modal = wx.MessageDialog(None, "只允许一个字符", "提示", style=wx.OK | wx.ICON_WARNING)
                    modal.ShowModal()
                    event.EventObject.SetValue(temp)
                    modal.Destroy()
                event.Skip()

            def at_least_one_blur(event):
                event_lock.acquire(1)
                global prev
                temp = prev
                event_lock.release()
                text = event.EventObject.GetValue()
                if len(text) < 2 or text == "":
                    modal = wx.MessageDialog(None, "至少需要两个字符", "提示", style=wx.OK | wx.ICON_WARNING)
                    modal.ShowModal()
                    modal.Destroy()
                    event.EventObject.SetValue(temp)
                if text.find(" ") == -1:
                    print("有空格")
                event.Skip()

            def size_blur(event):
                event_lock.acquire(1)
                global prev
                temp = prev
                event_lock.release()
                text = event.EventObject.GetValue()
                arr = text.split("x")
                if not len(arr) == 2:
                    event.EventObject.SetValue(temp)
                event.Skip()

            def start_game(event):
                global body_str, food_str, wall_str, speed, can_win, size, level
                wall_str = self.tc.GetValue()
                food_str = self.tc1.GetValue()
                choice = self.tc2.GetSelection()
                level = Level.get(choice)
                speed = level[1]
                if self.can_win.GetValue():
                    can_win = True
                else:
                    can_win = False
                arr = self.size_choose_choices.GetValue().split("x")
                size = tuple((int(item) for item in arr))
                body_str = self.tc4.GetValue()
                event.Skip()
                self.Destroy()
                World("贪吃蛇")

            self.tc.Bind(wx.EVT_SET_FOCUS, common_focus)
            self.tc.Bind(wx.EVT_KILL_FOCUS, one_char_blur)
            self.tc1.Bind(wx.EVT_SET_FOCUS, common_focus)
            self.tc1.Bind(wx.EVT_KILL_FOCUS, one_char_blur)
            self.size_choose_choices.Bind(wx.EVT_SET_FOCUS, common_focus)
            self.size_choose_choices.Bind(wx.EVT_KILL_FOCUS, size_blur)
            self.tc4.Bind(wx.EVT_SET_FOCUS, common_focus)
            self.tc4.Bind(wx.EVT_KILL_FOCUS, at_least_one_blur)
            self.buttonOk.Bind(wx.EVT_BUTTON, start_game)

        bind_stuff()

        self.panel.SetSizerAndFit(sizer)


class World(wx.Frame):
    def __init__(self, title):
        global size, won
        won = False
        super().__init__(None, id=-1, title=title, pos=(100, 100))
        self.__score = 0
        self.SetSize(size)
        self.SetMaxSize(size)
        self.__size = (size[0] - 20, size[1] - 40)
        size1 = self.__size
        self.__panel = wx.Panel(self, size=self.GetSize(), pos=(0, 0))

        def on_key_down_outer():

            prev_press = None

            def on_key_down(event):

                def inner():
                    lock.acquire(1)
                    global dead, running_flag
                    nonlocal prev_press
                    code = event.GetKeyCode()
                    last_available_press = prev_press if prev_press else self.__snake.dir
                    if code == 82:
                        global speed, level
                        self.score = 0
                        dead, running_flag = True, False
                        self.__main_thread.join()
                        wx.CallAfter(self.__reset)
                        speed = level[1]
                        self.__main_thread = threading.Thread(target=self.__run)
                        self.__main_thread.start()
                    elif code == 65:
                        if not last_available_press == Direction.RIGHT:
                            prev_press = Direction.LEFT
                    elif code == 68:
                        if not last_available_press == Direction.LEFT:
                            prev_press = Direction.RIGHT
                    elif code == 87:
                        if not last_available_press == Direction.DOWN:
                            prev_press = Direction.UP
                    elif code == 83:
                        if not last_available_press == Direction.UP:
                            prev_press = Direction.DOWN

                    if prev_press:
                        if not self.__snake.direction_queue.full():
                            self.__snake.direction_queue.put(prev_press)
                    lock.release()

                threading.Thread(target=inner).start()
                event.Skip()

            return on_key_down

        self.__on_key_down = on_key_down_outer()
        self.__panel.Bind(wx.EVT_KEY_DOWN, self.__on_key_down)
        self.__panel.SetFocus()
        for i in range(0, size1[1], pixel_size):
            for j in range(0, size1[0], pixel_size):
                if i == 0 or i == size1[1] - pixel_size or j == 0 or j == size1[0] - pixel_size:
                    wx.StaticText(self.__panel, label=wall_str, pos=(j, i))
        self.__initialize()
        self.Bind(wx.EVT_CLOSE, self.__on_close)
        self.__main_thread = threading.Thread(target=self.__run)
        self.__main_thread.start()

    def __on_close(self, event):
        self.close()

    def close(self):
        global running_flag, dead
        running_flag = False
        dead = True
        self.Destroy()

    @property
    def score(self):
        return self.__score

    @score.setter
    def score(self, value):
        self.__score = value

    @property
    def size(self):
        return self.__size

    def __run(self):
        global running_flag, dead, lock
        dead = False
        running_flag = True
        while not dead:
            wx.CallAfter(self.__snake.eat, self.__food)
            time.sleep(speed)
        if running_flag:
            msg_box = wx.MessageDialog(self.__panel, "游戏结束，您的得分是%s" % self.score, "提示",
                                       style=wx.OK | wx.ICON_WARNING)
            self.score = 0
            if msg_box.ShowModal() == wx.ID_OK:
                msg_box.Destroy()
                wx.CallAfter(self.close)
                wx.CallAfter(Menu)

    def __generate(self):
        self.__snake = Snake(self, self.__panel, pos=(pixel_size, self.size[1] / 2))
        self.__food = Food(self.__panel, self.__snake, self.size)

    def __reset(self):
        global body_str, running_flag, dead
        self.__snake.destroy()
        self.__snake = Snake(self, self.__panel, (pixel_size, self.size[1] / 2))
        self.__food.re_gen()

    def __initialize(self):
        self.Centre()
        self.__generate()
        self.Show(True)


class Direction:
    UP, RIGHT, DOWN, LEFT = 1, 2, 3, 4


class Food:
    def __init__(self, container, snake, ground_size):
        self.__container = container
        self.__snake = snake
        self.__ground_size = ground_size
        random_pos = self.ramdom_pos
        global food_str
        self.__content = wx.StaticText(container, label=food_str, pos=random_pos)

    @property
    def ramdom_pos(self):
        x, y = self.__ground_size

        def generate_random():
            return random.randint(pixel_size, x - pixel_size - 1), random.randint(pixel_size, y - pixel_size - 1)

        random_pos = generate_random()
        while True:
            for node in self.__snake:
                if random_pos[0] == node.x and random_pos[1] == node.y:
                    random_pos = generate_random()
                    break
            else:
                if random_pos[0] % pixel_size != 0 or random_pos[1] % pixel_size != 0:
                    random_pos = generate_random()
                    continue
                else:
                    break
        return random_pos

    @property
    def x(self):
        return self.__content.GetPosition()[0]

    def destroy(self):
        self.__content.Destroy()

    @property
    def y(self):
        return self.__content.GetPosition()[1]

    def re_gen(self):
        random_pos = self.ramdom_pos
        self.__content.SetPosition(random_pos)


class Snake:
    def __init__(self, world, container, pos=(0, 0)):
        super().__init__()
        self.__world = world
        self.direction_queue = Queue(2)
        self.__dir = Direction.RIGHT
        self.__container = container
        self.__body = list(body_str)
        self.__hard_point = 0
        word = self.__body.pop(0)
        if not can_win:
            self.__body.append(word)
        self.__head = Snake.Node(container, word, pos)
        self.__tail = self.__head
        self.__current_node = self.__head

    def destroy(self):
        for node in self:
            node.destroy()

    def __become_harder(self):
        global speed, become_harder_per_score
        if int((self.__world.score - self.__hard_point) / become_harder_per_score):
            rate = int((self.__world.score - self.__hard_point) / become_harder_per_score)
            for index in range(0, rate):
                speed -= 0.003
                print("速度加快了", "现在速度是", speed)
            self.__hard_point = self.__world.score

    @property
    def head(self):
        return self.__head

    @property
    def tail(self):
        return self.__tail

    @property
    def dir(self):
        return self.__dir

    @dir.setter
    def dir(self, value):
        self.__dir = value

    def __iter__(self):
        self.__current_node = self.__head
        return self

    def __next__(self):
        if not self.__current_node:
            raise StopIteration()
        node = self.__current_node
        self.__current_node = self.__current_node.next
        return node

    def __die(self, pos):
        x, y = self.__world.size
        flag = (pos[0] <= x and (pos[1] >= y - pixel_size or pos[1] <= 0)) or \
               (pos[1] >= 0 and (pos[0] >= x - pixel_size or pos[0] <= 0))
        if not flag:
            for node in self:
                if node == self.__head:
                    continue
                if pos[0] == node.x and pos[1] == node.y:
                    flag = True
                    break
        if flag:
            global dead
            dead = True

    def eat(self, food):
        global speed, can_win, won
        if not self.head.available or won:
            return
        self.__become_harder()
        word = self.__head.word
        new_pos = None
        if not self.direction_queue.empty():
            self.dir = self.direction_queue.get()
            self.direction_queue.task_done()
        if self.dir == Direction.UP:
            new_pos = (self.__head.x, self.__head.y - pixel_size)
        elif self.dir == Direction.RIGHT:
            new_pos = (self.__head.x + pixel_size, self.__head.y)
        elif self.dir == Direction.DOWN:
            new_pos = (self.__head.x, self.__head.y + pixel_size)
        elif self.dir == Direction.LEFT:
            new_pos = (self.__head.x - pixel_size, self.__head.y)
        self.__die(new_pos)
        global dead
        if dead:
            return
        head = Snake.Node(self.__container, word, new_pos)
        self.__head.prev = head
        head.next = self.__head
        self.__head = head
        next_node = self.__head.next
        while next_node.next:
            next_node.set_text(next_node.next.word)
            next_node = next_node.next

        x, y = self.__head.x, self.__head.y
        flag = (x == food.x and y == food.y)
        if flag:
            self.__world.score = self.__world.score + 100
            food.re_gen()
            word = self.__body.pop(0)
            if not can_win:
                self.__body.append(word)
            self.__tail.set_text(word)
            if can_win and self.win():
                won = True
                modal = wx.MessageDialog(None, "恭喜您完成游戏", "提示", style=wx.OK | wx.ICON_WARNING)
                if modal.ShowModal() == wx.ID_OK:
                    modal.Destroy()
                    self.__world.close()
                    Menu()
                    return
        else:
            tail = self.__tail
            self.__tail = tail.prev
            tail.destroy()

    def win(self):
        if not len(self.__body):
            return True
        return False

    class Node:
        def __init__(self, container, content, pos):
            super().__init__()
            self.__prev = None
            self.__next = None
            self.__content = wx.StaticText(container, label=content, pos=pos)
            self.__pos = pos

        def set_pos(self, pos):
            self.__content.SetPosition(pos)

        @property
        def word(self):
            return self.__content.LabelText

        @word.setter
        def word(self, val):
            self.__content.SetLabelText(val)

        @property
        def prev(self):
            return self.__prev

        @property
        def x(self):
            return self.__pos[0]

        @property
        def y(self):
            return self.__pos[1]

        @prev.setter
        def prev(self, value):
            self.__prev = value

        @property
        def next(self):
            return self.__next

        def set_text(self, text):
            self.__content.SetLabelText(text)

        @next.setter
        def next(self, value):
            self.__next = value

        @property
        def available(self):
            return self.__content

        def destroy(self):
            if self.prev:
                self.prev.next = None
            if self.next:
                self.next.prev = None
            self.__content.Destroy()


app = wx.App()
Menu()
app.MainLoop()
