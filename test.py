from objectmc import *

@ObjectMC()
class ObjectMCTest:
    description = "Just a test datapack"
    
    def concatenation():
        name = "Bob"
        print("Hello, ", name, "!", sep="")
    
    def length():
        test = "This message contains 35 characters"
        print("len(\"", test, "\") = ", len(test), sep="")
    
    def math():
        x = 10
        y = 4
        print("x =", x)
        print("y =", y)
        print("x + y =", x + y)
        print("x - y =", x - y)
        print("x * y =", x * y)
        print("x / y =", x / y)
        print("x % y =", x % y)
        print("x ** y =", x ** y)
        print("min(x, y) =", min(x, y))
        print("max(x, y) =", max(x, y))
    
    def logic():
        x = 22
        y = 9
        print("x =", x)
        print("y =", y)
        print("x < y", x < y)
        print("x <= y", x <= y)
        print("x == y", x == y)
        print("x != y", x != y)
        print("x > y", x > y)
        print("x >= y", x >= y)
        a = True
        b = False
        print("a =", a)
        print("b =", b)
        print("not a =", not a)
        print("not b =", not b)
    
    def conversion():
        a = 1
        b = 0
        c = "Bo"
        d = ""
        print("a =", a)
        print("b =", b)
        print("c =", c)
        print("d =", d)
        print("bool(a) =", bool(a))
        print("bool(b) =", bool(b))
        print("bool(c) =", bool(c))
        print("bool(d) =", bool(d))
    
    def recursion():
        recursion_1()
    
    def recursion_1():
        say_hello_from(recursion_1)
        recursion_2("Mine")
    
    def recursion_2(arg1):
        say_hello_from(recursion_2)
        recursion_3(arg1, "craft")
    
    def recursion_3(arg1, arg2):
        say_hello_from(recursion_3)
        print(arg1, arg2, sep="")
    
    def say_hello_from(func):
        print("Hello from", func)

ObjectMCTest.export(r"C:\Users\user\AppData\Roaming\.minecraft\saves\ObjectMC test\datapacks")
