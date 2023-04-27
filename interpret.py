# IPP Projekt 2
#
# file: interpret.py
# Author: Vojtěch Czakan (xczaka00)

import re
import argparse
import xml.etree.cElementTree as et


# Třída interpretu
# Zpracovává argumenty příkazové řádky, uchovává instrukce, zásobník dat, zásobník volání a labely
class Interpret:
    def __init__(self):
        self._input = None
        self._source = None
        self._instructions = []
        self._labels = {}
        self._symb = ["var", "int", "bool", "string", "nil"]
        self._call_stack = []
        self._data_stack = []

    # Zpracování argumentů příkazové řádky
    def run(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--source", nargs=1, help="sdasd")
        parser.add_argument("--input", nargs=1, help="sdasd")
        args = parser.parse_args()

        # Zpracování argumentu --source
        if args.source is not None:
            self._source = args.source[0]
            # Načtení souboru
            try:
                with open(self._source, "r") as f:
                    self._source = f.read()
            except:
                exit(11)
        else:
            if args.input is not None:
                self._source = input()
            else:
                exit(10)

        # Zpracování argumentu --input
        if args.input is not None:
            self._input = args.input[0]
        else:
            self._input = None

        # Načtení vstupu
        if self._input is not None:
            try:
                with open(self._input, "r") as f:
                    self._input = f.read()
                    self._input = self._input.split("\n")
            except:
                exit(11)

    def instrs(self):
        return self._instructions

    def input(self):
        return self._input

    def source(self):
        return self._source

    def labels(self):
        return self._labels

    def symb(self):
        return self._symb

    def call_stack(self):
        return self._call_stack

    def call_stack_push(self, value):
        self._call_stack.append(value)

    def call_stack_pop(self):
        return self._call_stack.pop()

    def add_instruction(self, instr):
        self._instructions.append(instr)

    def sort_instructions(self):
        # kontrola duplicitních čísel instrukcí
        if(len(set([instr.order() for instr in self._instructions])) != len(self._instructions)):
            exit(32)

        # seřazení instrukcí
        self._instructions.sort(key=lambda x: int(x.order()))

        # oprava hodnot pořadí instrukcí
        for i, instr in enumerate(self._instructions):
            instr.set_order(i + 1)

    def create_labels(self):
        for instr in self._instructions:
            if instr.opcode() == "LABEL":
                if instr.args()[0].value() in self._labels:
                    exit(52)

                self._labels[instr.args()[0].value()] = int(instr.order())

    def data_stack(self):
        return self._data_stack

    def data_stack_push(self, data):
        self._data_stack.append(data)

    def data_stack_pop(self):
        if len(self._data_stack) == 0:
            exit(56)
        return self._data_stack.pop()


# Třída Xml
# Zpracovává XML soubor
class Xml:
    def __init__(self, filename):
        try:
            self._root = et.fromstring(filename)
        except et.ParseError:
            exit(31)

    def root(self):
        return self._root

    def check_header(self):
        if self._root.tag != "program" or self._root.attrib["language"] != "IPPcode23" or "language" not in self._root.attrib:
            exit(32)

    def check_instructions(self):
        for instr in self._root:
            if instr.tag != "instruction":
                exit(32)

            if "order" not in instr.attrib or "opcode" not in instr.attrib:
                exit(32)

            if not instr.attrib["order"].isdigit() or int(instr.attrib["order"]) < 1:
                exit(32)

            if instr.attrib["opcode"].upper() not in ["MOVE", "CREATEFRAME", "PUSHFRAME", "POPFRAME", "DEFVAR",
                                                      "CALL", "RETURN", "PUSHS", "POPS", "ADD", "SUB", "MUL", "IDIV",
                                                      "LT", "GT", "EQ", "AND", "OR", "NOT", "INT2CHAR", "STRI2INT",
                                                      "READ",
                                                      "WRITE", "CONCAT", "STRLEN", "GETCHAR", "SETCHAR", "TYPE",
                                                      "LABEL",
                                                      "JUMP", "JUMPIFEQ", "JUMPIFNEQ", "EXIT", "DPRINT", "BREAK"]:
                exit(32)

            # kontrola argumentů
            for arg in instr:
                arg.text = arg.text.strip()

                if not re.match(r"^arg[1-3]$", arg.tag):
                    exit(32)

                if "type" not in arg.attrib:
                    exit(32)

                if arg.attrib["type"] not in ["var", "int", "bool", "string", "label", "type", "nil"]:
                    exit(32)

                if arg.attrib["type"] == "var":
                    if not re.match(r"^(LF|TF|GF)@[a-zA-Z_\-$&%*!?][\w\-$&%*!?]*$", arg.text):
                        exit(32)

                if arg.attrib["type"] == "int":
                    if not re.match(r"^[-+]?[0-9]+$", arg.text):
                        exit(32)

                if arg.attrib["type"] == "bool":
                    if not re.match(r"^(true|false)$", arg.text):
                        exit(32)

                if arg.attrib["type"] == "string":
                    if arg.text == None:
                        arg.text = ""

                    if not re.match(r"^(\d\d\d|[^\s])*$", arg.text):
                        exit(32)

                if arg.attrib["type"] == "label":
                    if not re.match(r"^([a-zA-Z_\-$&%*!?])[a-zA-Z0-9_\-$&%*!?]*$", arg.text):
                        exit(32)

                if arg.attrib["type"] == "type":
                    if not re.match(r"^(int|string|bool)$", arg.text):
                        exit(32)

                if arg.attrib["type"] == "nil":
                    if arg.text != "nil":
                        exit(32)

    def get_instructions(self, interpret):
        for instr in self._root:
            interpret.add_instruction(Instruction(instr.attrib["order"], instr.attrib["opcode"].upper()))
            for arg in instr:
                interpret.instrs()[-1].add_arg(arg.attrib["type"], arg.text)


# Třída Frames
# Zpracovává rámce
class Frames:
    def __init__(self):
        self._global_frame = {}
        self._local_frame = []
        self._temp_frame = None

    def global_frame(self):
        return self._global_frame

    def local_frame(self):
        return self._local_frame

    def temp_frame(self):
        return self._temp_frame

    def create_frame(self):
        self._temp_frame = {}

    def push_frame(self):
        if self._temp_frame is not None:
            self._local_frame.append(self._temp_frame)
            self._temp_frame = None
        else:
            exit(55)

    def pop_frame(self):
        if len(self._local_frame) > 0:
            self._temp_frame = self._local_frame.pop()
        else:
            exit(55)

    def get_var(self, var):
        frame, name = var.value().split("@")

        if frame == "GF":
            if name in self._global_frame:
                return self._global_frame[name]
            else:
                exit(54)
        elif frame == "LF":
            if len(self._local_frame) > 0:
                if name in self._local_frame[-1]:
                    return self._local_frame[-1][name]
                else:
                    exit(54)
            else:
                exit(55)
        elif frame == "TF":
            if self._temp_frame is not None:
                if name in self._temp_frame:
                    return self._temp_frame[name]
                else:
                    exit(54)
            else:
                exit(55)
        else:
            exit(32)

    def set_var(self, var, value):
        frame, name = var.value().split("@")

        if value is None:
            exit(56)

        if frame == "GF":
            if name in self._global_frame:
                self._global_frame[name] = value
            else:
                exit(54)
        elif frame == "LF":
            if len(self._local_frame) > 0:
                if name in self._local_frame[-1]:
                    self._local_frame[-1][name] = value
                else:
                    exit(54)
            else:
                exit(55)
        elif frame == "TF":
            if self._temp_frame is not None:
                if name in self._temp_frame:
                    self._temp_frame[name] = value
                else:
                    exit(54)
            else:
                exit(55)
        else:
            exit(32)

    def add_var(self, var):
        frame, name = instr.args()[0].value().split("@", 1)

        # Zápis proměnné do rámce
        if frame == "GF":
            if name not in self._global_frame:
                self._global_frame[name] = None
            else:
                exit(52)
        elif frame == "LF":
            if len(self._local_frame) > 0:
                if name not in self._local_frame[-1]:
                    self._local_frame[-1][name] = None
                else:
                    exit(52)
            else:
                exit(55)
        elif frame == "TF":
            if self._temp_frame is not None:
                if name not in self._temp_frame:
                    self._temp_frame[name] = None
                else:
                    exit(52)
            else:
                exit(55)


# Třída Argument
# Zpracovává argumenty instrukcí
class Argument:
    def __init__(self, type, value):
        self._type = type
        self._value = value

    def type(self):
        return self._type

    def value(self):
        return self._value


# Třída Instruction
# Zpracovává instrukce
class Instruction:
    _relational_instructions = ["JUMPIFEQ", "JUMPIFNEQ", "LT", "GT", "EQ"]

    def __init__(self, order, opcode):
        self._order = order
        self._opcode = opcode
        self._args = []

    def add_arg(self, type, value):
        self._args.append(Argument(type, value))

    def relational_instructions(self):
        return self._relational_instructions

    def order(self):
        return self._order

    def opcode(self):
        return self._opcode

    def args(self):
        return self._args

    def set_order(self, order):
        self._order = order


# Třída nil
# Pro ukládání hodnoty nil
class nil:
    def __init__(self):
        pass


# Kontrola zdali je hodnota proměnné typu int
# -------------------------------------------
# @param value hodnota proměnné
# @return hodnota proměnné
#         nebo exit(53) pokud není typu int
#         nebo exit(56) pokud je proměnná neinicializovaná
def check_var_is_int(value):
    if value is not None:
        if type(value) is int:
            return value
        else:
            exit(53)
    else:
        exit(56)


# Kontrola zdali je hodnota proměnné typu bool
# --------------------------------------------
# @param value hodnota proměnné
# @return hodnota proměnné
#         nebo exit(53) pokud není typu bool
#         nebo exit(56) pokud je proměnná neinicializovaná
def check_var_is_bool(value):
    if value is not None:
        if type(value) is bool:
            return value
        else:
            exit(53)
    else:
        exit(56)


# Výpis konstanty
# ---------------
# @param arg_num číslo argumentu
#        instr instrukce
def print_value(type, value):
    if type == "int":
        print(value, end="")
    elif type == "bool":
        if value:
            print("true", end="")
        else:
            print("false", end="")
    elif type == "string":
        # escape sekvence
        value = re.sub(r"\\([0-9]{3})", lambda x: chr(int(x.group(1))), value)
        print(value, end="")
    elif type == "nil":
        print("", end="")
    else:
        exit(32)


# Kontrola rovnosti hodnot
# ------------------------
# @param value1 první hodnota
#        value2 druhá hodnota
# @return True/False
def is_eq(value1, value2):
    if type(value1) is int and type(value2) is int:
        return value1 == value2
    elif type(value1) is bool and type(value2) is bool:
        return value1 == value2
    elif type(value1) is str and type(value2) is str:
        return value1 == value2
    elif type(value1) is nil and type(value2) is nil:
        return True
    elif type(value1) is nil or type(value2) is nil:
        return False
    else:
        exit(53)


# Kontrola typu a hodnoty konstanty
# --------------------------------
# @param const_type typ konstanty
#        const_value hodnota konstanty
# @return hodnota konstanty
def check_const(const_type, const_value):
    if const_type == "int":
        return int(const_value)
    elif const_type == "bool":
        if const_value == "true":
            return True
        else:
            return False

    elif const_type == "string":
        return re.sub(r"\\([0-9]{3})", lambda x: chr(int(x.group(1))), const_value)
    elif const_type == "nil":
        return nil()
    else:
        exit(32)


if __name__ == "__main__":
    interpret = Interpret()
    frames = Frames()

    interpret.run()
    inp = interpret.input()

    # Zpracování XML
    xml = Xml(interpret.source())

    xml.check_header()

    xml.check_instructions()

    xml.get_instructions(interpret)

    interpret.sort_instructions()

    instrs = interpret.instrs()

    interpret.create_labels()

    # zpracování instrukcí
    i = 0
    while i < len(instrs):
        instr = instrs[i]

        if instr.opcode() == "MOVE":
            if len(instr.args()) != 2:
                exit(32)

            # První argument musí být proměnná
            if instr.args()[0].type() != "var":
                exit(32)

            # Druhý argument musí být proměnná, konstanta nebo nil
            if instr.args()[1].type() not in interpret.symb():
                exit(32)

            # Získání hodnoty druhého argumentu
            if instr.args()[1].type() == "var":
                temp_value = frames.get_var(instr.args()[1])
            else:
                temp_value = check_const(instr.args()[1].type(), instr.args()[1].value())

            frames.set_var(instr.args()[0], temp_value)

        elif instr.opcode() == "CREATEFRAME" or instr.opcode() == "PUSHFRAME" or instr.opcode() == "POPFRAME" or instr.opcode() == "RETURN":
            if len(instr.args()) != 0:
                exit(32)

            if instr.opcode() == "CREATEFRAME":
                frames.create_frame()
            elif instr.opcode() == "PUSHFRAME":
                frames.push_frame()
            elif instr.opcode() == "POPFRAME":
                frames.pop_frame()
            elif instr.opcode() == "RETURN":
                if len(interpret.call_stack()) > 0:
                    i = interpret.call_stack_pop()
                else:
                    exit(56)
        elif instr.opcode() == "DEFVAR":
            if len(instr.args()) != 1:
                exit(32)

            # Argument musí být proměnná
            if instr.args()[0].type() != "var":
                exit(32)

            frames.add_var(instr.args()[0])

        elif instr.opcode() == "ADD" or instr.opcode() == "SUB" or instr.opcode() == "MUL" or instr.opcode() == "IDIV":
            if len(instr.args()) != 3:
                exit(32)

            # První argument musí být proměnná
            if instr.args()[0].type() != "var":
                exit(32)

            # Druhý a třetí argument musí být proměnná, konstanta nebo nil
            if instr.args()[1].type() not in interpret.symb():
                exit(32)
            if instr.args()[2].type() not in interpret.symb():
                exit(32)

            # Druhý a třetí argument musí být typu int
            if instr.args()[1].type() != "var" and instr.args()[1].type() != "int":
                exit(53)
            if instr.args()[2].type() != "var" and instr.args()[2].type() != "int":
                exit(53)

            # Zpracování druhého argumentu
            if instr.args()[1].type() == "var":
                temp_value1 = check_var_is_int(frames.get_var(instr.args()[1]))
            elif instr.args()[1].type() == "int":
                temp_value = int(instr.args()[1].value())

            # Zpracování třetího argumentu
            if instr.args()[2].type() == "var":
                temp_value2 = check_var_is_int(frames.get_var(instr.args()[2]))
            elif instr.args()[2].type() == "int":
                temp_value2 = int(instr.args()[2].value())

            # Výpočet
            if instr.opcode() == "ADD":
                temp_value = temp_value + temp_value2
            elif instr.opcode() == "SUB":
                temp_value = temp_value - temp_value2
            elif instr.opcode() == "MUL":
                temp_value = temp_value * temp_value2
            elif instr.opcode() == "IDIV":
                if temp_value2 == 0:
                    exit(57)
                temp_value = temp_value // temp_value2

            frames.set_var(instr.args()[0], temp_value)

        elif instr.opcode() == "READ":
            if len(instr.args()) != 2:
                exit(32)

            # První argument musí být proměnná
            if instr.args()[0].type() != "var":
                exit(32)

            # Druhý argument musí být typu type
            if instr.args()[1].type() != "type":
                exit(32)

            # Získání vstupu
            if inp is not None:
                temp_value = inp.pop(0)
            else:
                temp_value = input()

            # Kontrola typu
            if instr.args()[1].value() == "int":
                try:
                    temp_value = int(temp_value)
                except ValueError:
                    temp_value = nil()
            elif instr.args()[1].value() == "bool":
                if temp_value.lower() == "true":
                    temp_value = True
                elif temp_value.lower() == "false":
                    temp_value = False
                else:
                    temp_value = nil()
            elif instr.args()[1].value() == "string":
                temp_value = str(temp_value)

            frames.set_var(instr.args()[0], temp_value)

        elif instr.opcode() == "WRITE":
            if len(instr.args()) != 1:
                exit(32)

            # Argument musí být proměnná nebo konstanta
            if instr.args()[0].type() not in interpret.symb():
                exit(32)

            if instr.args()[0].type() == "var":
                temp_value = frames.get_var(instr.args()[0])
                if temp_value is not None:
                    if type(temp_value) is nil:
                        print("", end="")
                    elif type(temp_value) is bool:
                        print(str(temp_value).lower(), end="")
                    else:
                        print(temp_value, end="")
                else:
                    exit(56)

            else:
                print_value(instr.args()[0].type(), instr.args()[0].value())

        elif instr.opcode() == "JUMP":
            if len(instr.args()) != 1:
                exit(32)

            # Argument musí být label
            if instr.args()[0].type() != "label":
                exit(32)

            if instr.args()[0].value() in interpret.labels():
                i = interpret.labels()[instr.args()[0].value()]-1
            else:
                exit(52)

        elif instr.opcode() in instr.relational_instructions():
            if len(instr.args()) != 3:
                exit(32)

            if instr.opcode() == "JUMPIFEQ" or instr.opcode() == "JUMPIFNEQ":
                # První argument musí být label
                if instr.args()[0].type() != "label":
                    exit(32)
            else:
                # První argument musí být proměnná
                if instr.args()[0].type() != "var":
                    exit(32)

            # Druhý a třetí argument musí být proměnná nebo konstanta
            if instr.args()[1].type() not in interpret.symb() and instr.args()[2].type() not in interpret.symb():
                exit(32)

            if instr.args()[1].type() == "var":
                temp_value1 = frames.get_var(instr.args()[1])
            else:
                temp_value1 = check_const(instr.args()[1].type(), instr.args()[1].value())
            if instr.args()[2].type() == "var":
                temp_value2 = frames.get_var(instr.args()[2])
            else:
                temp_value2 = check_const(instr.args()[2].type(), instr.args()[2].value())

            if temp_value1 is None or temp_value2 is None:
                exit(56)

            if instr.opcode() == "JUMPIFEQ":
                if is_eq(temp_value1, temp_value2):
                    if instr.args()[0].value() in interpret.labels():
                        i = interpret.labels()[instr.args()[0].value()] - 1
                    else:
                        exit(52)
            elif instr.opcode() == "JUMPIFNEQ":
                if not is_eq(temp_value1, temp_value2):
                    if instr.args()[0].value() in interpret.labels():
                        i = interpret.labels()[instr.args()[0].value()] - 1
                    else:
                        exit(52)
            else:
                if instr.opcode() == "EQ":
                    if is_eq(temp_value1, temp_value2):
                        temp_value = True
                    else:
                        temp_value = False
                elif instr.opcode() == "LT":
                    if type(temp_value1) is int and type(temp_value2) is int or\
                            type(temp_value1) is bool and type(temp_value2) is bool or\
                            type(temp_value1) is str and type(temp_value2) is str:
                        if temp_value1 < temp_value2:
                            temp_value = True
                        else:
                            temp_value = False
                    else:
                        exit(53)
                else:
                    if type(temp_value1) is int and type(temp_value2) is int or\
                            type(temp_value1) is bool and type(temp_value2) is bool or\
                            type(temp_value1) is str and type(temp_value2) is str:
                        if temp_value1 > temp_value2:
                            temp_value = True
                        else:
                            temp_value = False
                    else:
                        exit(53)

                frames.set_var(instr.args()[0], temp_value)

        elif instr.opcode() == "AND" or instr.opcode() == "OR" or instr.opcode() == "NOT":
            if instr.opcode() == "NOT":
                if len(instr.args()) != 2:
                    exit(32)
            else:
                if len(instr.args()) != 3:
                    exit(32)

            # První argument musí být proměnná
            if instr.args()[0].type() != "var":
                exit(32)

            # Druhý a třetí argument musí být proměnná, konstanta nebo nil
            if instr.args()[1].type() not in interpret.symb():
                exit(32)
            # instrukce NOT má pouze jeden argument
            if instr.opcode() != "NOT":
                if instr.args()[2].type() not in interpret.symb():
                    exit(32)

            # Druhý a třetí argument musí být bool
            if instr.args()[1].type() != "var" and instr.args()[1].type() != "bool":
                exit(53)
            if instr.opcode() != "NOT":
                if instr.args()[2].type() != "var" and instr.args()[2].type() != "bool":
                    exit(53)

            if instr.args()[1].type() == "var":
                temp_value1 = check_var_is_bool(frames.get_var(instr.args()[1]))
            else:
                temp_value1 = check_const(instr.args()[1].type(), instr.args()[1].value())
            if instr.opcode() != "NOT":
                if instr.args()[2].type() == "var":
                    temp_value2 = check_var_is_bool(frames.get_var(instr.args()[2]))
                else:
                    temp_value2 = check_const(instr.args()[2].type(), instr.args()[2].value())

            if instr.opcode() == "AND":
                temp_value = temp_value1 and temp_value2
            elif instr.opcode() == "OR":
                temp_value = temp_value1 or temp_value2
            else:
                temp_value = not temp_value1

            frames.set_var(instr.args()[0], temp_value)

        elif instr.opcode() == "INT2CHAR":
            if len(instr.args()) != 2:
                exit(32)

            # První argument musí být proměnná
            if instr.args()[0].type() != "var":
                exit(32)

            # Druhý argument musí být proměnná nebo konstanta
            if instr.args()[1].type() not in interpret.symb():
                exit(32)

            # Druhý argument musí být int
            if instr.args()[1].type() != "var" and instr.args()[1].type() != "int":
                exit(53)

            if instr.args()[1].type() == "var":
                temp_value = check_var_is_int(frames.get_var(instr.args()[1]))
            else:
                temp_value = check_const(instr.args()[1].type(), instr.args()[1].value())

            if temp_value is None:
                exit(58)

            # Platné ordinální hodnoty znaků jsou v rozsahu 0-1114111
            if temp_value < 0 or temp_value > 1114111:
                exit(58)
            else:
                temp_value = chr(temp_value)

            frames.set_var(instr.args()[0], temp_value)

        elif instr.opcode() == "STRI2INT":
            if len(instr.args()) != 3:
                exit(32)

            # První argument musí být proměnná
            if instr.args()[0].type() != "var":
                exit(32)

            # Druhý a třetí argument musí být proměnná nebo konstanta
            if instr.args()[1].type() not in interpret.symb():
                exit(32)
            if instr.args()[2].type() not in interpret.symb():
                exit(32)

            if instr.args()[1].type() == "var":
                temp_value1 = frames.get_var(instr.args()[1])
            else:
                temp_value1 = check_const(instr.args()[1].type(), instr.args()[1].value())

            if instr.args()[2].type() == "var":
                temp_value2 = frames.get_var(instr.args()[2])
            else:
                temp_value2 = check_const(instr.args()[2].type(), instr.args()[2].value())

            if temp_value1 is None or temp_value2 is None:
                exit(56)

            if type(temp_value1) is str and type(temp_value2) is int:
                if temp_value2 < 0 or temp_value2 > len(temp_value1) - 1:
                    exit(58)
                else:
                    temp_value = ord(temp_value1[temp_value2])
            else:
                exit(53)

            frames.set_var(instr.args()[0], temp_value)

        elif instr.opcode() == "CONCAT" or instr.opcode() == "STRLEN" or instr.opcode() == "GETCHAR" or instr.opcode() == "SETCHAR":
            if instr.opcode() == "STRLEN":
                if len(instr.args()) != 2:
                    exit(32)
            else:
                if len(instr.args()) != 3:
                    exit(32)

            # První argument musí být proměnná
            if instr.args()[0].type() != "var":
                exit(32)

            # Druhý a třetí argument musí být proměnná nebo konstanta
            if instr.args()[1].type() not in interpret.symb():
                exit(32)
            # STRLEN má pouze dva argumenty
            if instr.opcode() != "STRLEN":
                if instr.args()[2].type() not in interpret.symb():
                    exit(32)

            if instr.args()[1].type() == "var":
                temp_value1 = frames.get_var(instr.args()[1])
            else:
                temp_value1 = check_const(instr.args()[1].type(), instr.args()[1].value())

            if instr.opcode() != "STRLEN":
                if instr.args()[2].type() == "var":
                    temp_value2 = frames.get_var(instr.args()[2])
                else:
                    temp_value2 = check_const(instr.args()[2].type(), instr.args()[2].value())

            if temp_value1 is None or (instr.opcode() != "STRLEN" and temp_value2 is None):
                exit(56)

            if instr.opcode() == "CONCAT":
                if type(temp_value1) is str and type(temp_value2) is str:
                    temp_value = temp_value1 + temp_value2
                else:
                    exit(53)
            elif instr.opcode() == "STRLEN":
                if type(temp_value1) is str:
                    temp_value = len(temp_value1)
                else:
                    exit(53)
            elif instr.opcode() == "GETCHAR":
                if type(temp_value1) is str and type(temp_value2) is int:
                    if temp_value2 < 0 or temp_value2 > len(temp_value1) - 1:
                        exit(58)
                    else:
                        temp_value = temp_value1[temp_value2]
                else:
                    exit(53)
            elif instr.opcode() == "SETCHAR":
                temp_value = frames.get_var(instr.args()[0])

                if temp_value is None:
                    exit(56)

                if type(temp_value) is str and type(temp_value1) is int and type(temp_value2) is str:
                    if temp_value1 < 0 or temp_value1 > len(temp_value) - 1 or temp_value2 == "":
                        exit(58)
                    else:
                        temp_value = temp_value[:temp_value1] + temp_value2[0] + temp_value[temp_value1 + 1:]

                else:
                    exit(53)

            frames.set_var(instr.args()[0], temp_value)

        elif instr.opcode() == "TYPE":
            if len(instr.args()) != 2:
                exit(32)

            # První argument musí být proměnná
            if instr.args()[0].type() != "var":
                exit(32)

            # Druhý argument musí být proměnná nebo konstanta
            if instr.args()[1].type() not in interpret.symb():
                exit(32)

            if instr.args()[1].type() == "var":
                temp_value = frames.get_var(instr.args()[1])
            else:
                temp_value = check_const(instr.args()[1].type(), instr.args()[1].value())

            if type(temp_value) is int:
                temp_value = "int"
            elif type(temp_value) is str:
                temp_value = "string"
            elif type(temp_value) is bool:
                temp_value = "bool"
            elif type(temp_value) is nil:
                temp_value = "nil"
            elif temp_value is None:
                temp_value = ""

            frames.set_var(instr.args()[0], temp_value)

        elif instr.opcode() == "EXIT":
            if len(instr.args()) != 1:
                exit(32)

            # Argument musí být proměnná nebo konstanta
            if instr.args()[0].type() not in interpret.symb():
                exit(32)

            if instr.args()[0].type() == "var":
                temp_value = frames.get_var(instr.args()[0])
            else:
                temp_value = check_const(instr.args()[0].type(), instr.args()[0].value())

            if temp_value is not None:
                if type(temp_value) is int:
                    if temp_value < 0 or temp_value > 49:
                        exit(57)
                    else:
                        exit(temp_value)
                else:
                    exit(53)
            else:
                exit(56)

        elif instr.opcode() == "CALL":
            if len(instr.args()) != 1:
                exit(32)

            # Argument musí být label
            if instr.args()[0].type() != "label":
                exit(32)

            if instr.args()[0].value() in interpret.labels():
                interpret.call_stack_push(i)
                i = interpret.labels()[instr.args()[0].value()] - 1
            else:
                exit(52)

        elif instr.opcode() == "PUSHS":
            if len(instr.args()) != 1:
                exit(32)

            # Argument musí být proměnná nebo konstanta
            if instr.args()[0].type() not in interpret.symb():
                exit(32)

            if instr.args()[0].type() == "var":
                temp_value = frames.get_var(instr.args()[0])
            else:
                temp_value = check_const(instr.args()[0].type(), instr.args()[0].value())

            if temp_value is not None:
                interpret.data_stack_push(temp_value)
            else:
                exit(56)

        elif instr.opcode() == "POPS":
            if len(instr.args()) != 1:
                exit(32)

            # Argument musí být proměnná
            if instr.args()[0].type() != "var":
                exit(32)

            if len(interpret.data_stack()) > 0:
                temp_value = interpret.data_stack_pop()
                frames.set_var(instr.args()[0], temp_value)
            else:
                exit(56)

        i = i+1

    exit(0)
