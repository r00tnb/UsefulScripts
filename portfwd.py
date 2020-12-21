import re
import os
import sys
import subprocess
import importlib

class Colour:
    '''对字符串着色、改变样式
    
    Description:
        对输出到终端的字符串着色及改变它的样式
    
    Attribute:
        color 定义终端颜色代码
        color_regexp_rules 定义着色规则，对匹配到的字串进行着色
    
    '''
    color = {
        "fore":{   # 前景色
            'black'        : 30,   #  黑色
            'red'      : 31,   #  红色
            'green'    : 32,   #  绿色
            'blue'     : 34,   #  蓝色
            'yellow'   : 33,   #  黄色
            'purple'   : 35,   #  紫红色
            'cyan'     : 36,   #  青蓝色
            'white'    : 37,   #  白色
        },
        'back' :{   # 背景
            'black'     : 40,  #  黑色
            'red'       : 41,  #  红色
            'green'     : 42,  #  绿色
            'yellow'    : 43,  #  黄色
            'blue'      : 44,  #  蓝色
            'purple'    : 45,  #  紫红色
            'cyan'      : 46,  #  青蓝色
            'white'     : 47,  #  白色
        },
        'mode' :{   # 显示模式
            'mormal'    : 0,   #  终端默认设置
            'bold'      : 1,   #  高亮显示
            'note'      : 2, # 注释型文字，bash中为斜体，powershell中为灰体
            'underline' : 4,   #  使用下划线
            'blink'     : 5,   #  闪烁
            'invert'    : 7,   #  反白显示
            'hide'      : 8,   #  不可见
        }
    }

    color_regexp_rules = { # 会根据每条规则的先后顺序来着色, 有分组的会对分组内容着色，没有分组的对所有匹配字符串着色
        'doc':[ # 高亮文档、帮助信息
            {
                'regexp':re.compile(r"^[ \t]*>.*$", re.M), # 一行中除去空白字符以 > 开始的的字符串认为是命令或脚本，则把它高亮显示
                'color':['', 'blue', ''] # 对应mode, fore, back
            },
            {
                'regexp':re.compile(r"^.*?[:：][ \t]*$", re.M), # 一行中以:结尾的普通字符串认为它是标题，则把它高亮显示
                'color':['bold', 'yellow', ''] # 对应mode, fore, back
            },
            {
                'regexp':re.compile(r"(?:^|\s+)-[\w\-]+?(?:$|\s+)", re.M), # 以 - 开头的单词认为是命令行选项
                'color':['', 'cyan', ''] # 对应mode, fore, back
            },
            {
                'regexp':re.compile(r"#.*$", re.M), # 以#开始的字符串认为是注释，则把它高亮显示
                'color':['note', 'green', ''] # 对应mode, fore, back
            },
        ],
        'log':[ # 高亮日志输出信息
            {
                'regexp':re.compile(r"^\[\*\]", re.M), # 信息
                'color':['', 'blue', ''] # 对应mode, fore, back
            },
            {
                'regexp':re.compile(r"^\[(?:-|\+)\]", re.M), # 提示
                'color':['', 'yellow', ''] # 对应mode, fore, back
            },
            {
                'regexp':re.compile(r"^\[!\]", re.M), # 错误
                'color':['', 'red', ''] # 对应mode, fore, back
            },
        ]
    }

    def __init__(self):
        self.enable = True # 指定着色是否可用

    def __call__(self, string: str, type="log")-> str:
        '''根据预定义的规则修饰字符串
        
        Description:
            根据预定义的规则修饰字符串
        
        Arguments:
            
        
        Return:
            返回修饰后的字符串
        
        '''
        rules = Colour.color_regexp_rules.get(type)
        if rules is not None:
            string = self.normalize(string)
            for rule in rules:
                def repl(match)-> str:
                    result = match.group()
                    if isinstance(rule['color'], str):# 如果color字段为字符串，表明该部分需要使用其他规则来进行解析
                        return self(result, rule['color'])
                    
                    color = rule['color']
                    if match.groups():
                        # gourp count > 0
                        for group in match.groups():
                            result = result.replace(group, self.colorize(group, *color))
                    else:
                        result = self.colorize(result, *color)
                    return result
                string = rule['regexp'].sub(repl, string)
        
        return string

    def normalize(self, string: str)-> str:
        '''使字符串的内容不被终端解释为带颜色格式的字符串
        
        Description:
            使字符串的内容不被终端解释为带颜色格式的字符串
        
        '''
        return string.replace('\033', '\\033')

    def colorize(self, string: str, mode='', fore='', back='')-> str:
        '''对字符串着色
        
        Description:
            对字符串按照指定的颜色、模式进行修饰

            一般来说终端会对"\033[v1;v2;v3;...m"类似的字符串进行解析来改变后续字符串的颜色及显示样式，其中v1、v2 ...等为颜色后模式代码，在`Colour.color`定义了部分代码。
            每个 `v` 代码都会覆盖前面同类型的代码设置，所以对于前景色、背景色、模式的代码位置没必要关心，
            但是对于代码值为0的需要放在最开始，因为该代码会恢复默认样式影响所有类型的代码。
            例如
                > echo -e "\033[2;34;47m123123\033[0m"
                > 123123 # 白底蓝字

                > echo -e "\033[34;2;47m123123\033[0m"
                > 123123 # 白底蓝字
            结果都是一样的
        
        Arguments:
            string  待修饰字符串
            mode    显示模式
            fore    前景色
            back    背景色
        
        Return:
            已经修饰过的字符串
        
        '''
        if not self.enable:
            return string

        v1 = Colour.color['mode'].get(mode, 0)
        v2 = Colour.color['fore'].get(fore, 0)
        v3 = Colour.color['back'].get(back, 0)
        v1, v2, v3 = sorted([v1, v2, v3]) # 避免0代码放在后面了
        return f"\033[{v1};{v2};{v3}m{string}\033[0m"

colour = Colour()

class Tablor:
    '''向终端输出表格式内容
    
    Description:
        将列表中的内容以表格的形式输出到终端
    
    Attribute:
        
    
    '''

    def __call__(self, table:list, header=True, border=True, aligning='left')-> str:
        '''格式化列表中的内容为表格样式
        
        Description:
            格式化列表中的内容为表格样式
        
        Arguments:
            table 需要转化的表格
                标准格式为
                    [['header1', 'header2'], [d1, d2], [d3, d4]]

            header 如果为真则表示列表的第一行为表头
        
        Return:
            格式化后的字符串
        
        '''
        if table is None or not table:
            return ''
        
        try:
            return self.__analyse(table, header=header, border=border, aligning=aligning)
        except Exception:
            raise ValueError("analyse error!check your params")
        
    def __analyse(self, table: list, header: bool, border: bool, aligning="left")-> str:
        columns = len(table[0])
        result = ''
        width_list = [0 for i in range(columns)] # 对应每列的字符最大宽度
        for row in table:
            for c in range(columns):
                if width_list[c] < len(str(row[c])):
                    width_list[c] = len(str(row[c]))
        
        border_line = ['-'*i for i in width_list]
        if header:
            if border:
                result += self.__draw_line(border_line, width_list, '+', padding='-')+'\n'
            result += self.__draw_line(table[0], width_list, '|' if border else '', aligning)+'\n'
            del table[0]

        result += self.__draw_line(border_line, width_list, '+' if border else '', padding='-')+'\n'
        for row in table:
            result += self.__draw_line(row, width_list, '|' if border else "", aligning)+'\n'
        if border:
            result += self.__draw_line(border_line, width_list, '+', padding='-')+'\n'

        return result

    def __draw_line(self, line: list, width_list: list, joint='|', aligning='left', padding=' ')-> str:
        result = joint
        for i in range(len(line)):
            d = str(line[i])
            if aligning == 'left':
                d= d.ljust(width_list[i], ' ')
            elif aligning == 'right':
                d= d.rjust(width_list[i], ' ')
            elif aligning == 'center':
                d= d.center(width_list[i], ' ')
            result += f"{padding}{d}{padding}{joint}"
        return result

tablor = Tablor()

class ForwardPort:

    def __init__(self, username, host, passwd=None, port=22):
        self._username = username
        self._host = host
        self._passwd = passwd
        self._port = port
    
    def is_win(self):
        if sys.platform.lower().startswith("win"):
            return True
        return False

    def forward(self, lport, rport, rhost=None, reverse=False):
        if rhost is None:
            rhost = '127.0.0.1' if reverse else self._host

        if os.system("ssh -V 1>{} 2>&1".format(os.devnull)) == 0 :
            pexpect = None
            spawn = None
            try:
                if self.is_win():
                    pexpect = importlib.import_module('winpexpect')
                    spawn = pexpect.winspawn
                else:
                    pexpect = importlib.import_module('pexpect')
                    spawn = pexpect.spawn
            except Exception as e:
                print(colour(f"[!] No module {'winpexpect' if self.is_win() else 'pexpect'}, you need install it by ","log")+
                    colour.colorize(f"`pip install {'winpexpect' if self.is_win() else 'pexpect'}`", 'bold', 'blue'))
                exit(1)

            ssh = spawn(f"ssh -p {self._port} -o StrictHostKeyChecking=no -CNgf\
                 {'-R' if reverse else '-L'} {lport}:{rhost}:{rport} {self._username}@{self._host}")
            try:
                i = ssh.expect([pexpect.TIMEOUT, pexpect.EOF, r'p'], timeout=10)
                if i == 0:
                    print(colour("[!] Connection is timeout!"))
                elif i == 1:
                    print(colour("[!] Connection is closed!"))
                elif i == 2:
                    ssh.sendline(self._passwd)
                    j = ssh.expect(["denied", pexpect.TIMEOUT, pexpect.EOF], timeout=10)
                    if j == 0:
                        print(colour("[!] Permission denied, check your passwd or username!"))
                        exit(1)
                    else:
                        print(colour(f"[+] {'Remote' if reverse else 'Local'} :{lport} => {rhost}:{rport}"))
            finally:
                ssh.terminate()
        else:    
            print(colour("[!] No ssh command!"))


fwd = ForwardPort('gyh', '172.16.20.101', passwd="123")
fwd.forward(4444, 12345)
