" system commands for the assembler"
from ast import literal_eval

__all__ = []

commands = {}

assembler = None

# give commands access to the assembler object
def bind(assembler_object):
    global assembler
    assembler = assembler_object


def register(cls):
    def func_wrapper(name):
        commands[cls] = name

    return func_wrapper


@register(".int")
def pos(s):
    v = assembler.labels[s[0]]
    print(v)


@register(".label")
def label(name):
    " create a label , useful inside macros"
    return [[name[0] + ":"]]


@register(".string")
def stringer(s):
    print(s)
    print("|")
    for i in s[0]:
        print(ord(i))
    print("|")
    print(assembler)
    return [[]]


@register(".equ")
def equ(s):
    name = s[0]
    val = literal_eval(s[1])
    assembler.variables[name] = val 

# rebind a exisiting command
@register(".def")
def defn(s):
    dst = s[0]
    src = s[1]
    assembler.instr_set[dst] =   assembler.instr_set[src]
    assembler.instr_param[dst] =   assembler.instr_param[src]
    assembler.instr_count[dst] =   assembler.instr_count[src]


@register(".alloc")
def alloc(s):
    name = s[0]
    cmds = [[name+":"]]
    v = literal_eval(s[1])
    if isinstance(v,int):
        for i in range(v):
            cmds.append(["NOP"])
    return cmds

@register(".global")
def glob(s):
    pass

