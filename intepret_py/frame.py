import sys

def printMessageAndExit(code, message):
    print(message, file=sys.stderr)
    sys.exit(code)

class frame():
    def __init__(self):
        #stack of frames
        self.frame_stack = []
        # DOCASNY RAMEC (TF)
        self.undefined = True
        self.tmp_frame = {}
        # GLOBALNI RAMEC
        self.global_frame = {}

    # PRACE S RAMCI

    def create_tmp_frame(self):
        """Inicializuje novy docasny ramec"""
        self.undefined = False
        self.tmp_frame = {}

    def push_tmp_frame_to_frame_stack(self):
        """Vlozi TF na zasobnik ramcu, po provedeni bude TF nedefinovan"""
        if self.undefined == False:
            # docasny ramec je definovan, muze byt presunut do zasobniku ramcu
            self.frame_stack.append(self.tmp_frame)
        else:
            printMessageAndExit(55, "ERROR: TEMPORARY FRAME NOT DEFINIED")
        self.undefined = True

    def pop_frame_stack_to_temporary_frame(self):
        """Presune ramec z vrcholu zasobniku ramcu do TF"""
        if len(self.frame_stack) > 0:
            # zasobnik ramcu obsahuje ramce, muzeme provest presun
            self.tmp_frame = self.frame_stack.pop()
            self.undefined = False
        else:
            printMessageAndExit(55, "ERROR: EMPTY FRAME STACK")


    def get_frame_stack(self):
        """Vrati cely zasobnik ramcu"""
        return self.frame_stack


    def get_frame(self, frame):
        """Vrati pozadovany ramec nebo NEDEFINOVAN"""
        if frame == 'GF':
            return self.global_frame
        elif frame == 'LF':
            if len(self.frame_stack) > 0:
                # v zasobniku se nachazi ramce, muzeme ziskat obsah lokalniho ramce
                return self.frame_stack[len(self.frame_stack) - 1]
            else:
                return 'NEDEFINOVAN'
        elif frame == 'TF':
            if self.undefined == True:
                # TF je nedefinovan
                return 'NEDEFINOVAN'
            else:
                return self.tmp_frame


    def parse_arg_variable_frame_and_name(self, i_arg_variable):
        """Vrati ramec a nazev promenne zvlast"""
        return i_arg_variable.split('@', 1)

    def get_arg_type_and_value(self, arg_type, arg_value): #arg_type = var, arg_value = GF@mantak
        if arg_type in ["string", "int", "bool", "nil", "type", "label"]:
            # vrati typ literalu + hodnotu, False (neni v promenne)
            return (arg_type, arg_value, False)
        else:
            # symb je promenna
            frame, name = self.parse_arg_variable_frame_and_name(arg_value)
            frame_to_search = self.get_frame(frame)
            if frame_to_search == 'NEDEFINOVAN':
                printMessageAndExit(55, "ERROR: FRAME NOT DEFINIED")
            elif name not in frame_to_search:
                printMessageAndExit(54, "ERROR: VARIABLE NOT DEFINIED, WRITING TO UNDEFINIED VARIABLE")
            else:
                type = frame_to_search[name]['type']
                value = frame_to_search[name]['value']
                return (type, value, True) # True protoze je v promenne

    def isVarDefined(self, argValue):
        frame, name = self.parse_arg_variable_frame_and_name(argValue)
        frame_to_search = self.get_frame(frame)
        if frame_to_search == 'NEDEFINOVAN':
            printMessageAndExit(55, "ERROR: FRAME NOT DEFINIED")
        elif name not in frame_to_search:
            return False
        else:
            return True


    def set_var(self, i_arg_variable, type, value):
        """Vlozi novou hodnotu do promenne i_arg_variable"""
        frame, name = self.parse_arg_variable_frame_and_name(i_arg_variable)
        frame_to_search = self.get_frame(frame)
        if frame_to_search == 'NEDEFINOVAN':
            printMessageAndExit(55, "ERROR: FRAME NOT DEFINIED, WRITING TO UNDEFINIED FRAME")

        elif name not in frame_to_search:
            printMessageAndExit(54, "ERROR: VARIABLE NOT DEFINIED, WRITING TO UNDEFINIED VARIABLE")

        else:
            # promenna existuje, muzeme do ni zapsat hodnotu
            frame_to_search[name]['type'] = type
            frame_to_search[name]['value'] = value



    # INSTRUKCE

    # DEFVAR
    def defvar(self, i_arg):
        frame, name = self.parse_arg_variable_frame_and_name(i_arg)
        frame_to_insert = self.get_frame(frame)
        if frame_to_insert == 'NEDEFINOVAN':
            # nedefinovany ramec
            printMessageAndExit(55, "ERROR: FRAME NOT DEFINIED")

        else:
            # ramec existuje
            if name in frame_to_insert:
                # promenna jiz existuje
                printMessageAndExit(58, "ERROR: TRYING TO DECLARE ALREADY EXISTING VARIABLE")                
            else:
                # promenna neexistuje, muzeme ji vlozit
                frame_to_insert[name] = {'value': None, 'type': None}
