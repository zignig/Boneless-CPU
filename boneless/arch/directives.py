" system commands for the assembler"

from .mc import * 

__all__ = []

# other commands 
# .include <filename>
# .macro <name>
# .endm
# .equ  /  define a constant , will need mc.Constant and tracking

directives = {}
directives_params  = {}
assembler = None

# expose the entire assembler to this module
def bind(asm):
    global assembler
    assembler = asm
    Directive.assembler = asm


def register_directive(n, count):
    def func_wrapper(func):
        directives[n] = func 
        directives_params[n] = count
    return func_wrapper


class Directive:

    assembler = None

    def __init__(self,args):
        self.args = args 
        print(args['args'])
        

def args(m):
    ar = m['args'].split(',')
    return ar

@register_directive(".equ", 2)
class equate(Directive):
    def run(self):
        return [Constant(args(m)[0],args(m)[1])]

@register_directive(".macro",1)
class macro(Directive):
    def run(self):
        self.assembler._in_macro = True
        self.assembler._current_macro = Macro(args(m)[0],args(m)[1:])

@register_directive(".endm",0)
class end_macro(Directive):
    def run(self):
        assembler._in_macro = False
        cm = assembler._current_macro
        assembler.macros[cm.name] = cm
        assembler.instr_cls.mnemonics[cm.name] = assembler._current_macro

@register_directive(".section", 1)
class section(Directive):
    # the assembler should break into sections for linker
    # Boneless is all relative addressing , code is instrinscally slideable
    def run(self):
        print("section",m)

@register_directive(".word",1)
class word(Directive):
    def run(self):
        return int(m["args"], 0)

@register_directive(".window",0)
class window(Directive):
    # TODO assembler should align this automatically.
    def run(self):
        return [0 for i in range(8)]

@register_directive(".alloc",1)
class alloc(Directive):
    " add a list of zeros of length to the input stream"
    def run(self):
        v = [0 for i in range(int(args(m)[0],0))] 
        return v

@register_directive(".string",2)
class stringer(Directive):
    # TODO look into packing char instead of words 
    def run(self):
        r = []
        sta = []
        st = eval(args(m)[0])
        r += [len(st)]
        for i in st:
            sta.append(ord(i))
        r += sta
        #r += [0] # null ending
        return r
