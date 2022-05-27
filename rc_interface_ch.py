"""
Project home: https://github.com/Starlight-Brilliant/random_call_ch
**Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0 **

*main developer: Ziran Tang
                 @StarlightResplendent: https://github.com/Starlight-Brilliant
*moderator:      Lunli Yuan
                 @Zhijiang Dong Autonomous County 1st middle school
This is a tool to call students randomly.
This is coded for practising, there may be bugs and bad coding behaviors.
"""


from tkinter import messagebox, filedialog
import tkinter
from rc_select_ch_api import *
from signal import SIG_DFL
from functools import partial
from json import dump as json_dump, load as json_load
from hashlib import md5
from threading import Thread
from time import sleep
from random import choice as random_choice
# noinspection PyUnresolvedReferences,PyProtectedMember
from os import _exit as os_exit, kill as os_kill, getpid
from abc import ABCMeta, abstractmethod


# TODO:1进一步检查用户输入done；
#  2保证正常退出主程序semi-done；
#  3做好关闭verify_admin窗口的操作done；
#  4分情况与总帮助页面postpone；
#  5优化判断null输入的错误提示done；
#  6打日志，记录每一次的抽取名单及相关信息 the format is: selection_mem:(MainGUIMessage) (time)；
#  7增加伪随机防重复；
#  8切换 从小组中抽取 界面的按钮上的信息（组名与组长名互换）
#  9独立颜色转换器done;
#  10迭代更换显示文字（特效的一种）doing；
#  11增加register上下文管理器（试用）；

# TODO:1加个快速开始；
#  2特效的音效；
#  3.1代码api加个多班级管理；3.2可视化多班级管理；
#  4代码api多语言管理postpone；
#  5代码api字体大小风格管理；
#  6重新设计管理员页面done;
#  ...
#  last 普通设置可视化

# TODO:1主界面优化，进一步布局按钮；
#  2多按钮吸引特效;
#  3检查数据库;
#  4方便鼠标输入数字done；

# 项目总结：
# 1.一般情况下，要保证数据的灵活性，即保持数据处理的方便性（除非要像普通用户展现最终结果）
# 2.将数据处理成普通用户能理解的文字 的函数 要在最后一步实现
# 3.强化命名的关键字和顺序
# 4.善用cache/register储存一些信息

_pid = getpid()
is_on_main_window = True
admin_flag = False
_font = ("宋体", 20)
HELP_PAGE_CONTENT = """
[编辑名字须知]
当你编辑名字的时候(学生名字或组名)，
你需要用一个或多个空格隔开各个名字，
其他的分隔符均无效，并且会被当成名字的一部分。
[编辑组名，决定从那些组抽取学生]
此时要注意，重复的名字都会被当成一个名字看待。
[管理员模式][编辑小组成员信息]
(1)以每一行作为一个小组。
(2)每行第一个名字为小组组长的名字。
(3)每个小组的名字以其组长的名字命名。
"""


def show_help_page():
    messagebox.showinfo("帮助页面", HELP_PAGE_CONTENT)


def _validate_input(number: str) -> int:
    if number.isdigit():
        number = int(number)
        if number:
            return number
        else:
            raise UserInputException('请输入一个有效的整数')
    else:
        raise UserInputException('请输入一个有效的整数')


def _dump_to_file(male: list = None, female: list = None, groups: list = None, update_group: bool = False):
    with open(rc_source_path, 'r', encoding="utf-8") as _f:
        _cache = json_load(_f)
        if male is None:
            _male = _cache["_male"]
        else:
            _male = male
        if female is None:
            _female = _cache["_female"]
        else:
            _female = female
        if groups is None:
            _groups = _cache["_gall"]
        else:
            if isinstance(groups[0], list):
                if update_group:
                    _groups = _cache["_gall"]
                    for i in groups:
                        _groups.update({i.pop(0): i})
                else:
                    _groups = {}
                    for i in groups:
                        _groups.update({i.pop(0): i})
            else:
                _groups = _cache["_gall"]
                _groups.update({groups.pop(0): groups})

    with open(rc_source_path, 'w', encoding="utf-8") as _f:
        json_dump({"_all": _male + _female, "_male": _male, "_female": _female, "_gall": _groups}, _f,
                  ensure_ascii=False, indent=4)


def _insert_to_end(widget, message: str) -> None:
    widget.insert('end', message)


def _str_to_list(string: str) -> list:
    _result = []
    for i in string.rstrip("\n").split(' '):
        if i:
            _result.append(i)
    return _result


def _group_str_to_list(string: str) -> list:
    _result = []
    for i in string.split('\n'):
        if i:
            _result.append(_str_to_list(i))
    return _result


def _list_to_str(_list: list) -> str:
    return str(_list).replace("'", '').replace(",", '').lstrip('[').rstrip(']')


def _group_list_to_str(_list: list) -> str:
    _result = ""
    for i in _list:
        _result += _list_to_str(i) + "\n"
    return _result


def _check_psw(psw: str) -> bool:
    _result = None
    with open(r"rc_sr", 'rb') as _f:
        md = md5()
        md.update((psw + "SR").encode())
        _result = True if md.digest() == _f.read() else False
    # 密码区分大小写
    # 初始密码为w2001
    return _result


def _change_password(newpsw: str):
    with open(r"rc_sr", "wb") as _f:
        md = md5()
        md.update((newpsw + "SR").encode())
        _f.write(md.digest())


def circle_color(prefix: str = "#", repeat_num: int = 1) -> str:
    """
    Construct a generator to constantly yield a string presenting colors in RBG.
    Only yield the most outer round of color in a RBG selector,
    in another word, the color-string always contains 00 and FF,
    for example: #FF0015 (This is a RBG-string presenting red in general)
    :param prefix: the prefix added to the front of RBG-string
    :param repeat_num the turns to yield str, each turn yield 6*16*16 strings, -1 means to yield forever.
    :rtype str

    """
    def _main():
        nonlocal _rbg_color
        for i1 in range(6):
            if i1 % 2 == 0:
                for i2 in range(255):
                    color = "%02X%02X%02X" % (_rbg_color[0], _rbg_color[1], _rbg_color[2])
                    yield prefix + color
                    _rbg_color[i1 % 3] += 1

            else:
                for i2 in range(255):
                    color = "%02X%02X%02X" % (_rbg_color[0], _rbg_color[1], _rbg_color[2])
                    yield prefix + color
                    _rbg_color[i1 % 3] -= 1
    _rbg_color = [0, 255, 0]
    if repeat_num == -1:
        while True:
            cc = _main()
            for i in cc:
                yield i
    else:
        for i_ in range(repeat_num):
            cc = _main()
            for i in cc:
                yield i


class RowStunt(metaclass=ABCMeta):
    @abstractmethod
    def _main(self):
        """
        the main function to execute the stunt
        """
        pass

    @abstractmethod
    def start(self):
        """
        the public method to start the stunt
        """
        pass

    @abstractmethod
    def stop(self):
        """
        the public method to stop the stunt
        """
        pass


class StuntChangeInfo(RowStunt):
    def __init__(self, widget, info: list, interval: float = 1.5):
        self._widget = widget
        self._info = info
        self._interval = interval
        self._stop_flag = True

    def _main(self):
        while True:
            for i in self._info:
                if self._stop_flag:
                    return
                self._widget.config(text=i)
                sleep(self._interval)

    def start(self):
        self._stop_flag = False
        self._main()

    def stop(self):
        self._stop_flag = True


class StuntManyColors(RowStunt):
    def __init__(self, widget, mode: str = "bg", is_main: bool = False):
        self._widget = widget
        self._mode = mode
        self._stop_flag = True
        self.is_main = is_main

    def _main(self):
        for i in circle_color(repeat_num=-1):
            self._widget.config(**{self._mode: i})
            sleep(0.005)

    def start(self):
        self._stop_flag = False
        try:
            self._main()
        except tkinter.TclError:
            if self.is_main or not is_on_main_window:
                global admin_flag
                if not admin_flag:
                    os_exit(0)

    def stop(self):
        self._stop_flag = True


class StuntColorsGlint(RowStunt):
    def __init__(self, widget, colorhighlight: str, colornothighlight: str, times: int = 3, interval_time: float = 0.5,
                 mode: str = "bg"):
        self._widget = widget
        self._mode = mode
        self._colorhighlight = colorhighlight
        self._colornothighlight = colornothighlight
        self._times = times
        self._interval_time = interval_time
        self._stop_flag = True

    def _main(self):
        for t in range(self._times):
            self._widget.config(**{self._mode: self._colorhighlight})
            sleep(self._interval_time)
            if self._stop_flag:
                return
            self._widget.config(**{self._mode: self._colornothighlight})
            sleep(self._interval_time)
            if self._stop_flag:
                return

    def start(self):
        self._stop_flag = False
        try:
            self._main()
        except tkinter.TclError:
            os_exit(0)

    def stop(self):
        self._stop_flag = True


class StuntScrollNames(RowStunt):
    def __init__(self, times: int, raw_source: list, target: list, title: str, message: str,
                 widget, _self):
        # raw_source was the source selected
        # target was source that cantains both selected and not selected
        self.title = title
        self.message = message
        self.widget = widget
        self._self = _self
        self.interval_time = 0.1
        self.times = times
        self.raw_source = raw_source
        self.target = target
        self.main = tkinter.Tk()
        self.main_frame_maincontainer = tkinter.Frame(self.main, bd=4, bg="#B23AE5")
        self.main_frame_maincontainer.pack(fill="both")
        self.label_showinfo = tkinter.Label(self.main_frame_maincontainer, text="选择中", font=_font)
        self.label_showinfo.pack()
        self.label_stunt = tkinter.Label(self.main_frame_maincontainer, text="", font=("宋体", 110))
        self.label_stunt.pack(after=self.label_showinfo, fill="both")
        self._stop_flag = True
        self._main()

    def main_window_init(self):
        self.main.title("特效准备中")
        screenwidth = self.main.winfo_screenwidth()
        screenheight = self.main.winfo_screenheight()
        self.main.geometry(f"{screenwidth // 2}x{int(screenheight / 2.5)}+{screenwidth // 3}+{screenheight // 3}")

    def _main(self):
        self.main_window_init()
        Thread(target=self.start, name="main_loop_StuntScrollNames", daemon=True).start()
        self.main.mainloop()

    def start(self):
        self._stop_flag = False
        try:
            self.main.title("选择中")
            for name in self.raw_source:
                for i in range(self.times):
                    if self._stop_flag:
                        break
                    self.label_stunt.config(text=random_choice(self.target))
                    sleep(self.interval_time)
                if random_choice([False] * 3 + [True]):
                    for i in range(5):
                        if self._stop_flag:
                            break
                        self.label_stunt.config(text=random_choice(self.target))
                        sleep(self.interval_time * i * 2)
                if self._stop_flag:
                    break
                self.label_stunt.config(text=name)
                sleep(self.interval_time)
                StuntColorsGlint(self.label_stunt, "#7F59E5", "#A2E5B3").start()
                self.label_stunt.config(bg="#FFFFFF")
                _temp = f"恭喜！ {name}被点中了"
                self.label_showinfo.config(text=_temp)
                self.main.title(_temp)
                sleep(1)
            self.main.destroy()
            self._self.show_label_showresult(self.title, self.message, self.widget)
        except tkinter.TclError:
            pass

    def stop(self):
        self._stop_flag = True


class MainGUI:
    def __init__(self):
        self.text_male = None
        self.text_female = None
        self.text_group = None

        self.register_stunt_main = []
        self.register_stunt_middle = []

        self.main = tkinter.Tk()
        self.main_frame_maincontainer = tkinter.Frame(self.main, bd=4, bg="#B23AE5")
        self.main_frame_maincontainer.pack()
        self.user_frame = tkinter.LabelFrame(self.main_frame_maincontainer, text="常规操作", font=_font)
        self.admin_frame = tkinter.LabelFrame(self.main_frame_maincontainer, text="管理员操作", font=_font)
        self.button_admin = tkinter.Button(self.admin_frame, text="管理... ", font=_font,
                                           command=self.goto_verift_admin)
        self.button_cpsw = tkinter.Button(self.admin_frame, text="更改密码... ", font=_font,
                                          command=self.goto_change_psw)

        self.middle_window = tkinter.Tk()
        self.middle_window.withdraw()
        self._menu_init(self.middle_window)
        self.middle_frame_maincontainer = tkinter.Frame(self.middle_window, highlightcolor="#B23AE5",
                                                        highlightthickness=4)

        self.stunt_middle_window_label_showresult = None
        self.frame_ctrl = tkinter.Frame(self.middle_frame_maincontainer)
        self.frame_show = tkinter.Frame(self.middle_frame_maincontainer)
        self.label_showresult = tkinter.Label(self.frame_show, bg="#A2E5B3", font=_font)

        self.logon_window = None

        self.main_window_init()
        self._menu_init(self.main)
        self.user_mode_init()

        self.stunt = None
        self.stunt_lengthen = None
        self.checkbutton_stunt_lengthen = None

        stunt_main_window = StuntManyColors(self.main_frame_maincontainer, is_main=True)
        Thread(target=stunt_main_window.start, name="main_window_stunt_many_colors", daemon=True).start()
        self.register_stunt_main.append(stunt_main_window)
        self.main.mainloop()

    def show_label_showresult(self, title: str, message: str, widget):
        widget.pack()
        messagebox.showinfo(title, message)
        # TODO: add log for have shown message
        stunt_middle_window_label_showresult = StuntColorsGlint(widget, "#7F59E5", "#A2E5B3")
        Thread(target=stunt_middle_window_label_showresult.start,
               name="middle_window_message_showresult_stunt_colors_glint", daemon=True).start()
        self.register_stunt_middle.append(stunt_middle_window_label_showresult)

    def _exit_interface(self):
        for i in self.register_stunt_main:
            i.stop()
        self.main.destroy()
        exit()

    def _menu_init(self, widget):
        menu_parent = tkinter.Menu(widget, takefocus=False)
        _start_menu = tkinter.Menu(menu_parent, tearoff=False)
        _start_menu.add_command(label="帮助页面", command=show_help_page)
        _start_menu.add_separator()
        _start_menu.add_command(label="退出", command=self._exit_interface)
        menu_parent.add_cascade(label="开始", menu=_start_menu)
        widget.config(menu=menu_parent)

    def _show(self, title: str, _message: str, raw_source: list, target=None):
        """
        :param title:
        :param _message:
        :param raw_source:
        :param target:
        a str stands for super set
        a list stands for group set
        NoneType stands for group_whole
        :return:
        """
        if not raw_source:
            raise UserInputException("请输入一个大于0的数值")
        message = ""
        _sep = 40
        while len(_message) > _sep:
            message += _message[:_sep] + "\n"
            _message = _message[_sep:]
        else:
            message += _message

        self.label_showresult.config(text=message)
        if self.stunt.get():
            if isinstance(target, str):
                target = {'所有学生': SuperStudentSet.get_all, '男生': SuperStudentSet.get_male,
                          '女生': SuperStudentSet.get_female}[target]()
            elif isinstance(target, list):
                pass
            elif target is None:
                for i in range(len(raw_source)):
                    raw_source[i] += "组"
                target = StudentGroupSet.get_all_groupnames()
                for i in range(len(target)):
                    target[i] += "组"
            else:
                raise TypeError("target should be one of str,list,None")
            # why can't use
            # StuntScrollNames(20, raw_source, target)
            times = 40 if self.stunt_lengthen.get() else 20
            StuntScrollNames(times, raw_source, target, title=title, message=message, widget=self.label_showresult,
                             _self=self)
        self.show_label_showresult(title, message, self.label_showresult)

    def _stunt_set(self):
        frame_stunt_set = tkinter.Frame(self.frame_ctrl)
        frame_stunt_set.grid(row=1, column=2, sticky="e")
        self.stunt = tkinter.BooleanVar(self.frame_ctrl)
        self.stunt_lengthen = tkinter.BooleanVar(self.frame_ctrl)
        checkbutton_add_stunt = tkinter.Checkbutton(frame_stunt_set, text="加特效", variable=self.stunt, font=_font,
                                                    onvalue=True, offvalue=False,
                                                    command=self._stunt_set_furthersetable)
        checkbutton_add_stunt.grid(row=1)
        checkbutton_add_stunt.select()
        self.checkbutton_stunt_lengthen = tkinter.Checkbutton(frame_stunt_set, text="延长特效时间",
                                                              variable=self.stunt_lengthen,
                                                              font=_font, onvalue=True, offvalue=False)
        self.checkbutton_stunt_lengthen.grid(row=2)
        self.checkbutton_stunt_lengthen.deselect()

    def _stunt_set_furthersetable(self):
        if self.stunt.get():
            self.checkbutton_stunt_lengthen.config(state="normal")
        else:
            self.checkbutton_stunt_lengthen.config(state="disabled")
            self.checkbutton_stunt_lengthen.deselect()

    def show_result_super(self, target: str, number: str) -> None:
        """
        show the result super
        :param number: the number of students selected
        :param target: the mode of select, can be '所有学生', '女生', '男生'
        :return:
        """
        try:
            number = _validate_input(number)
            if target in ['所有学生', '女生', '男生']:
                raw_source = select_from_super_set(target, number, return_type="list")
                source = name_list_to_str(raw_source)
                title = f"从 {target} 中点 {number} 名学生"
                message = f"恭喜！ {source} 被点中了!"
                self._show(title, message, raw_source, target)
        except UserInputException as err:
            messagebox.showerror('无效输入', err)

    def show_result_group(self, leaders: list, number: str) -> None:
        """
        show the result group
        :param leaders: the same as target
        :param number: the same as above
        :return:
        """
        leaders = list(set(leaders))
        try:
            number = _validate_input(number)
            raw_source = select_from_groups_by_groupleaders(leaders, number, return_type="list")
            source = name_list_to_str(raw_source)
            str_leaders = ""
            for name in leaders:
                str_leaders += f"{name}组,"
            str_leaders.rstrip(',')
            title = f"从 {str_leaders} 中点 {number} 位学生"
            message = f"恭喜！ {source} 被点中了!"
            self._show(title, message, raw_source, StudentGroupSet.get_groups_by_names(leaders))
        except UserInputException as err:
            messagebox.showerror('无效输入', err)

    def show_result_wholegroup(self, number: str) -> None:
        try:
            number = _validate_input(number)
            _raw_source = select_a_certain_amount_of_groups(number, return_type="list")
            source = ""
            for i in _raw_source:
                source += f"{i}组,"
            source = source.rstrip(",")
            title = f"点了 {number} 个组"
            message = f"恭喜！ {source} 被点中了!"
            self._show(title, message, _raw_source)
        except UserInputException as err:
            messagebox.showerror('无效输入', err)

    def main_window_init(self):
        self.main.title("欢迎使用随机点名器！━(*｀∀´*)ノ亻!")
        self.main.resizable(False, False)
        screenwidth = self.main.winfo_screenwidth()
        screenheight = self.main.winfo_screenheight()
        self.main.geometry(f"{screenwidth // 2}x{screenheight // 2}+{screenwidth // 4}+{screenheight // 4}")
        self.user_frame.config(height=screenheight // 8)
        self.admin_frame.config(height=screenheight // 15)

    def middle_window_reset(self):
        for i in self.register_stunt_middle:
            i.stop()
        if self.stunt_middle_window_label_showresult:
            self.stunt_middle_window_label_showresult.stop()
        try:
            self.middle_window.destroy()
        except tkinter.TclError:
            pass

        self.middle_window = tkinter.Tk()
        self.middle_window.withdraw()
        self._menu_init(self.middle_window)
        self.middle_frame_maincontainer = tkinter.Frame(self.middle_window, highlightcolor="#B23AE5",
                                                        highlightthickness=4)
        self.frame_ctrl = tkinter.Frame(self.middle_frame_maincontainer)
        self.frame_show = tkinter.Frame(self.middle_frame_maincontainer)
        self.label_showresult = tkinter.Message(self.frame_show, bg="#A2E5B3", font=_font)

    def user_mode_init(self):
        width = self.main.winfo_screenwidth() // 20
        self.user_frame.config(width=width + 10)
        self.user_frame.pack()
        self.admin_frame.config(width=width + 10)
        self.admin_frame.pack(after=self.user_frame)
        button_all = tkinter.Button(self.user_frame, text="从所有学生中抽选", font=_font,
                                    command=lambda: self.goto_select_from_super_set('所有学生'), width=width)
        button_all.pack()
        button_female = tkinter.Button(self.user_frame, text="从所有女生中抽选", font=_font,
                                       command=lambda: self.goto_select_from_super_set('女生'), width=width)
        button_female.pack(after=button_all)
        button_male = tkinter.Button(self.user_frame, text="从所有男生中抽选", font=_font,
                                     command=lambda: self.goto_select_from_super_set('男生'), width=width)
        button_male.pack(after=button_female)
        button_group = tkinter.Button(self.user_frame, text="从小组中抽选", font=_font,
                                      command=self.goto_select_from_group_set, width=width)
        button_group.pack(after=button_male)
        button_group_as_a_whole = tkinter.Button(self.user_frame, text="抽选小组", font=_font,
                                                 command=self.goto_select_group, width=width)
        button_group_as_a_whole.pack(after=button_group)
        self.button_admin.config(width=width)
        self.button_cpsw.config(width=width)
        self.button_admin.pack()
        self.button_cpsw.pack(after=self.button_admin)
        button_group_as_a_whole.pack(after=button_group)

    def admin_logon(self, psw: str):
        if _check_psw(psw):
            """self.main.deiconify()
            self.logon_window.destroy()
            self.admin_mode_init()"""
            for i in self.register_stunt_main:
                i.stop()

            global SR, admin_flag
            admin_flag = True
            self.main.destroy()
            SR = AdminGUI()
        else:
            messagebox.showerror("密码错误", "密码错误，请重试！")

    def admin_mode_init(self):
        """
        Deprecated
        Use AdminGui() instead
        """
        self.main.title("欢迎使用随机点名器！【管理员模式】")
        screenwidth = self.main.winfo_screenwidth()
        screenheight = self.main.winfo_screenheight()
        self.main.geometry(f"{screenwidth // 2}x{screenheight}+{screenwidth // 4}+0")
        self.admin_frame.pack_forget()
        label_show_usemethod = tkinter.Label(
            self.main, text="直接编辑下方文字，更多信息请查阅帮助页面。【开始->帮助页面】", font=_font)
        label_show_usemethod.pack()
        button_save = tkinter.Button(self.main, text="保存更改", command=self.goto_save_changes, font=_font)
        button_save.pack(after=label_show_usemethod)
        label_male = tkinter.Label(self.main, text="请在下方输入所有男生名字", font=_font)
        label_male.pack(after=button_save)
        self.text_male = tkinter.Text(self.main, height=5, highlightthickness=2, highlightcolor="#CBBDE5")
        self.text_male.pack(after=label_male)
        label_female = tkinter.Label(self.main, text="请在下方输入所有女生名字", font=_font)
        label_female.pack(after=self.text_male)
        self.text_female = tkinter.Text(self.main, height=5, highlightthickness=2, highlightcolor="#CBBDE5")
        self.text_female.pack(after=label_female)
        label_group = tkinter.Label(self.main, text="请在下方输入小组名单，每行为一小组，每行第一个为组长", font=_font)
        label_group.pack(after=self.text_female)
        self.text_group = tkinter.Text(self.main, height=len(StudentGroupSet.get_all_raw()) + 5,
                                       highlightthickness=2, highlightcolor="#CBBDE5")
        self.text_group.pack(after=label_group)
        self.text_male.insert("end", _list_to_str(SuperStudentSet.get_male()))
        self.text_female.insert("end", _list_to_str(SuperStudentSet.get_female()))
        self.text_group.insert("end", _group_list_to_str(StudentGroupSet.get_all_raw()))

    def goto_save_changes(self):
        """
        Deprecated
        Use AdminGUI() and manage them instead
        """
        if messagebox.askyesno(title="确认更改",
                               message="确定要保存更改吗？该操作不可撤回！"):
            _dump_to_file(male=_str_to_list(self.text_male.get("0.0", "end")),
                          female=_str_to_list(self.text_female.get("0.0", "end")),
                          groups=_group_str_to_list(self.text_group.get("0.0", "end")))
            messagebox.showinfo("已保存", "更改已成功保存！")

    def turn_to_main_window(self):
        global is_on_main_window
        is_on_main_window = True
        self.middle_window_reset()
        self.main.deiconify()
        for i in self.register_stunt_main:
            Thread(target=i.start, name="main_window" + i.start.__name__, daemon=True).start()

    def turn_to_middle_window(self, mode: str = "normal"):
        global is_on_main_window
        is_on_main_window = False
        self.main.withdraw()
        for i in self.register_stunt_main:
            i.stop()
        self.middle_window.deiconify()
        screenwidth = self.middle_window.winfo_screenwidth()
        screenheight = self.middle_window.winfo_screenheight()
        if mode == "normal":
            self.middle_window.geometry(f"{int(screenwidth // 2.2)}x{int(screenheight / 2.5)}+"
                                        f"{screenwidth // 3}+{screenheight // 3}")
        elif mode == "fullscreen":
            self.middle_window.geometry(f"{screenwidth}x{screenheight}+0+0")
        elif mode == "semi-fullscreen_y":
            self.middle_window.geometry(f"{screenwidth}x{screenheight // 2}+0+{screenheight // 4}")
        elif mode == "semi-fullscreen_x":
            pass
        else:
            raise ValueError("mode must be one of 'normal','fullscreen','semi-fullscreen_y,'semi-fullscreen_x' ")

        self.frame_ctrl.config(height=screenheight // 12)
        self.frame_ctrl.pack()
        self.frame_show.config(height=screenheight // 12)
        self.frame_show.pack(after=self.frame_ctrl)
        self.middle_frame_maincontainer.pack()
        stunt_middle_window_border = StuntManyColors(self.middle_frame_maincontainer, mode="highlightcolor")
        Thread(target=stunt_middle_window_border.start, name="middle_window_border_stunt_many_colors", daemon=True
               ).start()
        self.register_stunt_middle.append(stunt_middle_window_border)

    def turn_to_logon_window(self):
        try:
            if self.logon_window is not None:
                self.logon_window.destroy()
        except tkinter.TclError:
            pass
        self.logon_window = tkinter.Toplevel()
        screenwidth = self.logon_window.winfo_screenwidth()
        screenheight = self.logon_window.winfo_screenheight()
        self.logon_window.geometry(f"{screenwidth // 4}x{screenheight // 3}+{screenwidth // 4}+{screenheight // 4}")
        self.logon_window.deiconify()

    def goto_select_from_super_set(self, target: str) -> None:

        def _reinsert_showing_num(var):
            nonlocal scale_num
            entry_num.delete(0, "end")
            _insert_to_end(entry_num, var)

        self.turn_to_middle_window()
        self.middle_window.title(f"从 {target} 中抽选学生")
        label_showinfo = tkinter.Label(self.frame_ctrl, text="请输入抽选学生的数量",
                                       font=_font)
        label_showinfo.grid(row=1)
        label_showinfo.update()
        scale_num = tkinter.Scale(self.frame_ctrl, highlightthickness=2, highlightcolor="#CBBDE5", showvalue=False,
                                  length=label_showinfo.winfo_width(), width=label_showinfo.winfo_height(),
                                  orient=tkinter.HORIZONTAL, from_=1, to=30, resolution=1, takefocus=False,
                                  command=_reinsert_showing_num)
        scale_num.grid(row=2)
        scale_num.set(1)
        entry_num = tkinter.Entry(self.frame_ctrl, font=_font, highlightthickness=2, highlightcolor="#CBBDE5")
        entry_num.grid(row=3)
        entry_num.focus_set()
        entry_num.insert(0, '1')
        button_show = tkinter.Button(self.frame_ctrl, text="点这里开始点名", font=_font,
                                     command=lambda: self.show_result_super(target, entry_num.get()))
        button_show.grid(row=4)
        button_to_main = tkinter.Button(self.frame_ctrl, text="回到主菜单页面", font=_font,
                                        command=self.turn_to_main_window)
        button_to_main.grid(row=5)

        self._stunt_set()
        self.middle_window.mainloop()

    def goto_select_from_group_set(self) -> None:
        def _reinsert_showing_num(var):
            nonlocal scale_num
            entry_num.delete(0, "end")
            _insert_to_end(entry_num, var)

        self.turn_to_middle_window(mode="semi-fullscreen_y")
        self.middle_window.title("从选中的小组中抽选学生")
        label_showinfo = tkinter.Label(self.frame_ctrl, text="请输入抽选学生的数量",
                                       font=_font)
        label_showinfo.grid(row=1)
        label_showinfo.update()
        scale_num = tkinter.Scale(self.frame_ctrl, highlightthickness=2, highlightcolor="#CBBDE5", showvalue=False,
                                  length=label_showinfo.winfo_width(), width=label_showinfo.winfo_height(),
                                  orient=tkinter.HORIZONTAL, from_=1, to=30, resolution=1, takefocus=False,
                                  command=_reinsert_showing_num)
        scale_num.grid(row=2)
        entry_num = tkinter.Entry(self.frame_ctrl, highlightthickness=2, highlightcolor="#CBBDE5", font=_font)
        entry_num.grid(row=3)
        entry_num.focus_set()
        entry_num.insert(0, '1')
        label_show_usemethod = tkinter.Label(self.frame_ctrl, font=_font,
                                             text="点击按钮以选择小组或在下方直接编辑名单\n"
                                                  "更多信息，见【开始->帮助页面】")
        label_show_usemethod.grid(row=4)
        entry_selectedgroups = tkinter.Entry(self.frame_ctrl, width=self.middle_window.winfo_screenwidth() // 30,
                                             highlightthickness=2, highlightcolor="#CBBDE5", font=_font)
        entry_selectedgroups.grid(row=5)
        all_names_groupleaders = StudentGroupSet.get_all_groupnames()
        _tc = 0
        for _name in all_names_groupleaders:
            _tc += 1
            tkinter.Button(self.frame_ctrl, text=f"{_name}组", font=_font, takefocus=False,
                           command=partial(_insert_to_end, entry_selectedgroups, f"{_name} ")).grid(row=4 + _tc // 3,
                                                                                                    column=_tc % 3 + 1)

        button_show = tkinter.Button(self.frame_ctrl, text="点这里开始点名", font=_font,
                                     command=lambda: self.show_result_group(_str_to_list(entry_selectedgroups.get()),
                                                                            entry_num.get()))
        button_show.grid(row=6)
        button_to_main = tkinter.Button(self.frame_ctrl, text="回到主菜单页面", font=_font,
                                        command=self.turn_to_main_window)
        button_to_main.grid(row=7)
        self._stunt_set()
        self.middle_window.mainloop()

    def goto_select_group(self) -> None:

        def _reinsert_showing_num(var):
            nonlocal scale_num
            entry_num.delete(0, "end")
            _insert_to_end(entry_num, var)

        self.turn_to_middle_window()
        self.middle_window.title("抽选指定数量的小组，每个小组为一个整体")
        label_showinfo = tkinter.Label(self.frame_ctrl, text="请输入抽选小组的数量",
                                       font=_font)
        label_showinfo.grid(row=1)
        label_showinfo.update()
        scale_num = tkinter.Scale(self.frame_ctrl, highlightthickness=2, highlightcolor="#CBBDE5", showvalue=False,
                                  length=label_showinfo.winfo_width(), width=label_showinfo.winfo_height(),
                                  orient=tkinter.HORIZONTAL, from_=1, to=30, resolution=1, takefocus=False,
                                  command=_reinsert_showing_num)
        scale_num.grid(row=2)
        entry_num = tkinter.Entry(self.frame_ctrl, highlightthickness=2, highlightcolor="#CBBDE5", font=_font)
        entry_num.grid(row=3)
        entry_num.focus_set()
        entry_num.insert(0, '1')
        button_show = tkinter.Button(self.frame_ctrl, text="点这里开始点名", font=_font,
                                     command=lambda: self.show_result_wholegroup(entry_num.get()))
        button_show.grid(row=4)
        button_to_main = tkinter.Button(self.frame_ctrl, text="回到主菜单页面", font=_font,
                                        command=self.turn_to_main_window)
        button_to_main.grid(row=5)
        self._stunt_set()
        self.middle_window.mainloop()

    def goto_verift_admin(self):
        self.turn_to_logon_window()
        self.logon_window.title("登录为管理员身份")
        label_showinfo = tkinter.Label(self.logon_window, text="请输入密码（初始密码为空）", font=_font)
        label_showinfo.pack()
        entry_psw = tkinter.Entry(self.logon_window, show='*', highlightthickness=2, highlightcolor="#CBBDE5",
                                  font=_font)
        entry_psw.pack(after=label_showinfo)
        button_logon = tkinter.Button(self.logon_window, text="登录", font=_font,
                                      command=lambda: self.admin_logon(entry_psw.get()))
        button_logon.pack(after=entry_psw)
        self.logon_window.mainloop()

    def goto_change_psw(self):
        self.turn_to_logon_window()
        self.logon_window.title("更改密码")
        label_showinfo_oldpsw = tkinter.Label(self.logon_window, text="请输入旧密码", font=_font)
        label_showinfo_oldpsw.pack()
        entry_oldpsw = tkinter.Entry(self.logon_window, show='*', highlightthickness=2, highlightcolor="#CBBDE5",
                                     font=_font)
        entry_oldpsw.pack(after=label_showinfo_oldpsw)

        label_showinfo_newpsw = tkinter.Label(self.logon_window, text="请输入新密码", font=_font)
        label_showinfo_newpsw.pack(after=entry_oldpsw)
        entry_newpsw = tkinter.Entry(self.logon_window, show='*', highlightthickness=2, highlightcolor="#CBBDE5",
                                     font=_font)
        entry_newpsw.pack(after=label_showinfo_newpsw)

        label_showinfo_newpswag = tkinter.Label(self.logon_window, text="请再次输入新密码",
                                                font=_font)
        label_showinfo_newpswag.pack(after=entry_newpsw)
        entry_newpswag = tkinter.Entry(self.logon_window, show='*', highlightthickness=2, highlightcolor="#CBBDE5",
                                       font=_font)
        entry_newpswag.pack(after=label_showinfo_newpswag)

        button_logon = tkinter.Button(self.logon_window, text="点击这以更改密码", font=_font,
                                      command=lambda: self._handle_cpsw(
                                          entry_oldpsw.get(), entry_newpsw.get(), entry_newpswag.get()))
        button_logon.pack(after=entry_newpswag)
        self.logon_window.mainloop()

    def _handle_cpsw(self, oldpsw: str, newpsw: str, newpswag: str):
        if not _check_psw(oldpsw):
            messagebox.showerror("密码错误", "密码错误！请重试。")
            return
        if newpsw != newpswag:
            messagebox.showerror("无效新密码", "两新密码应相同")
            return
        if messagebox.askyesno("确认操作", "确定要更改密码吗\n"
                                       "该操作不可撤回！"):
            _change_password(newpsw)
            self.main.deiconify()
            self.logon_window.destroy()
            self.logon_window = tkinter.Tk()
            self.logon_window.withdraw()


class AdminGUI:
    def __init__(self):
        self.root = tkinter.Tk()
        self._menu_init(self.root)
        self.root_frame_maincontainer = tkinter.Frame(self.root, bd=4, bg="#B23AE5")
        self.root_frame_maincontainer.pack()
        self.frame_student_manage = tkinter.LabelFrame(self.root_frame_maincontainer, text="管理学生", font=_font)
        self.frame_student_manage.pack()
        self.frame_other_settings_manage = tkinter.LabelFrame(self.root_frame_maincontainer, text="其他设置", font=_font)
        self.frame_other_settings_manage.pack(after=self.frame_student_manage)

        self.root_window_init()

        self.toplevel = None
        self.root.mainloop()

    @staticmethod
    def _menu_init(widget):
        menu_parent = tkinter.Menu(widget, takefocus=False)
        _start_menu = tkinter.Menu(menu_parent, tearoff=False)
        _start_menu.add_command(label="帮助页面", command=show_help_page)
        _start_menu.add_separator()
        menu_parent.add_cascade(label="开始", menu=_start_menu)
        widget.config(menu=menu_parent)

    @staticmethod
    def _threat_alive_test(widget):
        """
        Heartbeat detection to check whether the GUI is currently visible
        by constantly config a widget
        Once the GUI is invisible, which means widget.config will raise an Exception called tkinter.TclError,
        System will be called to kill the process to ensure that sources all freed.
        """
        while True:
            try:
                widget.config()
                sleep(0.1)
            except tkinter.TclError:
                global _pid
                os_kill(_pid, SIG_DFL)

    def root_window_init(self):
        self.root.title("欢迎使用随机点名器！━(*｀∀´*)ノ亻!【管理员模式】")
        self.root.resizable(False, False)
        screenwidth = self.root.winfo_screenwidth()
        screenheight = self.root.winfo_screenheight()

        label_guide_to_help = tkinter.Label(self.frame_student_manage, text="各类操作语法，见【开始->帮助页面】", font=_font)
        label_guide_to_help.pack()
        Thread(name="self._threat_alive_test", target=lambda: self._threat_alive_test(label_guide_to_help)).start()
        self.root.geometry(f"{screenwidth // 2}x{screenheight // 2}+{screenwidth // 4}+{screenheight // 4}")

        button_to_change_super_set = tkinter.Button(self.frame_student_manage, text="管理男生/女生名单", font=_font,
                                                    command=self.goto_manage_super_set)
        button_to_change_super_set.pack(after=label_guide_to_help)
        button_to_change_group_set = tkinter.Button(self.frame_student_manage, text="管理小组名单", font=_font,
                                                    command=self.goto_manage_group_set)
        button_to_change_group_set.pack(after=button_to_change_super_set)
        button_to_change_group_set_by_file = tkinter.Button(self.frame_student_manage, text="导入小组名单", font=_font,
                                                            command=self.manage_group_set_by_upload_group_file)
        button_to_change_group_set_by_file.pack(after=button_to_change_group_set)

    def turn_to_toplevel(self, name: str, mode: str = "normal"):
        self.toplevel = tkinter.Toplevel()
        self.toplevel.title(f"欢迎使用随机点名器！━(*｀∀´*)ノ亻!【管理员模式】:{name}")
        self._menu_init(self.toplevel)
        screenwidth = self.root.winfo_screenwidth()
        screenheight = self.root.winfo_screenheight()
        if mode == "normal":
            self.toplevel.geometry(f"{int(screenwidth // 2.2)}x{int(screenheight / 2.5)}+"
                                   f"{screenwidth // 3}+{screenheight // 3}")
        elif mode == "fullscreen":
            self.toplevel.geometry(f"{screenwidth}x{screenheight}+0+0")
        elif mode == "semi-fullscreen_y":
            self.toplevel.geometry(f"{screenwidth}x{screenheight // 2}+0+{screenheight // 4}")
        elif mode == "semi-fullscreen_x":
            pass
        else:
            raise ValueError("mode must be one of 'normal','fullscreen','semi-fullscreen_y,'semi-fullscreen_x' ")

    def goto_manage_super_set(self):
        def save_changes():
            nonlocal text_male, text_female
            if messagebox.askyesno(title="确认更改",
                                   message="确定要保存更改吗？该操作不可撤回！"):
                _dump_to_file(male=_str_to_list(text_male.get("0.0", "end")),
                              female=_str_to_list(text_female.get("0.0", "end")))
                nonlocal self
                messagebox.showinfo("已保存", "更改已成功保存！")
                self.toplevel.destroy()

        self.turn_to_toplevel(name="管理小组名单", mode="semi-fullscreen_y")
        label_show_usemethod = tkinter.Label(
            self.toplevel, text="直接编辑下方文字，更多信息请查阅帮助页面。【开始->帮助页面】", font=_font)
        label_show_usemethod.pack()
        button_save = tkinter.Button(self.toplevel, text="保存更改", command=save_changes, font=_font)
        button_save.pack(after=label_show_usemethod)
        label_male = tkinter.Label(self.toplevel, text="请在下方输入所有男生名字", font=_font)
        label_male.pack(after=button_save)
        text_male = tkinter.Text(self.toplevel, height=5, highlightthickness=2, highlightcolor="#CBBDE5")
        # TODO:add Scrollbar
        text_male.pack(after=label_male)
        label_female = tkinter.Label(self.toplevel, text="请在下方输入所有女生名字", font=_font)
        label_female.pack(after=text_male)
        text_female = tkinter.Text(self.toplevel, height=5, highlightthickness=2, highlightcolor="#CBBDE5")
        text_female.pack(after=label_female)

        text_male.insert("end", _list_to_str(SuperStudentSet.get_male()))
        text_female.insert("end", _list_to_str(SuperStudentSet.get_female()))

        self.toplevel.mainloop()

    def goto_manage_group_set(self):
        def display_buttons():
            _tc = 0
            StudentGroupSet.update()
            all_names_groupleaders = StudentGroupSet.get_all_groupnames()
            for _name in all_names_groupleaders:
                _tc += 1
                tkinter.Button(frame_ctrl, text=f"{_name}组", font=_font, takefocus=False,
                               command=partial(_show_editing_area, _name)) \
                    .grid(row=1 + _tc // 3, column=_tc % 3 + 2)
            else:
                _tc += 1
                button_create_new_group.grid(row=1 + _tc // 3, column=_tc % 3 + 2)

        def _show_editing_area(group: str = None):
            nonlocal _ctrl_register, entry_group_name, entry_group_students, label_show_method
            nonlocal label_show_input_group_students

            label_show_method.grid_forget()
            for i in range(len(_ctrl_register)):
                _ctrl_register[i].grid(row=i + 1, column=1)
            label_show_input_group_students.update()
            entry_group_students.config(width=label_show_input_group_students.winfo_width() // 10)
            entry_group_name.delete(0, "end")
            entry_group_students.delete(0, "end")
            if group is not None:
                _insert_to_end(entry_group_name, group)
                _insert_to_end(entry_group_students, _list_to_str(StudentGroupSet.get_group_by_name(group)))

        def save_changes():
            _group_name = entry_group_name.get().rstrip("组")
            if not _group_name:
                messagebox.showerror(title="无效输入", message="请输入组名")
                return
            _result = _str_to_list(entry_group_students.get())
            _result.insert(0, _group_name)
            _dump_to_file(groups=_result)
            messagebox.showinfo(title="操作完成", message="修改成功")
            nonlocal self
            self.toplevel.destroy()

        def remove_group():
            nonlocal entry_group_name, self
            with open(rc_source_path, encoding="utf-8") as _f:
                _cache = json_load(_f)
                _groups = _cache["_gall"]
                try:
                    _groups.pop(entry_group_name.get().rstrip("组"))
                except KeyError as err:
                    messagebox.showerror(title="无效输入", message=f"{err}组不存在")
                    return
                _male = _cache["_male"]
                _female = _cache["_female"]
            with open(rc_source_path, 'w', encoding="utf-8") as _f:
                json_dump({"_all": _male + _female, "_male": _male, "_female": _female, "_gall": _groups}, _f,
                          ensure_ascii=False, indent=4)
            messagebox.showinfo(title="操作完成", message="移除成功！")
            self.toplevel.destroy()

        self.turn_to_toplevel(name="管理小组名单", mode="semi-fullscreen_y")
        frame_ctrl = tkinter.Frame(self.toplevel, height=self.toplevel.winfo_screenheight() // 12)
        frame_ctrl.pack()
        label_show_method = tkinter.Label(frame_ctrl, text="点击右方小组名或点击“创建新的小组”以进行编辑", font=_font)
        label_show_method.grid(row=1, column=1)
        button_create_new_group = tkinter.Button(frame_ctrl, text="创建新的小组", command=_show_editing_area,
                                                 font=_font)
        label_show_input_group_name = tkinter.Label(frame_ctrl, text="请在下方编辑组名", font=_font)
        entry_group_name = tkinter.Entry(frame_ctrl, font=_font, highlightthickness=2, highlightcolor="#CBBDE5")
        label_show_input_group_students = tkinter.Label(frame_ctrl, text="请在下方编辑该组人员名单，可按箭头键以调整光标位置",
                                                        font=_font)
        entry_group_students = tkinter.Entry(frame_ctrl, font=_font, highlightthickness=2, highlightcolor="#CBBDE5")
        button_save_changes = tkinter.Button(frame_ctrl, text="保存本组信息的修改", font=_font, command=save_changes)
        button_delete_group = tkinter.Button(frame_ctrl, text="删除以 该组名 命名的小组", font=_font, command=remove_group)
        _ctrl_register = [label_show_input_group_name, entry_group_name, label_show_input_group_students,
                          entry_group_students, button_save_changes, button_delete_group]

        display_buttons()
        self.toplevel.mainloop()

    @staticmethod
    def manage_group_set_by_upload_group_file():
        file_group = filedialog.askopenfilename()
        if not file_group:
            return
        _condition = messagebox.askyesnocancel(title="确认更改",
                                               message="更新曾经的小组数据？\n"
                                                       "按'是'以更新数据，这只会增加曾经不存在的小组和更新存在的小组人员名单\n"
                                                       "按'否'以覆盖曾经的数据，这会导致曾经导入和编辑的数据全部丢失，只保留本次导入的数据\n"
                                                       "按'取消'以放弃本次更改，这不会进行任何修改操作。")
        if _condition is None:
            return
        else:
            with open(file_group, encoding="utf-8") as _f:
                _temp = _group_str_to_list(_f.read())
                for i in _temp:
                    i[0] = i[0].rstrip("组")
                _dump_to_file(groups=_temp, update_group=_condition)
            messagebox.showinfo(title="操作完成", message="修改成功！")


if __name__ == '__main__':
    SR = MainGUI()

    # SR = AdminGUI()
    # SR = StuntScrollNames(20, ["1", "2"], ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', 'a', 's', 'd', 'f', 'g',
    #                                    'h', 'j', 'k', 'l', 'z', 'x', 'c', 'v', 'b', 'n', 'm'])
