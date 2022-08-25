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

ObjectMCTest.export(r"C:\Users\user\AppData\Roaming\.minecraft\saves\ObjectMC test\datapacks")
