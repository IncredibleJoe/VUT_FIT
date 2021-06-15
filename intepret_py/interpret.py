#author: Dušan Čičmiš
#school login: xcicmi00
#IPP project2 - interpreter of the code, based on XML input

import re
import argparse
import sys
import xml.etree.ElementTree as ET
from os import path

def Main():

    class dataStack():
        def __init__(self):
            self.stack = []

        def pushValue(self, type, value):
            #Insert the value to the top of the stack
            self.stack.append((type, value))

        def popValue(self):
            #If data stack is not empty, pop value from the stack
            if len(self.stack) > 0:
                return self.stack.pop()
            else:
                printMessageAndExit(56, "ERROR: NO VALUES IN STACK")

        def getStack(self):
            #Returns the content of the data stack (BREAK)
            return self.stack


    class argument:
        def __init__(self, type = "", value = ""):
            self.type = type
            self.value = value


    class instruction:
        def __init__(self, order = "", opcode = ""):
            self.order = order
            self.opcode = opcode
            self.arguments = []

        def addArgument(self, argument):
            self.arguments.append(argument)


    class frame():
        def __init__(self):
            #stack of frames
            self.frame_stack = []
            #temporary frame, if not definied => undefined
            self.undefined = True
            self.tmp_frame = {}
            #global frame
            self.global_frame = {}

        #init temporary frame => define frame
        def createTF(self):
            self.undefined = False
            self.tmp_frame = {}

        #push temporary frame to frame stack
        def pushTFtoFrameStack(self):
            #if TF is definied, we can move it to frame stack
            if self.undefined != True:
                self.frame_stack.append(self.tmp_frame)
            else:
                printMessageAndExit(55, "ERROR: TEMPORARY FRAME NOT DEFINIED")
            #after pushing to stack, frame becomes undefinied
            self.undefined = True

        #pop temporary frame from frame stack to temporary frame
        def popFrameStacktoTF(self):
            #frame stack contains at least one frame
            if len(self.frame_stack) > 0:
                self.tmp_frame = self.frame_stack.pop()
                self.undefined = False
            else:
                printMessageAndExit(55, "ERROR: EMPTY FRAME STACK")

        def getFrameStack(self):
            return self.frame_stack


        def getFrame(self, frame):
            if frame == "GF":
                return self.global_frame

            elif frame == "LF":
                #LF is always first element of frame stack, if frame stack contains at least one frame we can return it
                if len(self.frame_stack) > 0:
                    return self.frame_stack[len(self.frame_stack) - 1]
                else:
                    return "UNDEFINIED"

            elif frame == "TF":
                if self.undefined == True:
                    return "UNDEFINIED"
                else:
                    return self.tmp_frame

        #returns frame and name of the variable
        def getVarFrameAndName(self, variable):
            return variable.split('@', 1)

        #returns type, value of argument and tells whether argument is variable or constant
        def getTypeAndValue(self, arg_type, arg_value):                                     #arg_type = var, arg_value = GF@value
            if arg_type in ["string", "int", "bool", "nil", "type", "label"]:
                #False = constant
                return (arg_type, arg_value, False)

            else:
                frame, name = self.getVarFrameAndName(arg_value)
                reqFrame = self.getFrame(frame)

                if reqFrame == "UNDEFINIED":
                    printMessageAndExit(55, "ERROR: FRAME NOT DEFINIED")

                elif name not in reqFrame:
                    printMessageAndExit(54, "ERROR: VARIABLE NOT DEFINIED, WRITING TO UNDEFINIED VARIABLE")

                else:
                    type = reqFrame[name]["type"]
                    value = reqFrame[name]["value"]
                    #True = variable
                    return (type, value, True)

        #tells whether the varibale is definied or not
        def isVarDefined(self, argValue):
            frame, name = self.getVarFrameAndName(argValue)
            reqFrame = self.getFrame(frame)
            if reqFrame == "UNDEFINIED":
                printMessageAndExit(55, "ERROR: FRAME NOT DEFINIED")
            elif name not in reqFrame:
                return False
            else:
                return True

        #in case variable and frame in which variable is, is definied, set the value of variable, otherwise exit
        def setVariable(self, variable, type, value):
            frame, name = self.getVarFrameAndName(variable)
            reqFrame = self.getFrame(frame)

            if reqFrame == "UNDEFINIED":
                printMessageAndExit(55, "ERROR: FRAME NOT DEFINIED, WRITING TO UNDEFINIED FRAME")

            elif name not in reqFrame:
                printMessageAndExit(54, "ERROR: VARIABLE NOT DEFINIED, WRITING TO UNDEFINIED VARIABLE")

            else:
                reqFrame[name]['type'] = type
                reqFrame[name]['value'] = value

        #DEFVAR
        def defvar(self, argument):
            frame, name = self.getVarFrameAndName(argument)
            reqFrame = self.getFrame(frame)

            #if frame is definied
            if reqFrame == "UNDEFINIED":
                printMessageAndExit(55, "ERROR: FRAME NOT DEFINIED")

            #frame is not definied
            else:
                #trying to access already definied variable in the same frame
                if name in reqFrame:
                    printMessageAndExit(58, "ERROR: TRYING TO DECLARE ALREADY EXISTING VARIABLE")

                #frame is defnied and in the same frame, there is no variable with the same name => insert variable to frame
                else:
                    reqFrame[name] = {'value': None, 'type': None}


    #checks instruction argument, in case of correct number of arguments and type of arguments, does nothing, otherwise exits the program
    def checkInstructionArguments(instruction):
        #no operands (BREAK|RETURN|CREATEFRAME|PUSHFRAME|POPFRAME)
        if re.match("^(BREAK|RETURN|CREATEFRAME|PUSHFRAME|POPFRAME)$", instruction["opcode"]):
            if len(instruction["arguments"]) == 0:
                pass
            else:
                printMessageAndExit(32, "ERROR: INVALID NUMBER OF ARGUMENTS")

        #"var" (DEFVAR|POPS)
        if re.match("^(DEFVAR|POPS)$", instruction["opcode"]):
            if len(instruction["arguments"]) == 2:
                if instruction["arguments"][0] == "var":
                    pass
                else:
                    printMessageAndExit(53, "ERROR: INVALID TYPE OF ARGUMENTS")

            else:
                printMessageAndExit(32, "ERROR: INVALID NUMBER OF ARGUMENTS")

        #"label" (CALL|LABEL|JUMP)
        if re.match("^(CALL|LABEL|JUMP)$", instruction["opcode"]):
            if len(instruction["arguments"]) == 2:
                if instruction["arguments"][0] == "label":
                    pass
                else:
                    printMessageAndExit(53, "ERROR: INVALID TYPE OF ARGUMENTS")
            else:
                printMessageAndExit(32, "ERROR: INVALID NUMBER OF ARGUMENTS")

        #"symb" (PUSHS|WRITE|DPRINT|EXIT)
        if re.match("^(PUSHS|WRITE|DPRINT|EXIT)$", instruction["opcode"]):
            if len(instruction["arguments"]) == 2:
                if instruction["arguments"][0] in types and instruction["arguments"][0] != "label":
                    pass
                else:
                    printMessageAndExit(53, "ERROR: INVALID TYPE OF ARGUMENTS")
            else:
                printMessageAndExit(32, "ERROR: INVALID NUMBER OF ARGUMENTS")

        #"var", "type" (READ)
        if instruction["opcode"] == "^READ$":
            if len(instruction["arguments"]) == 4:
                if instruction["arguments"][0] == "var" and re.match("^int|string|bool$", instruction["arguments"][2]):
                    pass
                else:
                    printMessageAndExit(53, "ERROR: INVALID TYPE OF ARGUMENTS")
            else:
                printMessageAndExit(32, "ERROR: INVALID NUMBER OF ARGUMENTS")

        #"var", "symb" (MOVE|TYPE|INT2CHAR|STRLEN|NOT)
        if re.match("^(MOVE|TYPE|INT2CHAR|STRLEN|NOT)$", instruction["opcode"]):
            if len(instruction["arguments"]) == 4:
                if instruction["arguments"][0] == "var" and (instruction["arguments"][2] in types and instruction["arguments"][2] != "label"):
                    pass
                else:
                    printMessageAndExit(53, "ERROR: INVALID TYPE OF ARGUMENTS")
            else:
                printMessageAndExit(32, "ERROR: INVALID NUMBER OF ARGUMENTS")

        #"var", "symb1", "symb2" (ADD|SUB|MUL|IDIV|LT|GT|EQ|AND|OR|STRI2INT|CONCAT|GETCHAR|SETCHAR)
        if re.match("^(ADD|SUB|MUL|IDIV|LT|GT|EQ|AND|OR|STRI2INT|CONCAT|GETCHAR|SETCHAR)$", instruction["opcode"]):
            if len(instruction["arguments"]) == 6:
                if instruction["arguments"][0] == "var" and (instruction["arguments"][2] in types and instruction["arguments"][2] != "label") and (instruction["arguments"][4] in types and instruction["arguments"][4] != "label"):
                    pass
                else:
                    printMessageAndExit(53, "ERROR: INVALID TYPE OF ARGUMENTS")
            else:
                printMessageAndExit(32, "ERROR: INVALID NUMBER OF ARGUMENTS")

        #"label", "symb1", "symb2" (JUMPIFEQ|JUMPIFNEQ)
        if re.match("^(JUMPIFEQ|JUMPIFNEQ)$", instruction["opcode"]):
            if len(instruction["arguments"]) == 6:
                if instruction["arguments"][0] == "label" and (instruction["arguments"][2] in types and instruction["arguments"][2] != "label") and (instruction["arguments"][4] in types and instruction["arguments"][4] != "label"):
                    pass
                else:
                    printMessageAndExit(53, "ERROR: INVALID TYPE OF ARGUMENTS")
            else:
                printMessageAndExit(32, "ERROR: INVALID NUMBER OF ARGUMENTS")

    #checks argument values, in case of correct value, does nothing, otherwise exits the program
    def checkArgumentValue(argument):
        if argument.type == "type":
            if re.match("^(int|string|bool)$", argument.value):
                pass
            else:
                printMessageAndExit(32, "ERROR: INVALID VALUE OF ARGUMENTS")

        if argument.type == "bool":
            if re.match("^(TRUE|FALSE|true|false)$", argument.value):
                pass
            else:
                printMessageAndExit(32, "ERROR: INVALID VALUE OF ARGUMENTS")

        if argument.type == "int":
            if re.match("^(\+|-)?[0-9]+$", argument.value):
                pass
            else:
                printMessageAndExit(32, "ERROR: INVALID VALUE OF ARGUMENTS")

        if argument.type == "label":
            if re.match("^[a-zA-Z0-9_\-$&%*!?]+$", argument.value):
                pass
            else:
                printMessageAndExit(32, "ERROR: INVALID VALUE OF ARGUMENTS")

        if argument.type == "nil":
            if re.match("^nil$", argument.value):
                pass
            else:
                printMessageAndExit(32, "ERROR: INVALID VALUE OF ARGUMENTS")

        if argument.type == "string":
            if re.match("^([^\\\\]*(\\\\[0-9]{3})?[^\\\\]*)*$", str(argument.value)):
                #find all escape sequences
                listOfEscSeq = re.findall("\\\\[0-9]{3}", argument.value)
                for escape_sequence in listOfEscSeq:
                        argument.value = argument.value.replace(escape_sequence, chr(int(escape_sequence[1:])))
            else:
                printMessageAndExit(32, "ERROR: INVALID VALUE OF ARGUMENTS")

        if argument.type == "var":
            if re.match("^(GF|LF|TF)@([a-zA-Z_\-$&%*!?]+[a-zA-Z0-9_\-$&%*!?]*)$", argument.value):
                pass
            else:
                printMessageAndExit(32, "ERROR: INVALID VALUE OF ARGUMENTS")


    #parse command line arguments, returns the name of files, or by default, source of information is standard input
    def parseClArguments():
        parser = argparse.ArgumentParser(description = 'Interpret the code based on XML input.')
        parser.add_argument('--source', nargs=1, help = "XML source file", default=sys.stdin)
        parser.add_argument('--input', nargs=1, help = "input file for READ instruction", default=sys.stdin)

        args = parser.parse_args()
        inputFile = ""
        sourceFile = ""

        #if multiple files are given with one --source argument, take just first one
        if isinstance(args.source, list):
            sourceFile = args.source[0]

        #if multiple files are given with one --input argument, take just first one
        if isinstance(args.input, list):
            inputFile = args.input[0]

        return sourceFile, inputFile

    def printMessageAndExit(code, message):
        print(message, file=sys.stderr)
        sys.exit(code)


    #parse command line argumets and store the file names or path to files
    sourceFile, inputFile = parseClArguments()

    #possible types of variables
    types = ["bool", "int", "label", "nil", "string", "var", "type"]

    #xml load
    try:
        xmlTree = ET.parse(sourceFile)
        root = xmlTree.getroot()
        rootKey = root.attrib.keys()
    except:
        print("ERROR: LOADING XML FILE FAIL", file=sys.stderr)
        sys.exit(31)

    #xml check
    if "language" not in rootKey:
        printMessageAndExit(32, "XML ERROR: XML DOES NOT CONTAIN \"LANGUAGE\" ATTRIBUTE")

    if root.tag != "program":
        printMessageAndExit(32, "XML ERROR: XML DOES NOT CONTAIN \"PROGRAM\" ATTRIBUTE")

    if root.attrib["language"].upper() != "IPPCODE21":
        printMessageAndExit(32, "XML ERROR: XML DOES NOT CONTAIN CORRECT NAME OF LANGUAGE ATTRIBUTE")

    #list of valid instructions
    instructions = ["MOVE", "CREATEFRAME", "PUSHFRAME", "POPFRAME", "DEFVAR", "CALL", "RETURN", "PUSHS", "POPS", "ADD", "SUB", "MUL", "IDIV", "LT", "GT", "EQ", "AND", "OR", "NOT", "INT2CHAR", "STR2INT", "READ", "WRITE", "CONCAT", "STRLEN", "GETCHAR", "SETCHAR", "TYPE", "LABEL", "JUMP", "JUMPIFEQ", "JUMPIFNEQ", "EXIT", "DPRINT", "BREAK"]

    #this array is used for advanced xml tree parsing and will be used for interpreting the code, it contains instructions, with order, opcode, arguments and value of these arguments, eg:
    #{'order': 4, 'opcode': 'JUMPIFEQ', 'arguments': ['label', 'end', 'var', 'GF@counter', 'string', 'aaa']}
    instructionArray = []

    #parse xml input
    for child in root:
        try:
            #check if the xml has valid attributes, if so does nothing, otherwise exits
            if child.tag == "instruction" and list(child.attrib.keys())[0] == "order" and list(child.attrib.keys())[1] == "opcode":
                pass
            else:
                printMessageAndExit(32, "XML ERROR: XML DOES NOT CONTAIN CORRECT NAME OF LANGUAGE ATTRIBUTE")
        except:
            #this error occures if there are no attribute keys
            printMessageAndExit(32, "XML ERROR: NO ATTRIBUTE KEYS")

        #check if the order given is integer and if instruction name is valid
        if re.match("^[0-9]*$", child.attrib["order"]) and child.attrib["opcode"].upper() in instructions:
            #create new instansce of class instruction
            currInstruction = instruction()
            #convert order to int and add order and opcode to instruction
            currInstruction.order = int(child.attrib["order"])
            currInstruction.opcode = child.attrib["opcode"].upper()

        else:
            printMessageAndExit(32, "XML ERROR: ORDER OR OPCODE INVALID")

        #these variables are used for checking of arguments and sorting by order
        ArgListToOrder = {}
        argNum = 0
        argOrders = []

        for arg in child:
            argNum += 1
            #there is more than 3 arguments given to instruction
            if argNum > 3:
                printMessageAndExit(32, "ERROR: INVALID NUMBER OF ARGUMENTS")
            try:
                #check if the xml has valid attributes
                if not re.match("^(arg[1-3])$", arg.tag):
                    printMessageAndExit(32, "XML ERROR: NO ARG[1-3] ATTRIBUTE DETECTED")

                if 'type' not in arg.attrib:
                    printMessageAndExit(32, "XML ERROR: NO \"TYPE\" ATTRIBUTE DETECTED")

                if arg.attrib['type'] not in types:
                    printMessageAndExit(32, "XML ERROR: INVALID \"TYPE\" ATTRIBUTE DETECTED")
            except:
                printMessageAndExit(32, "UNEXPECTED XML ERROR")

            #create instance of class argument and assign values to it
            argtest = argument()
            argtest.type = arg.attrib["type"]
            argtest.value = arg.text

            #check if the argument is valid
            checkArgumentValue(argtest)

            #arg.tag should contain arg[1-3] and should not repeat
            if arg.tag in argOrders:
                printMessageAndExit(32, "XML ERROR: ARGUMENTS WITH SAME ORDER NUMBER")
            else:
                argOrders.append(arg.tag)

            ArgListToOrder[arg.tag] = argtest.__dict__

        #sort arguments by order and add types and values to instruction instance
        if "arg1" not in argOrders and len(argOrders) > 0:
            printMessageAndExit(32, "XML ERROR: INVALID ARGUMENT ORDER NUMBER")

        for i in sorted (ArgListToOrder):
            currInstruction.addArgument(ArgListToOrder[i]["type"])
            currInstruction.addArgument(ArgListToOrder[i]["value"])

        #check if the instruction has correct arguements and if so, add the instruction with arguments into array
        checkInstructionArguments(currInstruction.__dict__)
        instructionArray.append(currInstruction.__dict__)


    #sort the instructions by order
    instructionArray = sorted(instructionArray, key=lambda dct: dct['order'])
    number_of_instructions = len(instructionArray)

    #list to store labels
    labels = {}

    #used for sorting the instructions by correct order
    orders = []
    #check if each instruction has different order and if so, check if order goes one by one
    for instruction in instructionArray:
        order = instruction["order"]
        if order in orders:
            printMessageAndExit(32, "XML ERROR: DUPLICIT ORDER OF INSTRUCTIONS")
        else:
            if order > 0:
                orders.append(order)
            else:
                printMessageAndExit(32, "XML ERROR: ORDER \"0\"")

    #used for custom order
    orderer = 1
    #custom order => converts the order of instruction into instrucion with order numbers starting from 1 and incrementing by one
    for instruction in instructionArray:
        instruction["order"] = orderer
        orderer += 1

    for instruction in instructionArray:
        if instruction["opcode"] == "LABEL":
            if instruction["arguments"][1] not in labels:
                labels[instruction["arguments"][1]] = instruction["order"]
            else:
                printMessageAndExit(52, "ERROR: 2 LABELS WITH SAME NAME")


    '''
    ##############################INTERPRET#################################
    '''


    #auxiliary variable for READ instruction
    readLinesCounter = 0

    #initialize frame
    frame = frame()

    #is used to interpret correct instruction at the time
    inst_counter = 0

    #call stack, used by functions CALL and RETURN
    call_stack = []

    #counter of performed INSTRUCTIONS
    performedInstructions = 0

    #data Stack
    data_Stack = dataStack()


    while inst_counter < number_of_instructions:
        #set the instruction to interpret
        instruction = instructionArray[inst_counter]
        #instruction form: {'order': 4, 'opcode': 'JUMPIFEQ', 'arguments': ['label', 'end', 'var', 'GF@counter', 'string', 'aaa']}

        if instruction["opcode"] == "PUSHS":
            #instruction["arguments"][0] = type of arument, instruction["arguments"][1] = value of argument
            data_Stack.pushValue(instruction["arguments"][0], instruction["arguments"][1])

        elif instruction["opcode"] == "POPS":
            type, value = data_Stack.popValue()
            frame.setVariable(instruction["arguments"][1], type, value)

        elif instruction["opcode"] == "CREATEFRAME":
            frame.createTF()

        elif instruction["opcode"] == "PUSHFRAME":
            frame.pushTFtoFrameStack()

        elif instruction["opcode"] == "POPFRAME":
            frame.popFrameStacktoTF()

        elif instruction["opcode"] == "CALL":
            #store the incremented position of instruction counter to call stack
            call_stack.append(instruction["order"] + 1)
            #set the instruction counter (instruction reader)
            try:
                inst_counter = labels[instruction["arguments"][1]]
            except:
                printMessageAndExit(52, "INTERPRET ERROR: LABEL DOES NOT EXIST")
            performedInstructions += 1
            continue

        elif instruction["opcode"] == "DEFVAR":
            frame.defvar(instruction["arguments"][1])

        elif instruction["opcode"] == "RETURN":
            #if there was more then one CALL instruction used before calling RETURN instruction
            if len(call_stack) > 0:
                #set the instruction counter (instruction reader)
                inst_counter = call_stack.pop(0)
                performedInstructions += 1
                continue
            else:
                printMessageAndExit(56, "INTERPRET ERROR: CALL STACK IS EMPTY")

        #instruction form: {'order': 4, 'opcode': 'JUMPIFEQ', 'arguments': ['label', 'end', 'var', 'GF@counter', 'string', 'aaa']}

        elif instruction["opcode"] == "MOVE":
            type, value, var_or_const = frame.getTypeAndValue(instruction["arguments"][2], instruction["arguments"][3])
            frame.setVariable(instruction["arguments"][1], type, value)

        elif re.match("^(ADD|SUB|MUL|IDIV)$", instruction["opcode"]):
            type1, value1, var_or_const1 = frame.getTypeAndValue(instruction["arguments"][2], instruction["arguments"][3])
            type2, value2, var_or_const2 = frame.getTypeAndValue(instruction["arguments"][4], instruction["arguments"][5])

            #both types of arguments must be the same type
            if type1 == "int" and type2 == "int":
                if frame.isVarDefined(instruction["arguments"][1]):

                    if instruction["opcode"] == "MUL":
                        frame.setVariable(instruction["arguments"][1], "int", int(value1) * int(value2))

                    if instruction["opcode"] == "SUB":
                        frame.setVariable(instruction["arguments"][1], "int", int(value1) - int(value2))

                    if instruction["opcode"] == "ADD":
                        frame.setVariable(instruction["arguments"][1], "int", int(value1) + int(value2))

                    if instruction["opcode"] == "IDIV":
                        if (int(value2) == 0):
                            printMessageAndExit(57, "DIVIDING BY ZERO")
                        frame.setVariable(instruction["arguments"][1], "int", int(value1) // int(value2))

            else:
                printMessageAndExit(53, "INTERPRET ERROR: INVALID TYPE OF ARGUMENTS")


        elif re.match("^(LT|GT|EQ)$", instruction["opcode"]):
            type1, value1, var_or_const1 = frame.getTypeAndValue(instruction["arguments"][2], instruction["arguments"][3])
            type2, value2, var_or_const2 = frame.getTypeAndValue(instruction["arguments"][4], instruction["arguments"][5])

            #types are the same and the type is not "nil"
            if type1 == type2 and type1 != "nil":
                if type1 == "int":
                    value1 = int(value1)
                    value2 = int(value2)

                    #check if variable is definied
                    if frame.isVarDefined(instruction["arguments"][1]):

                        if instruction["opcode"] == "LT" and type1 != "nil" and type2 != "nil":
                            if value1 <= value2:
                                result = "true"
                            else:
                                result = "false"
                            frame.setVariable(instruction["arguments"][1], "bool", result)

                        if instruction["opcode"] == "GT" and type1 != "nil" and type2 != "nil":
                            if value1 >= value2:
                                result = "true"
                            else:
                                result = "false"
                            frame.setVariable(instruction["arguments"][1], "bool", result)

                        if instruction["opcode"] == "EQ":
                            if value1 == value2:
                                result = "true"
                            else:
                                result = "false"
                            frame.setVariable(instruction["arguments"][1], "bool", result)

            elif (type1 == "nil" or type2 == "nil") and instruction["opcode"] == "EQ":
                if type1 == type2:
                    result = "true"
                else:
                    result = "false"
                frame.setVariable(instruction["arguments"][1], "bool", result)

        #instruction form: {'order': 4, 'opcode': 'JUMPIFEQ', 'arguments': ['label', 'end', 'var', 'GF@counter', 'string', 'aaa']}

        elif re.match("^(AND|OR)$", instruction["opcode"]):
            type1, value1, var_or_const1 = frame.getTypeAndValue(instruction["arguments"][2], instruction["arguments"][3])
            type2, value2, var_or_const2 = frame.getTypeAndValue(instruction["arguments"][4], instruction["arguments"][5])

            if type1 == type2 == "bool":
                if frame.isVarDefined(instruction["arguments"][1]):

                    if instruction["opcode"] == "AND":
                        result = value1 and value2
                        frame.setVariable(instruction["arguments"][1], "bool", result)

                    if instruction["opcode"] == "OR":
                        result = value1 or value2
                        frame.setVariable(instruction["arguments"][1], "bool", result)

        elif instruction["opcode"] == "NOT":
            type, value, var_or_const = frame.getTypeAndValue(instruction["arguments"][2], instruction["arguments"][3])

            if type == "bool":
                if str(value.lower()) == "true" :
                    frame.setVariable(instruction["arguments"][1], "bool", "false")
                if str(value.lower()) == "false":
                    frame.setVariable(instruction["arguments"][1], "bool", "true")

        elif instruction["opcode"] == "INT2CHAR":
            type1, value1, var_or_const1 = frame.getTypeAndValue(instruction["arguments"][2], instruction["arguments"][3])
            if type1 == "int":
                type2, value2, var_or_const2 = frame.getTypeAndValue(instruction["arguments"][0], instruction["arguments"][1])
                result = chr(int(value1))
                frame.setVariable(instruction["arguments"][1], "string", result)

            else:
                printMessageAndExit(53, "INTERPRET ERROR: INVALID TYPE OF ARGUMENTS")

        #instruction form: {'order': 4, 'opcode': 'JUMPIFEQ', 'arguments': ['label', 'end', 'var', 'GF@counter', 'string', 'aaa']}


        elif instruction["opcode"] == "STR2INT":
            type1, value1, var_or_const1 = frame.getTypeAndValue(instruction["arguments"][2], instruction["arguments"][3])
            type2, value2, var_or_const2 = frame.getTypeAndValue(instruction["arguments"][4], instruction["arguments"][5])

            if type1 == "string" and type2 == "int":
                try:
                    result = ord(value1[int(value2)])
                except:
                    printMessageAndExit(58, "INTERPRET ERROR: STRING INDEX OUT OF RANGE")
                frame.setVariable(instruction["arguments"][1], "int", result)

            else:
                printMessageAndExit(53, "INTERPRET ERROR: INVALID TYPE OF ARGUMENTS")

        elif instruction["opcode"] == "CONCAT":
            type1, value1, var_or_const1 = frame.getTypeAndValue(instruction["arguments"][2], instruction["arguments"][3])
            type2, value2, var_or_const2 = frame.getTypeAndValue(instruction["arguments"][4], instruction["arguments"][5])

            if type1 == "string" and type2 == "string":
                #result = value1 + value2
                frame.setVariable(instruction["arguments"][1], "string", value1 + value2)
            else:
                printMessageAndExit(53, "INTERPRET ERROR: INVALID TYPE OF ARGUMENTS")

        elif instruction["opcode"] == "STRLEN":
            type1, value1, var_or_const1 = frame.getTypeAndValue(instruction["arguments"][2], instruction["arguments"][3])

            if type1 == "string":
                frame.setVariable(instruction["arguments"][1], "int", len(value1))

            else:
                printMessageAndExit(53, "INTERPRET ERROR: INVALID TYPE OF ARGUMENTS")

        elif instruction["opcode"] == "GETCHAR":
            type1, value1, var_or_const1 = frame.getTypeAndValue(instruction["arguments"][2], instruction["arguments"][3])
            type2, value2, var_or_const2 = frame.getTypeAndValue(instruction["arguments"][4], instruction["arguments"][5])

            if type1 == "string" and type2 == "int":
                try:
                    result = value1[int(value2)]
                except:
                    printMessageAndExit(58, "INTERPRET ERROR: STRING INDEX OUT OF RANGE")
                frame.setVariable(instruction["arguments"][1], "int", result)

            else:
                printMessageAndExit(53, "INTERPRET ERROR: INVALID TYPE OF ARGUMENTS")

        elif instruction["opcode"] == "SETCHAR":
            type1, value1, var_or_const1 = frame.getTypeAndValue(instruction["arguments"][0], instruction["arguments"][1])
            type2, value2, var_or_const2 = frame.getTypeAndValue(instruction["arguments"][2], instruction["arguments"][3])
            type3, value3, var_or_const3 = frame.getTypeAndValue(instruction["arguments"][4], instruction["arguments"][5])

            if type1 == "string" and type2 == "int" and type3 == "string":
                stringToChange = list(value1)
                stringToSet = list(value3)
                try:
                    charToSet = stringToSet[0]
                except:
                    printMessageAndExit(58, "INTERPRET ERROR: EMPTY STRING GIVEN AS ARGUMENT IN FUNCTION SETCHAR")
                try:
                    stringToChange[int(value2)] = charToSet
                except:
                    printMessageAndExit(58, "INTERPRET ERROR: STRING INDEX OUT OF RANGE")
                result = str(stringToChange)
                frame.setVariable(instruction["arguments"][1], "string", result)

            else:
                printMessageAndExit(53, "INTERPRET ERROR: INVALID TYPE OF ARGUMENTS")

        elif instruction["opcode"] == "TYPE":
            #get argument type and value of second argument (<symb>)
            type, value, var_or_const = frame.getTypeAndValue(instruction["arguments"][2], instruction["arguments"][3])

            #argument is variable
            if var_or_const:
                #variable is not definied or has no type or value
                if not frame.isVarDefined(instruction["arguments"][3]) or str(type) == "None":
                    frame.setVariable(instruction["arguments"][1], "string", "")
                else:
                    if type in ["string", "int", "bool", "nil"]:
                        print("kokot", instruction)
                        frame.setVariable(instruction["arguments"][1], "string", type)
                    else:
                        printMessageAndExit(53, "INTERPRET ERROR: INVALID TYPE OF ARGUMENTS")

            #argument is constant
            else:
                if type in ["string", "int", "bool", "nil"]:
                    frame.setVariable(instruction["arguments"][1], "string", type)
                else:
                    printMessageAndExit(53, "INTERPRET ERROR: INVALID TYPE OF ARGUMENTS")

        elif instruction["opcode"] == "LABEL":
            inst_counter += 1
            continue

        elif instruction["opcode"] == "JUMP":
            try:
                inst_counter = labels[instruction["arguments"][1]]
            except:
                printMessageAndExit(52, "INTERPRET ERROR: LABEL DOES NOT EXIST")
            performedInstructions += 1
            continue

        elif re.match("^(JUMPIFEQ|JUMPIFNEQ)$", instruction["opcode"]):
            type1, value1, var_or_const1 = frame.getTypeAndValue(instruction["arguments"][2], instruction["arguments"][3])
            type2, value2, var_or_const2 = frame.getTypeAndValue(instruction["arguments"][4], instruction["arguments"][5])

            if instruction["opcode"] == "JUMPIFEQ":
                #types are equal
                if type1 == type2:
                    if type1 == "int":
                        if int(value1) == int(value2):
                            try:
                                inst_counter = labels[instruction["arguments"][1]]
                            except:
                                printMessageAndExit(52, "INTERPRET ERROR: LABEL DOES NOT EXIST")
                            performedInstructions += 1
                            continue

                    #type is not int, we can compare values as strings
                    else:
                        if value1 == value2:
                            try:
                                inst_counter = labels[instruction["arguments"][1]]
                            except:
                                printMessageAndExit(52, "INTERPRET ERROR: LABEL DOES NOT EXIST")
                            performedInstructions += 1
                            continue

                #types or arguments are not equal
                else:
                    printMessageAndExit(53, "INTERPRET ERROR: INVALID TYPE OF ARGUMENTS")

            if instruction["opcode"] == "JUMPIFNEQ":
                #types are equal
                if type1 == type2:
                    if type1 == "int":
                        if int(value1) != int(value2):
                            try:
                                inst_counter = labels[instruction["arguments"][1]]
                            except:
                                printMessageAndExit(52, "INTERPRET ERROR: LABEL DOES NOT EXIST")
                            performedInstructions += 1
                            continue

                    #type is not int, we can compare values as strings
                    else:
                        if value1 != value2:
                            try:
                                inst_counter = labels[instruction["arguments"][1]]
                            except:
                                printMessageAndExit(52, "INTERPRET ERROR: LABEL DOES NOT EXIST")
                            performedInstructions += 1
                            continue

                #types are not equal and of them is type nil
                elif type1 == "nil" or type2 == "nil":
                    try:
                        inst_counter = labels[instruction["arguments"][1]]
                    except:
                        printMessageAndExit(52, "INTERPRET ERROR: LABEL DOES NOT EXIST")
                    performedInstructions += 1
                    continue

                else:
                    printMessageAndExit(53, "INTERPRET ERROR: INVALID TYPE OF ARGUMENTS")


        elif instruction["opcode"] == "EXIT":
            type, value, var_or_const = frame.getTypeAndValue(instruction["arguments"][0], instruction["arguments"][1])

            if type == "int":
                if 0 <= int(value) <= 49:
                    sys.exit(int(value))
                else:
                    printMessageAndExit(57, "INTERPRET ERROR: INVALID VALUE OF ARGUMENT (EXIT)")

            else:
                printMessageAndExit(53, "INTERPRET ERROR: INVALID TYPE OF ARGUMENTS")

        elif instruction["opcode"] == "DPRINT":
            type, value, var_or_const = frame.getTypeAndValue(instruction["arguments"][0], instruction["arguments"][1])
            print(str(value), file=sys.stderr)

        elif instruction["opcode"] == "BREAK":
            print("Position in code:", str(inst_counter),file=sys.stderr)
            print("Number of performed instuctions: ", str(performedInstructions), file=sys.stderr)
            print("Content of global frame: ", str(frame.getFrame("GF")), file=sys.stderr)
            print("Content of local frame: ", str(frame.getFrame("LF")), file=sys.stderr)
            print("Content of temporary frame: ", str(frame.getFrame("TF")), file=sys.stderr)
            print("Content of frame stack: ", str(frame.getFrameStack()), file=sys.stderr)

        elif instruction["opcode"] == "WRITE":
            type, value, var_or_const = frame.getTypeAndValue(instruction["arguments"][0], instruction["arguments"][1])

            if type == "nil":
                print("", end='')

            elif type == "bool":
                print(value, end='')

            else:
                print(value, end='')

        elif instruction["opcode"] == "READ":

            type = instruction["arguments"][3]

            if re.match("^(int|string|bool)$", type):
                #input method is file
                if path.isfile(inputFile):
                    file = open(inputFile, "r")
                    lines = file.readlines()

                    x = lines[readLinesCounter]

                    if type == "int":
                        try:
                            int(x)
                        except:
                            type = "nil"
                            x = "nil"

                        frame.setVariable(instruction["arguments"][1], type, x)

                    if type == "string":
                        if re.match("^([^\\\\]*(\\\\[0-9]{3})?[^\\\\]*)*$", x):
                            frame.setVariable(instruction["arguments"][1], type, x)
                        else:
                            frame.setVariable(instruction["arguments"][1], "nil", "nil")

                    if type == "bool":
                        if re.match("^true*$", x.lower()):
                            frame.setVariable(instruction["arguments"][1], type, x)
                        elif re.match("^([^\\\\]*(\\\\[0-9]{3})?[^\\\\]*)*$", x):
                            frame.setVariable(instruction["arguments"][1], type, "false")
                        else:
                            frame.setVariable(instruction["arguments"][1], "nil", "nil")

                    readLinesCounter += 1


                #input method is stdin
                else:
                    x = input()
                    if type == "int":
                        try:
                            int(x)
                        except:
                            type = "nil"
                            x = "nil"

                        frame.setVariable(instruction["arguments"][1], type, x)

                    if type == "string":
                        if re.match("^([^\\\\]*(\\\\[0-9]{3})?[^\\\\]*)*$", x):
                            frame.setVariable(instruction["arguments"][1], type, x)
                        else:
                            frame.setVariable(instruction["arguments"][1], "nil", "nil")

                    if type == "bool":
                        x = x.lower()
                        if re.match("^true*$", x.lower()):
                            frame.setVariable(instruction["arguments"][1], type, x)
                        elif re.match("^([^\\\\]*(\\\\[0-9]{3})?[^\\\\]*)*$", x):
                            frame.setVariable(instruction["arguments"][1], type, "false")
                        else:
                            frame.setVariable(instruction["arguments"][1], "nil", "nil")
            else:
                frame.setVariable(instruction["arguments"][1], "nil", "nil")


        inst_counter += 1
        performedInstructions += 1

if __name__ == '__main__':
    Main()
