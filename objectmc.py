from inspect import Signature, Parameter, isfunction
from os.path import join, exists
from shutil import rmtree
from dis import Bytecode
from os import makedirs
from json import dumps

__all__ = ["ObjectMC", "load", "tick", "mcfunction", "ignore"]

class ObjectMC:
    class Library:
        def len(self):
            return self.argmap(Signature([Parameter("obj", Parameter.POSITIONAL_OR_KEYWORD)])) + \
                   [f"data modify storage {self.id}:data Temporary append value " + "{Type:\"Integer\"}",
                    f"execute store result storage {self.id}:data Temporary[-1].Value int 1 run data get storage {self.id}:data Variables.obj.Value"] + \
                   self.store_result()
        
        def min(self):
            return self.argmap(Signature([Parameter("num1", Parameter.POSITIONAL_OR_KEYWORD), Parameter("num2", Parameter.POSITIONAL_OR_KEYWORD)])) + \
                   [f"data modify storage {self.id}:data Temporary append from storage {self.id}:data Variables.num1",
                    f"data modify storage {self.id}:data Temporary append from storage {self.id}:data Variables.num2"] + \
                   self.load_math() + \
                   self.math_operation("<") + \
                   self.store_math() + \
                   self.store_result()
        
        def max(self):
            return self.argmap(Signature([Parameter("num1", Parameter.POSITIONAL_OR_KEYWORD), Parameter("num2", Parameter.POSITIONAL_OR_KEYWORD)])) + \
                   [f"data modify storage {self.id}:data Temporary append from storage {self.id}:data Variables.num1",
                    f"data modify storage {self.id}:data Temporary append from storage {self.id}:data Variables.num2"] + \
                   self.load_math() + \
                   self.math_operation(">") + \
                   self.store_math() + \
                   self.store_result()
        
        def exit(self):
            return [f"scoreboard players set exited {self.id}_data 1"]
        
        def print(self):
            commands = self.argmap(Signature([Parameter("objs", Parameter.VAR_POSITIONAL), Parameter("sep", Parameter.KEYWORD_ONLY, default=" ")])) + \
                       [f"data modify storage {self.id}:data Args set value []",
                        f"data modify storage {self.id}:data Kwargs set value " + "{}",
                        f"data modify storage {self.id}:data Args append from storage {self.id}:data Variables.objs",
                        f"function {self.id}:core/len",
                        f"execute if data storage {self.id}:data Result" + "{Value:0} run tellraw @a [{\"text\":\" \"}]"]
            for argc in range(1, 17):
                commands.append(f"execute if data storage {self.id}:data Result" + "{Value:" + str(argc) + "} run tellraw @a [" + (",{\"storage\":\"" + self.id + ":data\",\"nbt\":\"Variables.sep.Value\"},").join(["{\"storage\":\"" + self.id + ":data\",\"nbt\":\"Variables.objs.Value[" + str(i) + "].Value\"}" for i in range(argc)]) + "]")
            commands += self.load_none() + self.store_result()
            return commands
    
    class Internal:
        def pow(self):
            return [f"scoreboard players operation 1 {self.id}_data *= 3 {self.id}_data",
                    f"scoreboard players remove 2 {self.id}_data 1",
                    f"execute if score 2 {self.id}_data matches 2.. run function {self.id}:internal/pow"]
    
    def __init__(self, name=None, id=None):
        self.name = name
        self.id = id
        self.functions = None
        self.target_functions = None
    
    def argmap(self, sign):
        commands = []
        for name, param in sign.parameters.items():
            if param.kind == param.POSITIONAL_ONLY or param.kind == param.POSITIONAL_OR_KEYWORD:
                if param.default is not param.empty:
                    commands += self.load_value(param.default) + \
                                self.store(name)
                commands += [f"data modify storage {self.id}:data Variables.{name} set from storage {self.id}:data Args[-1]",
                             f"data remove storage {self.id}:data Args[-1]"]
            elif param.kind == param.KEYWORD_ONLY:
                if param.default is not param.empty:
                    commands += self.load_value(param.default) + \
                                self.store(name)
                commands += [f"data modify storage {self.id}:data Variables.{name} set from storage {self.id}:data Kwargs.{name}",
                             f"data remove storage {self.id}:data Kwargs.{name}"]
            elif param.kind == param.VAR_POSITIONAL:
                commands += [f"data modify storage {self.id}:data Variables.{name} set value " + "{Type:\"List\"}",
                             f"data modify storage {self.id}:data Variables.{name}.Value set from storage {self.id}:data Args"]
            elif param.kind == param.VAR_KEYWORD:
                commands += [f"data modify storage {self.id}:data Variables.{name} set value " + "{Type:\"Dictionary\"}",
                             f"data modify storage {self.id}:data Variables.{name}.Value set from storage {self.id}:data Kwargs"]
        return commands
    
    def load_objectmc(self):
        return [f"data modify storage {self.id}:data Variables set value " + "{}",
                f"data modify storage {self.id}:data Temporary set value []",
                f"scoreboard objectives add {self.id}_data dummy"]
    
    def load_string(self, string):
        return [f"data modify storage {self.id}:data Temporary append value " + "{Type:\"String\",Value:" + dumps(string) + "}"]
    
    def load_integer(self, integer):
        return [f"data modify storage {self.id}:data Temporary append value " + "{Type:\"Integer\",Value:" + dumps(integer) + "}"]
    
    def load_none(self):
        return [f"data modify storage {self.id}:data Temporary append value " + "{Type:\"NoneType\",Value:\"None\"}"]
    
    def load_value(self, value):
        if type(value) == str:
            return self.load_string(value)
        elif type(value) == int:
            return self.load_integer(value)
        elif value is None:
            return self.load_none()
        else:
            raise ValueError(f"ObjectMC doesn't support {type(value).__name__} type")
    
    def pop_temp(self):
        return [f"data remove storage {self.id}:data Temporary[-1]"]
    
    def store(self, name):
        return [f"data modify storage {self.id}:data Variables.{name} set from storage {self.id}:data Temporary[-1]"] + self.pop_temp()
    
    def load(self, name):
        return [f"execute unless data storage {self.id}:data Variables.{name} run " + "tellraw @a [{\"text\":\"NameError: name '" + name + "' is not defined\",\"color\":\"red\"}]",
                f"execute unless data storage {self.id}:data Variables.{name} run function {self.id}:core/exit",
                f"data modify storage {self.id}:data Temporary append from storage {self.id}:data Variables.{name}"]
    
    def call(self, argcount):
        target_function = self.target_functions.pop()
        return [f"data modify storage {self.id}:data Args set value []"] + \
               ([f"data modify storage {self.id}:data Args prepend from storage {self.id}:data Temporary[-1]"] + \
                self.pop_temp()) * argcount + \
               [f"function {self.id}:{target_function}",
                f"data modify storage {self.id}:data Temporary append from storage {self.id}:data Result"]
    
    def kwcall(self, argcount):
        commands = [f"data modify storage {self.id}:data Args set value []",
                    f"data modify storage {self.id}:data Kwargs set value " + "{}"]
        for arg in self.kwargs:
            commands += [f"data modify storage {self.id}:data Kwargs.{arg} set from storage {self.id}:data Temporary[-1]"] + \
                        self.pop_temp()
            argcount -= 1
        target_function = self.target_functions.pop()
        commands += ([f"data modify storage {self.id}:data Args prepend from storage {self.id}:data Temporary[-1]"] + \
                     self.pop_temp()) * argcount + \
                    [f"function {self.id}:{target_function}",
                     f"data modify storage {self.id}:data Temporary append from storage {self.id}:data Result"]
        return commands
    
    def store_result(self):
        return [f"data modify storage {self.id}:data Result set from storage {self.id}:data Temporary[-1]"] + self.pop_temp()
    
    def load_math(self):
        commands = []
        for i in reversed(range(1, 3)):
            commands += [f"execute store result score {i} {self.id}_data run data get storage {self.id}:data Temporary[-1].Value"] + \
                        self.pop_temp()
        return commands
    
    def math_operation(self, operation):
        return [f"scoreboard players operation 1 {self.id}_data {operation} 2 {self.id}_data"]
    
    def store_math(self):
        return [f"data modify storage {self.id}:data Temporary append value " + "{\"Type\":\"Integer\"}",
                f"execute store result storage {self.id}:data Temporary[-1].Value int 1 run scoreboard players get 1 {self.id}_data"]
    
    def add(self):
        return self.load_math() + \
               self.math_operation("+=") + \
               self.store_math()
    
    def subtract(self):
        return self.load_math() + \
               self.math_operation("-=") + \
               self.store_math()
    
    def multiply(self):
        return self.load_math() + \
               self.math_operation("*=") + \
               self.store_math()
    
    def divide(self):
        return self.load_math() + \
               self.math_operation("/=") + \
               self.store_math()
    
    def modulo(self):
        return self.load_math() + \
               self.math_operation("%=") + \
               self.store_math()
    
    def power(self):
        return self.load_math() + \
               [f"scoreboard players operation 3 {self.id}_data = 1 {self.id}_data",
                f"function {self.id}:internal/pow"] + \
               self.store_math()
    
    def compile(self, function):
        bytecode = Bytecode(function)
        commands = []
        for instruction in bytecode:
            if instruction.opname == "LOAD_CONST":
                if type(instruction.argval) == tuple:
                    self.kwargs = reversed(instruction.argval)
                else:
                    commands += self.load_value(instruction.argval)
            elif instruction.opname == "STORE_FAST" or instruction.opname == "STORE_GLOBAL":
                commands += self.store(instruction.argval)
            elif instruction.opname == "LOAD_FAST" or instruction.opname == "LOAD_GLOBAL":
                if instruction.argval in self.functions["core"]:
                    self.target_functions.append(f"core/{instruction.argval}")
                elif instruction.argval in self.functions["internal"]:
                    self.target_functions.append(f"internal/{instruction.argval}")
                elif instruction.argval in self.functions["defined"]:
                    self.target_functions.append(f"defined/{instruction.argval}")
                else:
                    commands += self.load(instruction.argval)
            elif instruction.opname == "CALL_FUNCTION":
                commands += self.call(instruction.argval)
            elif instruction.opname == "CALL_FUNCTION_KW":
                commands += self.kwcall(instruction.argval)
            elif instruction.opname == "RETURN_VALUE":
                commands += self.store_result()
            elif instruction.opname == "BINARY_ADD":
                commands += self.add()
            elif instruction.opname == "BINARY_SUBTRACT":
                commands += self.subtract()
            elif instruction.opname == "BINARY_MULTIPLY":
                commands += self.multiply()
            elif instruction.opname == "BINARY_TRUE_DIVIDE" or instruction.opname == "BINARY_FLOOR_DIVIDE":
                commands += self.divide()
            elif instruction.opname == "BINARY_MODULO":
                commands += self.modulo()
            elif instruction.opname == "BINARY_POWER":
                commands += self.power()
        return map(lambda command: f"execute if score exited {self.id}_data matches 0 run " + command, commands)
    
    def export(self, functionpack):
        @ignore
        def export(path="."):
            if exists(join(path, self.name)):
                rmtree(join(path, self.name))
            makedirs(join(path, self.name, "data", "minecraft", "tags", "functions"))
            makedirs(join(path, self.name, "data", self.id, "functions", "core"))
            makedirs(join(path, self.name, "data", self.id, "functions", "internal"))
            makedirs(join(path, self.name, "data", self.id, "functions", "defined"))
            makedirs(join(path, self.name, "data", self.id, "functions", "event"))
            with open(join(path, self.name, "pack.mcmeta"), "w") as pack:
                pack.write(dumps({
                    "pack": {
                        "pack_format": 10,
                        "description": functionpack.description if hasattr(functionpack, "description") else "ObjectMC datapack"
                    }
                }))
            with open(join(path, self.name, "data", "minecraft", "tags", "functions", "load.json"), "w") as load:
                load.write(dumps({
                    "values": [
                        f"{self.id}:event/load"
                    ]
                }))
            with open(join(path, self.name, "data", "minecraft", "tags", "functions", "tick.json"), "w") as tick:
                tick.write(dumps({
                    "values": [
                        f"{self.id}:event/tick"
                    ]
                }))
            self.functions = {
                "core": [],
                "internal": [],
                "defined": []
            }
            self.target_functions = []
            for name in dir(self.Library):
                func = getattr(self.Library, name)
                if isfunction(func):
                    self.functions["core"].append(name)
                    with open(join(path, self.name, "data", self.id, "functions", "core", f"{name}.mcfunction"), "w") as mcfunc:
                        mcfunc.write("\n".join(func(self)))
            for name in dir(self.Internal):
                func = getattr(self.Internal, name)
                if isfunction(func):
                    self.functions["internal"].append(name)
                    with open(join(path, self.name, "data", self.id, "functions", "internal", f"{name}.mcfunction"), "w") as mcfunc:
                        mcfunc.write("\n".join(func(self)))
            for name in dir(functionpack):
                func = getattr(functionpack, name)
                if isfunction(func):
                    self.functions["defined"].append(name)
            load = open(join(path, self.name, "data", self.id, "functions", "event", "load.mcfunction"), "w")
            load.write(f"scoreboard players set exited {self.id}_data 0\n" + "\n".join(self.load_objectmc()) + "\n")
            tick = open(join(path, self.name, "data", self.id, "functions", "event", "tick.mcfunction"), "w")
            for name in self.functions["defined"]:
                func = getattr(functionpack, name)
                if not hasattr(func, "mode"):
                    func.mode = "mcfunction"
                if func.mode != "ignore":
                    source = "\n".join(self.compile(func)) + "\n"
                    with open(join(path, self.name, "data", self.id, "functions", "defined", f"{name}.mcfunction"), "w") as mcfunc:
                        mcfunc.write(source)
                    caller = f"scoreboard players set exited {self.id}_data 0\nfunction {self.id}:defined/{name}"
                    if func.mode == "load":
                        load.write(caller)
                    if func.mode == "tick":
                        tick.write(caller)
            load.close()
            tick.close()
        return export
    
    def __call__(self, cls):
        if self.name == None:
            self.name = cls.__name__
        if self.id == None:
            self.id = cls.__name__.lower()
        cls.export = self.export(cls)
        return cls

def mode(function, mode):
    function.mode = mode
    return function

def load(function):
    return mode(function, "load")

def tick(function):
    return mode(function, "tick")

def mcfunction(function):
    return mode(function, "mcfunction")

def ignore(function):
    return mode(function, "ignore")
