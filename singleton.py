class singleton():
    #when defining a singleton class we use _instance and set it to None. 
    #This defines a class-level variable that will hold the only instance
    _instance = None
    init = True #setting this to false will give error

    #__new__ will create the object of this class and allocate memory
    #we're overridding base class' __new__ function
    def __new__(cls, a, b):#cls = the class Counter itself. cls inside __new__ refers to the class itself
        #check if _instance is None (i.e., first time creation), then initialize it
        if cls._instance is None:
            #In python every class is derived by base class "object" by default
            #__new__ is defined in class "object" and super() means calling base class's function
            cls._instance = super().__new__(cls)        
            #cls._instance.init = True    #you can define here also
        return cls._instance
    
    def __init__(self,a,b):
        if self.init:
            self.value = a
            self.value2 = b
            self.init = False
    
    def getvalue(self):
        return self.value * self.value2

obj = singleton(2,3).getvalue()
obj2 = singleton(4,5).getvalue()


#print(obj.value, obj.value2, obj2.value, obj2.value2)
print(obj, obj2)
