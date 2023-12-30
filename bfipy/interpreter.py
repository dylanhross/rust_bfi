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
                 mem_sz: int = 4096, debug: bool = False
                 ) -> None:
        """
        Init a new BF interpreter instance

        Parameters
        ----------
        mem_sz : ``int``, default=4096
            size of memory array (bytes)
        debug : ``bool``
            debug flag, print interpreter state before each command
        """
        # store debug flag
        self.__debug = debug
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
        # counter for open/closed brackets
        # open increments, closed decrements
        # used doing jumps and detecting unbalanced [ ]
        self.__bracket_state = 0
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
    
    def _print_state(self
                     ) -> None:
        """ print out the current state of the interpreter for debugging """
        print("-" * 20)
        print("input buffer:", self.in_buf)
        print("output buffer:", self.__out_buf)
        print("memory:", self.__mem)
        print("jump stack:", self.__jump_stack)
        print("data pointer:", self.__ptr)
        print("bracket state:", self.__bracket_state)
        print("run flag:", self.__flg_run)
        print("terminated flag:", self.flg_trm)
        print("error flag:", self.__flg_err)
        print("error message:", self.__err_msg)
        print("-" * 20)
    
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

    def _move_pointer_right(self
                            ) -> None:
        """ handler for Command.MovePointerRight """
        self.__ptr += 1
        # make sure we have not overrun available memory
        if self.__ptr >= self.mem_sz:
            # set the error flag and message
            self.__flg_err = True
            self.__err_msg = "data pointer overran memory size"
        
    def _move_pointer_left(self
                           ) -> None:
        """ handler for Command.MovePointerLeft """
        self.__ptr -= 1
        # make sure we have not underrun available memory
        if self.__ptr < 0:
            # set the error flag and message
            self.__flg_err = True
            self.__err_msg = "data pointer underran memory size"

    def _increment_byte(self
                        ) -> None:
        """ handler for Command.IncrementByte """
        match self.ptr_val:
            case 255:
                # rollover
                self.__mem[self.__ptr] = 0
            case _:
                self.__mem[self.__ptr] += 1

    def _decrement_byte(self
                        ) -> None:
        """ handler for Command.IncrementByte """
        match self.ptr_val:
            case 0:
                # rollover (rollunder?)
                self.__mem[self.__ptr] = 255
            case _:
                self.__mem[self.__ptr] -= 1

    def _output_byte(self
                     ) -> None:
        """ handler for Command.OutputByte """
        # copy the byte at the pointer position directly
        # into the output buffer
        self.__out_buf.append(self.ptr_val)

    def _input_byte(self
                    ) -> None:
        """ handler for Command.InputByte """
        raise NotImplementedError("have not implemented inputting a byte yet, where does it come from?")

    def _jump_right_if_zero(self
                            ) -> None:
        """ handler for Command.JumpRightIfZero """
        # if byte at the current data pointer location is 0
        # skip all commands until a matching closing bracket is reached
        # and push everything (including that closing bracket) onto the jump stack
        pre_bracket_state = self.__bracket_state
        self.__bracket_state += 1
        if not self.ptr_val:
            # jump right
            # push everything onto the jump stack
            while len(self.in_buf) > 0 and self.__bracket_state != pre_bracket_state:
                if self.in_buf[0] == 91:
                    self.__bracket_state += 1
                if self.in_buf[0] == 93:
                    self.__bracket_state -= 1
                self.__jump_stack.insert(0, self.in_buf.pop(0))
            # detect an error condition
            if self.__bracket_state != pre_bracket_state:
                self.__flg_err = True
                self.__err_msg = "could not find matching ]" 

    def _jump_left_if_non_zero(self
                               ) -> None:
        """ handler for Command.JumpLeftIfNonZero """
        # check for unbalanced ]
        if self.__bracket_state == 0:
            self.__flg_err = True
            self.__err_msg = "unmatched ]"
        # if byte at the current data pointer location is not 0
        # jump back to the matching opening bracket [
        # by popping from the jump stack
        pre_bracket_state = self.__bracket_state
        self.__bracket_state -= 1
        if self.ptr_val:
            # TODO: There is something wrong with the pushing/popping
            #       logic here where commands are getting jumbled when
            #       they get moved from the jump stack back to the input
            #       buffer 
            # jump left
            # pop everything (except matching [) off of jump stack
            while self.__bracket_state != pre_bracket_state:
                if self.in_buf[0] == 91:
                    self.__bracket_state += 1
                if self.in_buf[0] == 93:
                    self.__bracket_state -= 1
                self.in_buf.insert(0, self.__jump_stack.pop(0))
            # move the [ back to the jump stack
            self.__jump_stack.insert(0, self.in_buf.pop(0))

    def run(self
            ) -> None:
        """
        Run the interpreter, consume the input buffer one byte at a time
        then parse and run the command 
        (use individual handler methods for each command)
        """
        # set running flag while interpreter is running
        self.__flg_run = True
        # consume 1 byte at a time from input buffer
        # ignore any bytes that are not recognized commands
        # continue while there are still bytes in the input buffer
        # and the error flag has not been set
        while len(self.in_buf) > 0 and  not self.__flg_err:
            if self.__debug:
                self._print_state()
            byte = self.in_buf.pop(0)
            match self._parse_command(byte):
                case Command.MovePointerRight:
                    self._move_pointer_right()
                case Command.MovePointerLeft:
                    self._move_pointer_left()
                case Command.IncrementByte:
                    self._increment_byte()
                case Command.DecrementByte:
                    self._decrement_byte()
                case Command.OutputByte:
                    self._output_byte()
                case Command.InputByte:
                    self._input_byte()
                case Command.JumpRightIfZero:
                    self._jump_right_if_zero()
                case Command.JumpLeftIfNonZero:
                    self._jump_left_if_non_zero()
            # after every loop cycle push the byte that was just processed onto the jump stack
            self.__jump_stack.insert(0, byte)
        # after executing reset run flag and set terminated flag
        # to signal execution has completed
        self.__flg_run = False
        self.__flg_trm = True


    
