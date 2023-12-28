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
    JumpLeftIfZero = auto()


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
        # used for detecting malformed jumps
        self.__open_parens = 0
        self.__closed_parens = 0

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
                return Command.JumpLeftIfZero
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
                    current_val = self.__mem[self.__ptr]
                    match self.__mem[self.__ptr]:
                        case 255:
                            # rollover
                            self.__mem[self.__ptr] = 0
                        case _:
                            self.__mem[self.__ptr] += 1
                case Command.DecrementByte:
                    current_val = self.__mem[self.__ptr]
                    match self.__mem[self.__ptr]:
                        case 0:
                            # rollover (rollunder?)
                            self.__mem[self.__ptr] = 255
                        case _:
                            self.__mem[self.__ptr] -= 1
                case Command.OutputByte:
                    # copy the byte at the pointer position directly
                    # into the output buffer
                    self.__out_buf.append(self.__mem[self.__ptr])
                case Command.InputByte:
                    raise NotImplementedError("have not implemented inputting a byte yet, where does it come from?")
            self.__in_buf_idx += 1
        # after executing reset run flag and set terminated flag
        # to signal execution has completed
        self.__flg_run = False
        self.__flg_trm = True


    
