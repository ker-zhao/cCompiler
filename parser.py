#! /usr/bin/env python3
import sys
import os
import platform

sys.path.extend(['.pycparser_master', '.'])

try:
    from pycparser import parse_file
except ModuleNotFoundError:
    from pycparser_master.pycparser import parse_file


FUNC_BEGIN = """
    pushl   %ebp
    movl    %esp, %ebp
    subl    $64, %esp
    pushl   %ecx
    pushl   %edx
    pushl   %ebx
    pushl   %esi
    pushl   %edi
"""

FUNC_END = """
    popl    %edi
    popl    %esi
    popl    %ebx
    popl    %edx
    popl    %ecx
    addl   $64, %esp
    leave
    ret
"""

SIZE_T = 4

DATA_LENGTH = {
    "int": 4,
    "string": 4,
    "pointer": 4,
}

REG_SUM = 6


class Regs:
    def __init__(self):
        self.regs = {
            "%eax": None,
            "%ecx": None,
            "%edx": None,
            "%ebx": None,
            "%esi": None,
            "%edi": None,
        }

    def get(self, ir):
        for i, v in self.regs.items():
            if v is None:
                self.regs[i] = ir
                return i
        # self.free_tmp()
        # for i, v in self.regs.items():
        #     if v is None:
        #         self.regs[i] = ir
        #         return i
        # print("Error: Out of registers.")
        return None

    def free_tmp(self):
        for i, v in self.regs.items():
            if v and (v.tmp is True):
                self.regs[i] = None

    def free(self, ir):
        if not hasattr(ir, "reg"):
            return
        self.regs[ir.reg] = None
        ir.reg = None


def load_ir(ir, target):
    if ir.var:
        reg = target.regs.get(ir)
        ir.reg = reg
        load = "movl {}, {}".format(ir.var.value, reg)
        target.push_text(load)
        return reg
    else:
        return ir.value


def save_ir(ir, target):
    if ir.var:
        target.push_text("movl {}, {}".format(ir.reg, ir.var.value))
        target.regs.free(ir)
        return
    else:
        return


def opt_ir(ir, opt, target):
    data = load_ir(ir, target)
    opt(data, target)
    save_ir(ir, target)
    return


def push_data(data, target):
    target.push_text("pushl {}".format(data))
    return


def push_ir(ir, target):
    return opt_ir(ir, push_data, target)


def write_data(lvalue, data, target):
    target.push_text("movl {}, {}".format(data, lvalue))


def write_ir(lvalue, ir, target):
    data = load_ir(ir, target)
    write_data(lvalue.value, data, target)
    save_ir(ir, target)
    return


def mem_mem(left, right, opt, target):
    if left.ast.__class__.__name__ == "Constant":
        ir = IR(left.ast, left.value, tmp=True)
        left = gen_tmp_var(ir, target)
    le = load_ir(left, target)
    ri = load_ir(right, target)
    opt(le, ri, target)
    tmp = gen_tmp_var(left, target)
    target.regs.free(left)
    target.regs.free(right)
    return tmp


def add_data(left, right, target):
    target.push_text("addl {}, {}".format(right, left))


def cmp_data(left, right, target):
    target.push_text("cmpl {}, {}".format(right, left))


def add_ir(left, right, target):
    left_type = left.ast.__class__.__name__
    right_type = right.ast.__class__.__name__
    if left_type == "Constant" and right_type == "Constant":
        v = int(left.ast.value) + int(right.ast.value)
        left.value = "$" + str(v)
        return IR(left, left.value)
    else:
        return mem_mem(left, right, add_data, target)


def cmp_ir(left, right, target):
    return mem_mem(left, right, cmp_data, target)


def gen_tmp_var(src, target):
    ir = IR(src.ast, tmp=True)
    reg = target.regs.get(ir)
    ir.reg = reg
    ir.value = reg
    if hasattr(src, "reg"):
        target.push_text("movl {}, {}".format(src.reg, reg))
    else:
        target.push_text("movl {}, {}".format(src.value, reg))
    return ir


class Frame:
    def __init__(self, size=64, outer=None):
        self.size = size
        self.outer = outer
        self.var_ptr = 0
        self.param_ptr = 4

    def next(self, length=4):
        self.var_ptr -= length
        return self.var_ptr

    def next_param(self, length=4):
        self.param_ptr += length
        return self.param_ptr


class Asm:
    def __init__(self):
        self.rodata_list = [".section    .rodata"]
        self.data_list = [".data"]
        self.text_list = [".text\n.globl  main"]

        # self.r_rodata = ".section    .rodata\n"
        # self.r_data = ".data\n"
        # self.r_text = ".text\n.globl  main\n"
        self.root_env = Env()
        self.env = self.root_env
        self.label_n = 0
        self.frame = Frame()
        self.regs = Regs()
        self.in_def_params = False

    def in_params(self):
        return self.in_def_params

    def push(self, cmd, l):
        l.append("\t{}".format(cmd))

    def push_rodata(self, cmd):
        self.push(cmd, self.rodata_list)

    def push_data(self, cmd):
        self.push(cmd, self.data_list)

    def push_text(self, cmd):
        self.push(cmd, self.text_list)

    def push_label(self, label, l):
        l.append("{}:".format(label))

    def next_label(self):
        self.label_n += 1
        return ".LC%d" % self.label_n

    def __str__(self):
        return "{}\n{}\n{}\n".format(
            "\n".join(self.rodata_list),
            "\n".join(self.data_list),
            "\n".join(self.text_list))


class IR:
    def __init__(self, ast, value=None, var=None, tmp=None):
        self.ast = ast
        self.value = value
        self.var = var
        self.tmp = tmp
        if self.var:
            self.value = self.var.value

    # def is_constant(self):
    #     return self.ast.__class__.__name__ == "Constant"


class Var:
    def __init__(self, offset, level=0):
        self.offset = offset
        self.level = level
        if self.level == 0:
            self.value = str(offset)
        else:
            self.value = "{}(%ebp)".format(offset)


class Env:
    def __init__(self, outer_env=None):
        self.outer_env = outer_env
        self.vars = {}
        if self.outer_env:
            self.level = self.outer_env.level + 1
        else:
            self.level = 0

    def ext_env(self, x, v):
        self.vars[x] = v
        return self

    def lookup(self, x):
        if x in self.vars:
            return self.vars[x]
        else:
            if self.outer_env:
                return self.outer_env.lookup(x)
            else:
                print("Error: unknown ID: ", x)
                return False

    def set(self, x, v):
        if x in self.vars:
            self.vars[x] = v
            return self
        else:
            if self.outer_env:
                return self.outer_env.set(x, v)
            else:
                return False


def process(ast, target: Asm):
    ty = ast.__class__.__name__

    if ty == "FileAST":
        for stm in ast.ext:
            process(stm, target)
    elif ty == "FuncDef":
        label = "%s" % ast.decl.name
        target.push_label(label, target.text_list)
        target.push_text(FUNC_BEGIN)
        target.frame = Frame()
        target.env = Env(target.env)
        if ast.decl.type.args:
            for param in ast.decl.type.args.params:
                target.in_def_params = True
                process(param, target)
        target.in_def_params = False
        process(ast.body, target)
        target.push_text(FUNC_END)
        target.env = target.env.outer_env
    elif ty == "Compound":
        for stm in ast:
            process(stm, target)
    elif ty == "FuncCall":
        if ast.args:
            for arg in reversed(ast.args.exprs):
                ir = process(arg, target)
                # target.push_text("pushl %s" % ir.value)
                push_ir(ir, target)

        target.push_text("call %s" % ast.name.name)
        if ast.args:
            target.push_text("addl $%d, %%esp" % (SIZE_T * len(ast.args.exprs)))
        return IR(ast, "%" + "eax")
    elif ty == "Return":
        ir = process(ast.expr, target)
        target.push_text("movl %s, %%eax" % ir.value)
        target.push_text(FUNC_END)
    elif ty == "Constant":
        if ast.type == "string":
            label = target.next_label()
            target.push_label(label, target.rodata_list)
            target.push_rodata('.string %s' % ast.value)
            ir = IR(ast, "$" + label)
            return ir
        elif ast.type == "int":
            ir = IR(ast, "$" + ast.value)
            return ir
        else:
            print("Error: unknown Constant")
    elif ty == "Decl":
        if target.in_params():
            offset = target.frame.next_param()
        else:
            offset = target.frame.next()
        if ast.init:
            rvalue = process(ast.init, target)
        else:
            rvalue = IR(ast)
        lvalue = IR(ast, None, Var(offset, target.env.level))
        target.env.ext_env(ast.type.declname, lvalue)
        if rvalue.value:
            target.push_text("movl {}, {}".format(rvalue.value, lvalue.var.value))
    elif ty == "ID":
        return target.env.lookup(ast.name)
    elif ty == "Assignment":
        lvalue = process(ast.lvalue, target)
        rvalue = process(ast.rvalue, target)
        write_ir(lvalue, rvalue, target)
        target.regs.free_tmp()
    elif ty == "BinaryOp":
        left = process(ast.left, target)
        right = process(ast.right, target)
        op = ast.op
        tmp = None
        if op == "+":
            tmp = add_ir(left, right, target)
        elif op == "==":
            tmp = cmp_ir(left, right, target)
        else:
            print("Error: process: unknown Operator: ", op)
        return tmp
    elif ty == "If":
        process(ast.cond, target)
        label0 = target.next_label()
        label1 = target.next_label()
        target.push_text("jne {}".format(label0))
        # if true
        process(ast.iftrue, target)
        # if end
        target.push_text("jmp {}".format(label1))
        # if false
        target.push_label(label0, target.text_list)
        process(ast.iffalse, target)
        target.push_label(label1, target.text_list)
        target.regs.free_tmp()
    else:
        print("Error: process: unknown Statement: ", ty)


def asm_link(asm):
    with open(asmfile, 'w') as f:
        f.write(str(asm))
    gen_cmd = "gcc -o {} {}".format(execfile, asmfile)
    print(os.system(gen_cmd))


# filename = sys.argv[1]
filename = "hello.c"
asmfile = "hello.s"
execfile = "hello"


def main():
    # print(preprocess_file(filename, cpp_args="-Ipycparser_master/utils/fake_libc_include"))
    ast = parse_file(filename, use_cpp=True,
                     cpp_args="-Ipycparser_master/utils/fake_libc_include")
    asm = Asm()
    process(ast, asm)
    if platform.system() == "Windows":
        print(asm)
    else:
        asm_link(asm)


if __name__ == "__main__":
    main()
