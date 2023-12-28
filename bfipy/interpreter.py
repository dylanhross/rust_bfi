"""
    bfipy/interpreter.py

    Brainfart interpreter object and associated enums
"""


from enum import Enum, auto
from typing import Optional


class Command(Enum):
    MovePointerRight = auto()
    MovePointerLeft = auto()
    IncrementByte = auto()
    DecrementByte = auto()
    OutputByte = auto()
    InputByte = auto()
    JumpRightIfZero = auto()
    JumpLeftIfNonZero = auto()


class BFI:
    """ 
    Brainfart interpreter object

    *all attributes read only unless specified otherwise*
    
    Attributes
    ----------
    mem_sz : ``int``:
        size of memory array (bytes)
    mem : ``bytearray``
        memory of the machine model, an array of bytes
    ptr : ``int``
        data pointer, indexes into memory
    in_buf : ``bytearray``
        input buffer, an array of bytes (read/write)
    out_buf : ``bytearray``
        output buffer, an array of bytes
    flg_run : ``bool``
        status flag: interpreter is running
    flg_trm : ``bool``
        status flag: interpreter has terminated (either end of program or error)
    flg_err : ``bool``
        status flag: iterpreter has encountered an error
    err_msg : ``str``
        error message (if interpreter encountered an error)
    in_buf_idx : ``int``
        index into the input buffer (for error reporting/debugging)
    """

    def __init__(self, 
                 mem_sz: int = 4096
                 ) -> None:
        """
        Init a new BF interpreter instance

        Parameters
        ----------
        mem_sz : ``int``, default=4096
            size of memory array (bytes)
        """
        self.__mem_sz = mem_sz  # R
        # initialize memory array (filled w/ zeros)
        self.__mem = bytearray(self.__mem_sz)  # R
        # data pointer starts at index 0
        self.__ptr = 0  # R
        # input and output buffers start empty
        self.in_buf = bytearray()  # RW
        self.__out_buf = bytearray()  # R
        # set initial status flag states
        self.__flg_run = False  # R
        self.__flg_trm = False  # R
        self.__flg_err = False  # R
        self.__err_msg = ""  # R
        # keep track of index into input buffer for error reporting
        self.__in_buf_idx = 0
        # counter for open/closed parens
        # open increments, closed decrements
        # used for detecting unbalanced [ ]
        self.__paren_state = 0
        # stack for storing input buffer bytes for jumps
        self.__jump_stack = bytearray()

    @property
    def mem_sz(self
               ) -> int:
        return self.__mem_sz    

    @property
    def mem(self
            ) -> bytearray:
        return self.__mem

    @property
    def ptr(self
            ) -> int:
        return self.__ptr
    
    @property
    def ptr_val(self
                ) -> int:
        return self.__mem[self.__ptr]
    
    @property
    def out_buf(self
                ) -> bytearray:
        return self.__out_buf
    
    @property
    def flg_run(self
                ) -> bool:
        return self.__flg_run
    
    @property
    def flg_trm(self
                ) -> bool:
        return self.__flg_trm
    
    @property
    def flg_err(self
                ) -> bool:
        return self.__flg_err
    
    @property
    def err_msg(self
                ) -> str:
        return self.__err_msg
    
    @property
    def in_buf_idx(self
                   ) -> int:
        return self.__in_buf_idx
    
    def _parse_command(self, 
                       byte: int) -> Optional[Command]:
        """
        parse a byte into a Command, if unable to parse return None

        Parameters
        ----------
        byte : ``int``
            a byte
        
        Returns
        -------
        command : ``Command`` or ``None``
            parsed command or None if unable to parse
        """
        match  byte:
            case 43:
                return Command.IncrementByte
            case 44:
                return Command.InputByte
            case 45:
                return Command.DecrementByte
            case 46:
                return Command.OutputByte
            case 60:
                return Command.MovePointerLeft
            case 62:
                return Command.MovePointerRight
            case 91:
                return Command.JumpRightIfZero
            case 93:
                return Command.JumpLeftIfNonZero
            case _:
                return None

    def run(self
            ) -> None:
        """
        Run the interpreter, consume the input buffer one byte at a time
        then parse and run the command
        """
        # set running flag while interpreter is running
        self.__flg_run = True
        # consume 1 byte at a time from input buffer
        # ignore any bytes that are not recognized commands
        while len(self.in_buf) > 0:
            byte = self.in_buf.pop(0)
            match self._parse_command(byte):
                case Command.MovePointerRight:
                    self.__ptr += 1
                    # make sure we have not overrun available memory
                    if self.__ptr >= self.mem_sz:
                        # set the error flag and message
                        self.__flg_err = True
                        self.__err_msg = "data pointer overran memory size"
                        break
                case Command.MovePointerLeft:
                    self.__ptr -= 1
                    # make sure we have not underrun available memory
                    if self.__ptr < 0:
                        # set the error flag and message
                        self.__flg_err = True
                        self.__err_msg = "data pointer underran memory size"
                        break
                case Command.IncrementByte:
                    match self.ptr_val:
                        case 255:
                            # rollover
                            self.__mem[self.__ptr] = 0
                        case _:
                            self.__mem[self.__ptr] += 1
                case Command.DecrementByte:
                    match self.ptr_val:
                        case 0:
                            # rollover (rollunder?)
                            self.__mem[self.__ptr] = 255
                        case _:
                            self.__mem[self.__ptr] -= 1
                case Command.OutputByte:
                    # copy the byte at the pointer position directly
                    # into the output buffer
                    self.__out_buf.append(self.ptr_val)
                case Command.InputByte:
                    raise NotImplementedError("have not implemented inputting a byte yet, where does it come from?")
                case Command.JumpRightIfZero:
                    # increment paren state
                    self.__paren_state += 1
                    # do the conditional jump
                    if not self.ptr_val:
                        # jump right
                        # push input buffer bytes into a stack until a closing ] is found
                        if len(self.in_buf) == 0:
                            # make sure there are still bytes in the input buffer
                            self.__flg_err = True
                            self.__err_msg = "no bytes in input buffer after ["
                            break
                        self.__jump_stack.insert(0, byte)
                        next_byte = self.in_buf.pop(0)
                        while next_byte != 93 and len(self.in_buf) > 0:
                            self.__jump_stack.insert(0, next_byte)
                            next_byte = self.in_buf.pop(0)
                        # check that closing paren has been found
                        if next_byte != 93:
                            self.__flg_err = True
                            self.__err_msg = "no closing ] found"
                            break
                        # if the closing ] was found, push it back to the front of the input
                        # buffer before continuing with execution
                        self.in_buf.insert(0, next_byte)
                case Command.JumpLeftIfNonZero:
                    # check if open/close paren state makes sense
                    if self.__paren_state < 1:
                        # set the error flag and message
                        self.__flg_err = True
                        self.__err_msg = "unmatched ]"
                        break
                    # decrement paren state
                    self.__paren_state -= 1
                    # do conditional jump
                    if self.ptr_val:
                        # jump left
                        # pop bytes from stack until the opening [ and push them back into front of input buffer
                        # push the ] into input buffer first
                        self.in_buf.insert(0, byte)
                        next_byte = self.__jump_stack.pop(0)
                        while next_byte != 91:
                            self.in_buf.insert(0, next_byte)
                            next_byte = self.__jump_stack.pop(0)
                        # push the opening [ into input buffer before continuing with execution
                        self.in_buf.insert(0, next_byte)
            self.__in_buf_idx += 1
        # check the paren state at the end of execution, set error flag if not 0
        # but do not overwrite an existing error
        if not self.__flg_err and self.__paren_state != 0:
            self.__flg_err = True
            self.__err_msg = "unbalanced [ ] (paren state: {:+d})".format(self.__paren_state)
        # after executing reset run flag and set terminated flag
        # to signal execution has completed
        self.__flg_run = False
        self.__flg_trm = True


    
