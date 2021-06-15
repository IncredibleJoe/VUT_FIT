class DataStack():
    def __init__(self):
        self.stack = []

    def pushValue(self, type, value):
        #Insert the value to the top of the stack
        self.stack.append((type, value))

    def popValue(self):
        if len(self.stack) > 0:
            return self.stack.pop()
        else:
            self.exit(56, "ERROR: NO VALUES IN STACK")

    def get_stack(self):
        #Returns the content of the data stack (BREAK)
        return self.stack
