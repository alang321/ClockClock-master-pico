from collections import namedtuple
import json


class PersistentStorage:
    # checkFunc optional check function that should return true when the value is in range
    persistent_var = namedtuple("storedVar", ("name", "defaultValue", "checkFunc"))

    def __init__(self, filename, stored_var_lst : List[persistent_var]):
        self.filename = filename + ".txt"
        
        self.__var_values = []
        self.__var_default_values = []
        self.__var_check_funcs = []
        self.__var_names = []
        
        for var in stored_var_lst:
            self.__var_default_values.append(var.defaultValue)
            self.__var_check_funcs.append(var.checkFunc)
            self.__var_names.append(var.name)
        
        self.read_flash()
        
    def set_var(self, name, value):
        ind = self.__get_index(name)
        check_func = self.__var_check_funcs[ind]
        if check_func != None:
            if check_func(value):
                self.__var_values[ind] = value
    
    def get_var(self, name):
        ind = self.__get_index(name)
        return self.__var_values[ind]
            
    def __get_index(self, name):
        return self.__var_names.index(name)
            
    def read_flash(self):
        try:
            if __debug__:
                print("trying to read from flash:", self.filename)
                
            f = open(self.filename, "r")
            string = f.readline()
            self.__var_values = json.loads(string)
            f.close()

            for index, check_func in enumerate(self.__var_check_funcs):
                if check_func != None:
                    if not check_func(self.__var_values[index]):
                        raise ValueError("Bad stored data", index)
        except Exception as e:
            if __debug__:
                print(str(e))
                
            self.reset_flash()
            
        if __debug__:
            print("read data:", list(zip(self.__var_names, self.__var_values)))

    def write_flash(self):
        data_str = json.dumps(self.__var_values)
        f = open(self.filename, "w")
        f.write(data_str)
        f.close()
        
        if __debug__:
            print("wrote to flash:", self.filename)
            print("data:", list(zip(self.__var_names, self.__var_values)))

    def reset_flash(self):
        self.__var_values = []
            
        for val in self.__var_default_values:
            self.__var_values.append(val)

        self.write_flash()
            
        if __debug__:
            print("Resetting flash to default values")
