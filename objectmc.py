from inspect import Signature, Parameter, signature, isfunction
from os.path import join, exists
from json import dumps, loads
from shutil import rmtree
from dis import Bytecode
from re import fullmatch
from os import makedirs

__all__ = ["ObjectMC", "load", "tick", "mcfunction", "ignore"]

class ObjectMC:
    class Library:
        # Python built-ins
        
        def len(self):
            return self.argmap(Signature([Parameter("obj", Parameter.POSITIONAL_OR_KEYWORD)]), "len") + \
                   [f"data modify storage {self.id}:data Temporary append value " + "{Type:\"int\"}",
                    f"execute store result storage {self.id}:data Temporary[-1].Value int 1 run data get storage {self.id}:data Variables.obj.Value"] + \
                   self.store_result()
        
        def min(self):
            return self.argmap(Signature([Parameter("num1", Parameter.POSITIONAL_OR_KEYWORD), Parameter("num2", Parameter.POSITIONAL_OR_KEYWORD)]), "min") + \
                   [f"data modify storage {self.id}:data Temporary append from storage {self.id}:data Variables.num1",
                    f"data modify storage {self.id}:data Temporary append from storage {self.id}:data Variables.num2"] + \
                   self.load_math() + \
                   self.math_operation("<") + \
                   self.store_math() + \
                   self.store_result()
        
        def max(self):
            return self.argmap(Signature([Parameter("num1", Parameter.POSITIONAL_OR_KEYWORD), Parameter("num2", Parameter.POSITIONAL_OR_KEYWORD)]), "max") + \
                   [f"data modify storage {self.id}:data Temporary append from storage {self.id}:data Variables.num1",
                    f"data modify storage {self.id}:data Temporary append from storage {self.id}:data Variables.num2"] + \
                   self.load_math() + \
                   self.math_operation(">") + \
                   self.store_math() + \
                   self.store_result()
        
        def exit(self):
            return self.argmap(Signature(), "exit") + \
                   [f"scoreboard players set exited {self.id}_data 1"] + \
                   self.load_none() + self.store_result()
        
        def print(self):
            commands = self.argmap(Signature([Parameter("objs", Parameter.VAR_POSITIONAL), Parameter("sep", Parameter.KEYWORD_ONLY, default=" ")]), "print") + \
                       [f"data modify storage {self.id}:data Args set value []",
                        f"data modify storage {self.id}:data Kwargs set value " + "{}",
                        f"data modify storage {self.id}:data Args append from storage {self.id}:data Variables.objs",
                        f"function {self.id}:core/len",
                        f"execute if data storage {self.id}:data Result" + "{Value:0} run tellraw @a [{\"text\":\" \"}]"]
            for argc in range(1, 17):
                commands.append(f"execute if data storage {self.id}:data Result" + "{Value:" + str(argc) + "} run tellraw @a [" + (",{\"storage\":\"" + self.id + ":data\",\"nbt\":\"Variables.sep.Value\"},").join(["{\"storage\":\"" + self.id + ":data\",\"nbt\":\"Variables.objs.Value[" + str(i) + "].Value\"}" for i in range(argc)]) + "]")
            commands += self.load_none() + self.store_result()
            return commands
        
        def bool(self):
            return self.argmap(Signature([Parameter("obj", Parameter.POSITIONAL_OR_KEYWORD, default=False)]), "bool") + \
                   self.load("obj") + \
                   [f"scoreboard players set 2 {self.id}_data 0",
                    f"data modify storage {self.id}:data Operation set from storage {self.id}:data Temporary[-1]",
                    f"execute if score 2 {self.id}_data matches 0 run store result score 1 {self.id}_data run data modify storage {self.id}:data Operation set value " + "{\"Type\":\"NoneType\",\"Value\":\"None\"}",
                    f"execute if score 2 {self.id}_data matches 0 if score 1 {self.id}_data matches 0 run " + self.load_boolean(False)[0],
                    f"execute if score 2 {self.id}_data matches 0 if score 1 {self.id}_data matches 0 run scoreboard players set 2 {self.id}_data 1",
                    f"data modify storage {self.id}:data Operation set from storage {self.id}:data Temporary[-1]",
                    f"execute if score 2 {self.id}_data matches 0 store result score 1 {self.id}_data run data modify storage {self.id}:data Operation set value " + "{\"Type\":\"bool\",\"Value\":\"False\"}",
                    f"execute if score 2 {self.id}_data matches 0 if score 1 {self.id}_data matches 0 run " + self.load_boolean(False)[0],
                    f"execute if score 2 {self.id}_data matches 0 if score 1 {self.id}_data matches 0 run scoreboard players set 2 {self.id}_data 1",
                    f"data modify storage {self.id}:data Operation set from storage {self.id}:data Temporary[-1]",
                    f"execute if score 2 {self.id}_data matches 0 store result score 1 {self.id}_data run data modify storage {self.id}:data Operation set value " + "{\"Type\":\"int\",\"Value\":0}",
                    f"execute if score 2 {self.id}_data matches 0 if score 1 {self.id}_data matches 0 run " + self.load_boolean(False)[0],
                    f"execute if score 2 {self.id}_data matches 0 if score 1 {self.id}_data matches 0 run scoreboard players set 2 {self.id}_data 1",
                    f"execute if score 2 {self.id}_data matches 0 run data modify storage {self.id}:data Args set value []",
                    f"execute if score 2 {self.id}_data matches 0 run data modify storage {self.id}:data Kwargs set value " + "{}",
                    f"execute if score 2 {self.id}_data matches 0 run data modify storage {self.id}:data Args append from storage {self.id}:data Temporary[-1]",
                    f"execute if score 2 {self.id}_data matches 0 run function {self.id}:core/len",
                    f"execute if score 2 {self.id}_data matches 0 if data storage {self.id}:data Result" + "{Value:0} run " + self.load_boolean(False)[0],
                    f"execute if score 2 {self.id}_data matches 0 if data storage {self.id}:data Result" + "{Value:0} run " + f"scoreboard players set 2 {self.id}_data 1",
                    f"data remove storage {self.id}:data Result",
                    f"execute if score 2 {self.id}_data matches 0 run " + self.load_boolean(True)[0],
                    f"data remove storage {self.id}:data Temporary[-2]"] + \
                   self.load_none() + self.store_result()
        
        
        # Minecraft API
        
        def getblock(self):
            return self.argmap(Signature([Parameter("x", Parameter.POSITIONAL_OR_KEYWORD), Parameter("y", Parameter.POSITIONAL_OR_KEYWORD), Parameter("z", Parameter.POSITIONAL_OR_KEYWORD)]), "getblock") + \
                   ["summon minecraft:armor_stand ~ ~ ~ {NoGravity:1b,Invisible:1b,Invulnerable:1b,Marker:1b,Small:1b,Tags:[\"new\"]}",
                    f"data modify storage {self.id}:data Operation set value []",
                    f"data modify storage {self.id}:data Operation append from storage {self.id}:data Variables.x.Value",
                    f"data modify storage {self.id}:data Operation append from storage {self.id}:data Variables.y.Value",
                    f"data modify storage {self.id}:data Operation append from storage {self.id}:data Variables.z.Value",
                    f"data modify entity @e[tag=new,limit=1] Pos set from storage {self.id}:data Operation",
                    f"scoreboard players operation @e[tag=new,limit=1] {self.id}_blocks = id {self.id}_blocks",
                    f"scoreboard players add id {self.id}_blocks 1",
                    f"data modify storage {self.id}:data Temporary append value " + "{Type:\"Block\",Value:\"Block\",Attributes:{getid:{Type:\"Function\",Value:\"_block_getid\",Kind:\"core\"},setid:{Type:\"Function\",Value:\"_block_setid\",Kind:\"core\"}}}",
                    f"execute store result storage {self.id}:data Temporary[-1].Attributes.id int 1 run scoreboard players get @e[tag=new,limit=1] {self.id}_blocks",
                    "tag @e[tag=new,limit=1] remove new"] + \
                   self.store_result()
        
        def _block_getid(self):
            return self.argmap(Signature([Parameter("self", Parameter.POSITIONAL_OR_KEYWORD)]), "getid") + \
                   [f"execute store result score current {self.id}_blocks run data get storage {self.id}:data Variables.self.Attributes.id"] + \
                   [f"execute as @e[type=minecraft:armor_stand] if score @s {self.id}_blocks = current {self.id}_blocks at @s if block ~ ~ ~ {block_id} run data modify storage {self.id}:data Result set value " + "{Type:\"str\",Value:\"" + block_id + "\"}" for block_id in self.blocks]
        
        def _block_setid(self):
            commands = self.argmap(Signature([Parameter("self", Parameter.POSITIONAL_OR_KEYWORD), Parameter("id", Parameter.POSITIONAL_OR_KEYWORD)]), "setid") + \
                   [f"execute store result score current {self.id}_blocks run data get storage {self.id}:data Variables.self.Attributes.id"]
            for block_id in self.blocks:
                commands += [f"data modify storage {self.id}:data Operation set from storage {self.id}:data Variables.id.Value",
                             f"execute store success score 1 {self.id}_data run data modify storage {self.id}:data Operation set value \"{block_id}\"",
                             f"execute as @e[type=minecraft:armor_stand] if score @s {self.id}_blocks = current {self.id}_blocks at @s if score 1 {self.id}_data matches 0 run setblock ~ ~ ~ {block_id}"]
            return commands
    
    
    class Internal:
        def pow(self):
            return [f"scoreboard players operation 1 {self.id}_data *= 3 {self.id}_data",
                    f"scoreboard players remove 2 {self.id}_data 1",
                    f"execute if score 2 {self.id}_data matches 2.. run function {self.id}:internal/pow"]
    
    
    def __init__(self, id=None, name=None, description=None, blocks=None, version=None):
        self.id = id
        self.name = name
        self.description = description
        self.functions = None
        self.blocks = blocks
        if self.blocks == None:
            with open("blocks.json") as blocks:
                self.blocks = loads(blocks.read())
        self.version = version
        if self.version == None:
            self.version = 9
    
    def argmap(self, sign, funcname):
        commands = []
        for name, param in reversed(sign.parameters.items()):
            if param.kind == param.POSITIONAL_ONLY or param.kind == param.POSITIONAL_OR_KEYWORD:
                if param.default is not param.empty:
                    commands += map(lambda command: f"execute unless data storage {self.id}:data Args[-1] run " + command, self.load_value(param.default) + \
                                                                                                                           self.store(name))
                else:
                    commands += [f"execute unless data storage {self.id}:data Args[-1] run " + "tellraw @a [{\"text\":\"TypeError: " + funcname + "() missing required argument '" + name +"'\",\"color\":\"red\"}]",
                                 f"execute unless data storage {self.id}:data Args[-1] run function {self.id}:core/exit"]
                commands += [f"execute if data storage {self.id}:data Args[-1] run data modify storage {self.id}:data Variables.{name} set from storage {self.id}:data Args[-1]",
                             f"execute if data storage {self.id}:data Args[-1] run data remove storage {self.id}:data Args[-1]"]
            elif param.kind == param.KEYWORD_ONLY:
                if param.default is not param.empty:
                    commands += map(lambda command: f"execute unless data storage {self.id}:data Kwargs.{name} run " + command, self.load_value(param.default) + \
                                                                                                                           self.store(name))
                else:
                    commands += [f"execute unless data storage {self.id}:data Kwargs.{name} run " + "tellraw @a [{\"text\":\"TypeError: " + funcname + "() missing required argument '" + name +"'\",\"color\":\"red\"}]",
                                 f"execute unless data storage {self.id}:data Kwargs.{name} run function {self.id}:core/exit"]
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
                f"scoreboard objectives add {self.id}_data dummy",
                f"scoreboard objectives add {self.id}_blocks dummy",
                f"execute unless score id {self.id}_blocks = id {self.id}_blocks run scoreboard players set id {self.id}_blocks 0"]
    
    def load_string(self, string):
        return [f"data modify storage {self.id}:data Temporary append value " + "{Type:\"str\",Value:" + dumps(string) + "}"]
    
    def load_integer(self, integer):
        return [f"data modify storage {self.id}:data Temporary append value " + "{Type:\"int\",Value:" + dumps(integer) + "}"]
    
    def load_boolean(self, boolean):
        return [f"data modify storage {self.id}:data Temporary append value " + "{\"Type\":\"bool\",\"Value\":\"" + str(boolean) + "\"}"]
    
    def load_none(self):
        return [f"data modify storage {self.id}:data Temporary append value " + "{Type:\"NoneType\",Value:\"None\"}"]
    
    def load_value(self, value):
        if type(value) == str:
            return self.load_string(value)
        elif type(value) == int:
            return self.load_integer(value)
        elif type(value) == bool:
            return self.load_boolean(value)
        elif value is None:
            return self.load_none()
        else:
            raise ValueError(f"ObjectMC doesn't support {type(value).__name__} type")
    
    def load_attribute(self, name):
        return [f"execute unless data storage {self.id}:data Temporary[-1].Attributes.{name} run " + "tellraw @a [{\"text\":\"AttributeError: '\",\"color\":\"red\"},{\"storage\":\"" + self.id + ":data\",\"nbt\":\"Temporary[-1].Type\"},{\"text\":\"' object has no attribute '" + name + "'\",\"color\":\"red\"}]",
                f"execute unless data storage {self.id}:data Temporary[-1].Attributes.{name} run function {self.id}:core/exit",
                f"data modify storage {self.id}:data Temporary append from storage {self.id}:data Temporary[-1].Attributes.{name}",
                f"data modify storage {self.id}:data Operation set from storage {self.id}:data Temporary[-1]",
                f"execute store success score 1 {self.id}_data run data modify storage {self.id}:data Operation.Type set value \"Function\"",
                f"execute if score 1 {self.id}_data matches 0 run data modify storage {self.id}:data Temporary[-1].Self set from storage {self.id}:data Temporary[-2]",
                f"data remove storage {self.id}:data Temporary[-2]"]
    
    def pop_temp(self):
        return [f"data remove storage {self.id}:data Temporary[-1]"]
    
    def store(self, name):
        return [f"data modify storage {self.id}:data Variables.{name} set from storage {self.id}:data Temporary[-1]"] + self.pop_temp()
    
    def load(self, name):
        return [f"execute unless data storage {self.id}:data Variables.{name} run " + "tellraw @a [{\"text\":\"NameError: name '" + name + "' is not defined\",\"color\":\"red\"}]",
                f"execute unless data storage {self.id}:data Variables.{name} run function {self.id}:core/exit",
                f"data modify storage {self.id}:data Temporary append from storage {self.id}:data Variables.{name}"]
    
    def invoke(self):
        commands = [f"execute if data storage {self.id}:data Temporary[-1].Self run data modify storage {self.id}:data Args prepend from storage {self.id}:data Temporary[-1].Self",
                    f"data modify storage {self.id}:data Operation set from storage {self.id}:data Temporary[-1]",
                    f"execute store success score 1 {self.id}_data run data modify storage {self.id}:data Operation.Type set value \"Function\"",
                    f"execute if score 1 {self.id}_data matches 1 run " + "tellraw @a [{\"text\":\"TypeError: object '\",\"color\":\"red\"},{\"storage\":\"" + self.id + ":data\",\"nbt\":\"Temporary[-1].Type\"},{\"text\":\"' is not callable\",\"color\":\"red\"}]",
                    f"execute if score 1 {self.id}_data matches 1 run " + f"function {self.id}:core/exit",
                    f"scoreboard players set 2 {self.id}_data 1"]
        for function in self.functions["core"]:
            commands += [f"execute if score 2 {self.id}_data matches 1 run data modify storage {self.id}:data Operation set from storage {self.id}:data Temporary[-1]",
                         f"execute if score 2 {self.id}_data matches 1 store success score 1 {self.id}_data run data modify storage {self.id}:data Operation.Value set value {dumps(function)}",
                         f"execute if score 2 {self.id}_data matches 1 store success score 3 {self.id}_data run data modify storage {self.id}:data Operation.Kind set value \"core\"",
                         f"execute if score 2 {self.id}_data matches 1 run scoreboard players operation 1 {self.id}_data += 3 {self.id}_data",
                         f"execute if score 2 {self.id}_data matches 1 if score 1 {self.id}_data matches 0 run function {self.id}:core/{function}",
                         f"execute if score 2 {self.id}_data matches 1 if score 1 {self.id}_data matches 0 run scoreboard players set 2 {self.id}_data 0"]
        for function in self.functions["defined"]:
            commands += [f"execute if score 2 {self.id}_data matches 1 run data modify storage {self.id}:data Operation set from storage {self.id}:data Temporary[-1]",
                         f"execute if score 2 {self.id}_data matches 1 store success score 1 {self.id}_data run data modify storage {self.id}:data Operation.Value set value {dumps(function)}",
                         f"execute if score 2 {self.id}_data matches 1 store success score 3 {self.id}_data run data modify storage {self.id}:data Operation.Kind set value \"defined\"",
                         f"execute if score 2 {self.id}_data matches 1 run scoreboard players operation 1 {self.id}_data += 3 {self.id}_data",
                         f"execute if score 2 {self.id}_data matches 1 if score 1 {self.id}_data matches 0 run function {self.id}:defined/{function}",
                         f"execute if score 2 {self.id}_data matches 1 if score 1 {self.id}_data matches 0 run scoreboard players set 2 {self.id}_data 0"]
        commands += self.pop_temp() + \
                    [f"data modify storage {self.id}:data Temporary append from storage {self.id}:data Result"]
        return commands
    
    def call(self, argcount):
        return [f"data modify storage {self.id}:data Args set value []"] + \
               ([f"data modify storage {self.id}:data Args prepend from storage {self.id}:data Temporary[-1]"] + \
                self.pop_temp()) * argcount + \
               self.invoke()
    
    def kwcall(self, argcount):
        commands = [f"data modify storage {self.id}:data Args set value []",
                    f"data modify storage {self.id}:data Kwargs set value " + "{}"]
        for arg in self.kwargs:
            commands += [f"data modify storage {self.id}:data Kwargs.{arg} set from storage {self.id}:data Temporary[-1]"] + \
                        self.pop_temp()
            argcount -= 1
        commands += ([f"data modify storage {self.id}:data Args prepend from storage {self.id}:data Temporary[-1]"] + \
                     self.pop_temp()) * argcount + \
                    self.invoke()
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
        return [f"data modify storage {self.id}:data Temporary append value " + "{\"Type\":\"int\"}",
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
    
    def compare_equals(self):
        return [f"execute store success score 1 {self.id}_data run data modify storage {self.id}:data Temporary[-1] set from storage {self.id}:data Temporary[-2]"] + \
               self.pop_temp() * 2 + \
               [f"execute if score 1 {self.id}_data matches 1 run " + self.load_boolean(False)[0],
                f"execute unless score 1 {self.id}_data matches 1 run " + self.load_boolean(True)[0]]
    
    def compare_not_equals(self):
        return [f"execute store success score 1 {self.id}_data run data modify storage {self.id}:data Temporary[-1] set from storage {self.id}:data Temporary[-2]"] + \
               self.pop_temp() * 2 + \
               [f"execute if score 1 {self.id}_data matches 1 run " + self.load_boolean(True)[0],
                f"execute unless score 1 {self.id}_data matches 1 run " + self.load_boolean(False)[0]]
    
    def compare_math(self, operation):
        return [f"execute if score 1 {self.id}_data {operation} 2 {self.id}_data run " + self.load_boolean(True)[0],
                f"execute unless score 1 {self.id}_data {operation} 2 {self.id}_data run "  + self.load_boolean(False)[0]]
    
    def compare_less(self):
        return self.load_math() + \
               self.compare_math("<")
    
    def compare_less_or_equals(self):
        return self.load_math() + \
               self.compare_math("<=")
    
    def compare_greater(self):
        return self.load_math() + \
               self.compare_math(">")
    
    def compare_greater_or_equals(self):
        return self.load_math() + \
               self.compare_math(">=")
    
    def logic_not(self):
        return [f"scoreboard players set 2 {self.id}_data 0",
                f"data modify storage {self.id}:data Operation set from storage {self.id}:data Temporary[-1]",
                f"execute if score 2 {self.id}_data matches 0 run execute store result score 1 {self.id}_data run data modify storage {self.id}:data Operation set value " + "{\"Type\":\"bool\",\"Value\":\"True\"}",
                f"execute if score 2 {self.id}_data matches 0 run execute if score 1 {self.id}_data matches 0 run " + self.load_boolean(False)[0],
                f"execute if score 2 {self.id}_data matches 0 run execute if score 1 {self.id}_data matches 0 run scoreboard players set 2 {self.id}_data 1",
                f"data modify storage {self.id}:data Operation set from storage {self.id}:data Temporary[-1]",
                f"execute if score 2 {self.id}_data matches 0 run execute store result score 1 {self.id}_data run data modify storage {self.id}:data Operation set value " + "{\"Type\":\"bool\",\"Value\":\"False\"}",
                f"execute if score 2 {self.id}_data matches 0 run execute if score 1 {self.id}_data matches 0 run " + self.load_boolean(True)[0],
                f"execute if score 2 {self.id}_data matches 0 run execute if score 1 {self.id}_data matches 0 run scoreboard players set 2 {self.id}_data 1",
                f"data remove storage {self.id}:data Temporary[-2]"]
    
    def compile(self, function):
        bytecode = Bytecode(function)
        commands = self.argmap(signature(function), function.__name__)
        for instruction in bytecode:
            print(instruction)
            if instruction.opname == "LOAD_CONST":
                if type(instruction.argval) == tuple:
                    self.kwargs = reversed(instruction.argval)
                else:
                    commands += self.load_value(instruction.argval)
            elif instruction.opname == "STORE_FAST" or instruction.opname == "STORE_GLOBAL":
                commands += self.store(instruction.argval)
            elif instruction.opname == "LOAD_FAST" or instruction.opname == "LOAD_GLOBAL":
                commands += self.load(instruction.argval)
            elif instruction.opname == "LOAD_ATTR" or instruction.opname == "LOAD_METHOD":
                commands += self.load_attribute(instruction.argval)
            elif instruction.opname == "CALL_FUNCTION" or instruction.opname == "CALL_METHOD":
                commands += self.call(instruction.argval)
            elif instruction.opname == "CALL_FUNCTION_KW" or instruction.opname == "CALL_KW_METHOD":
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
            elif instruction.opname == "COMPARE_OP":
                if instruction.arg == 0:
                    commands += self.compare_less()
                elif instruction.arg == 1:
                    commands += self.compare_less_or_equals()
                elif instruction.arg == 2:
                    commands += self.compare_equals()
                elif instruction.arg == 3:
                    commands += self.compare_not_equals()
                elif instruction.arg == 4:
                    commands += self.compare_greater()
                elif instruction.arg == 5:
                    commands += self.compare_greater_or_equals()
            elif instruction.opname == "UNARY_NOT":
                commands += self.logic_not()
            elif instruction.opname == "POP_TOP":
                commands += self.pop_temp()
        return list(map(lambda command: f"execute if score exited {self.id}_data matches 0 run " + command, commands))
    
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
                        "pack_format": self.version,
                        "description": "ObjectMC datapack" if self.description == None else self.description
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
                        mcfunc.write("\n".join(list(map(lambda command: f"execute if score exited {self.id}_data matches 0 run " + command, func(self))) + [f"scoreboard players set 2 {self.id}_data 0"]))
            for name in dir(self.Internal):
                func = getattr(self.Internal, name)
                if isfunction(func):
                    self.functions["internal"].append(name)
                    with open(join(path, self.name, "data", self.id, "functions", "internal", f"{name}.mcfunction"), "w") as mcfunc:
                        mcfunc.write("\n".join(func(self)))
            for name in dir(functionpack):
                if fullmatch("[a-z0-9_]+", name):
                    func = getattr(functionpack, name)
                    if isfunction(func):
                        self.functions["defined"].append(name)
            load = open(join(path, self.name, "data", self.id, "functions", "event", "load.mcfunction"), "w")
            load_commands = self.load_objectmc()
            for name in self.functions["core"]:
                if not name.startswith("_"):
                    load_commands += [f"data modify storage {self.id}:data Variables.{name} set value " + "{Type:\"Function\",Value:" + dumps(name) + ",Kind:\"core\"}"]
            for name in self.functions["defined"]:
                load_commands += [f"data modify storage {self.id}:data Variables.{name} set value " + "{Type:\"Function\",Value:" + dumps(name) + ",Kind:\"defined\"}"]
            load.write(f"scoreboard players set exited {self.id}_data 0\n" + "\n".join(load_commands) + "\n")
            tick = open(join(path, self.name, "data", self.id, "functions", "event", "tick.mcfunction"), "w")
            for name in self.functions["defined"]:
                func = getattr(functionpack, name)
                if not hasattr(func, "mode"):
                    func.mode = "mcfunction"
                if func.mode != "ignore":
                    source = "\n".join(self.compile(func) + [f"scoreboard players set 2 {self.id}_data 0"]) + "\n"
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
        if self.id == None:
            self.id = cls.__name__.lower()
        if self.name == None:
            self.name = cls.__name__
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
