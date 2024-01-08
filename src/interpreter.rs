/*
    Module with interpreter struct and associated methods
*/


use std::collections::VecDeque;

use crate::{parsing, dtypes};


#[derive(Debug)]
pub struct BFInterpreter {
    mem_size: usize,
    mem: Vec<u8>,
    in_buf: VecDeque<u8>,
    out_buf: Vec<u8>,
    data_ptr: usize,
    run_flg: bool,
    term_flg: bool,
    error_flg: bool,
    error_msg: Option<String>,
    bracket_state: isize,
    jump_stack: Vec<u8>,
    current_byte: Option<u8>,
}


impl BFInterpreter {
    pub fn new (mem_size: usize) -> BFInterpreter {
        let in_buf: VecDeque<u8> = VecDeque::new();
        let out_buf: Vec<u8> = Vec::new();
        let jump_stack: Vec<u8> = Vec::new();
        let bfi = BFInterpreter {
            mem_size,
            mem: vec![0; mem_size],
            in_buf,
            out_buf,
            data_ptr: 0,
            run_flg: false,
            term_flg: false,
            error_flg: false,
            error_msg: Option::None,
            bracket_state: 0,
            jump_stack,
            current_byte: Option::None,
        };
        bfi
    }

    // return value at current data pointer location
    fn ptr_val (&mut self) -> u8 {
        self.mem[self.data_ptr]
    }

    // handler for Command::MovePointerRight
    fn move_pointer_right (&mut self) {
        self.data_ptr += 1;
        // ensure data pointer did not overrun available memory
        if self.data_ptr >= self.mem_size {
            self.error_flg = true;
            self.error_msg = Option::Some(String::from("data pointer overran available memory"));
        }
    }

    // handler for Command::MovePointerLeft
    fn move_pointer_left (&mut self) {
        // ensure data pointer did not underrun available memory
        if self.data_ptr == 0 {
            self.error_flg = true;
            self.error_msg = Option::Some(String::from("data pointer underran available memory"));
        } else {
            self.data_ptr -= 1;
        }
    }

    // handler for Command::IncrementByte
    fn increment_byte (&mut self) {
        // increment byte at data pointer location
        // with rollover
        if self.ptr_val() == 255 {
            self.mem[self.data_ptr] = 0;
        } else {
            self.mem[self.data_ptr] += 1;
        }
    }

    // handler for Command::DecrementByte
    fn decrement_byte (&mut self) {
        // increment byte at data pointer location
        // with rollover
        if self.ptr_val() == 0 {
            self.mem[self.data_ptr] = 255;
        } else {
            self.mem[self.data_ptr] -= 1;
        }
    }

    // handler for Command::OutputByte
    fn output_byte (&mut self) {
        let val = self.ptr_val();
        self.out_buf.push(val);
    }

    // handler for Command::InputByte
    fn input_byte (&mut self) {
       panic!("not implemented");
    }

    // handler for Command::JumpRightIfZero
    fn jump_right_if_zero (&mut self) {
        // if byte at the current data pointer location is 0
        // skip all commands until a matching closing bracket is reached
        // and push everything (including that closing bracket) onto the jump stack
        let pre_bracket_state = self.bracket_state;
        if self.ptr_val() == 0 {
            // jump right
            while self.in_buf.len() > 0 && self.bracket_state != pre_bracket_state {
                if let Some(cmd) = parsing::byte_to_command(self.in_buf[0]) {
                    match cmd {
                        dtypes::Command::JumpRightIfZero => {
                            self.bracket_state += 1;
                        },
                        dtypes::Command::JumpLeftIfNonZero => {
                            self.bracket_state -= 1;
                        },
                        // don't do anything with other commands
                        _ => {},
                    };
                };
                // push whatever byte was there onto the jump stack
                // can unwrap() because already know there are bytes
                // in the input buffer from while loop condition
                self.jump_stack.push(self.in_buf.pop_front().unwrap());
            }
            // detect an error condition
            if self.bracket_state != pre_bracket_state {
                self.error_flg = true;
                self.error_msg = Option::Some(String::from("could not find closing ]"));
            }
        }
    }

    // handler for Command::JumpLeftIfNonZero
    fn jump_left_if_non_zero (&mut self) {
        // check for unbalanced ]
        if self.bracket_state == 0 {
            self.error_flg = true;
            self.error_msg = Option::Some(String::from("unmatched ]"));
        } else {
            // if byte at the current data pointer location is not 0
            // jump back to the matching opening bracket [
            // by popping from the jump stack and inserting at the front 
            // of the input buffer
            let pre_bracket_state = self.bracket_state;
            self.bracket_state -= 1;
            if self.ptr_val() > 0 {
                // jump left
                // put the ] back in the input buffer first
                // can use unwrap here since this should not be reached unless
                // at least 1 byte has been read from input buffer (i.e. self.current_byte
                // cannot be Option::None)
                self.in_buf.push_front(self.current_byte.unwrap());
                while self.bracket_state != pre_bracket_state {
                    // pop everything (except matching [) off of jump stack
                    if let Some(cmd) = parsing::byte_to_command(self.jump_stack[self.jump_stack.len() - 1]) {
                        match cmd {
                            dtypes::Command::JumpRightIfZero => {
                                self.bracket_state += 1;
                            },
                            dtypes::Command::JumpLeftIfNonZero => {
                                self.bracket_state -= 1;
                            },
                            // don't do anything with other commands
                            _ => {},
                        };
                    };
                    self.in_buf.push_front(self.jump_stack.pop().unwrap());
                }
                // put the [ into self.current_byte, it will get pushed back onto the jump stack
                self.current_byte = self.in_buf.pop_front();
            }
        }
    }

    pub fn run (&mut self) {
        // set running flag while interpreter is running
        self.run_flg = true;
        // consume 1 byte at a time from input buffer
        // ignore any bytes that are not recognized commands
        // continue while there are still bytes in the input buffer
        // and the error flag has not been set
        while self.in_buf.len() > 0 && !self.error_flg {
            self.current_byte = self.in_buf.pop_front();
            if let Some(cmd) = parsing::byte_to_command(self.current_byte.unwrap()) {
                match cmd {
                    dtypes::Command::MovePointerRight => self.move_pointer_right(),
                    dtypes::Command::MovePointerLeft => self.move_pointer_left(),
                    dtypes::Command::IncrementByte => self.increment_byte(),
                    dtypes::Command::DecrementByte => self.decrement_byte(),
                    dtypes::Command::OutputByte => self.output_byte(),
                    dtypes::Command::InputByte => self.input_byte(),
                    dtypes::Command::JumpRightIfZero => self.jump_right_if_zero(),
                    dtypes::Command::JumpLeftIfNonZero => self.jump_left_if_non_zero(),
                };
            };
            // after every loop cycle push the byte that was just processed onto the jump stack
            //self.__jump_stack.insert(0, self.__byte)
            self.jump_stack.push(self.current_byte.unwrap());
        }
        // after executing reset run flag and set terminated flag
        // to signal execution has completed
        self.run_flg = false;
        self.term_flg = true;
    }

    pub fn fill_in_buff (&mut self, prog: String) {
        for c in prog.as_bytes() {
            self.in_buf.push_back(*c);
        }
    }

}


#[cfg(test)]
mod tests {

    use super::*;

    #[test]
    fn new_interpreter_no_errors () {
        let bfi = BFInterpreter::new(8);
        println!("\n--------------------");
        println!("bfi: {:?}", bfi);
    }

    #[test]
    fn test_fill_in_buf () {
        // fill input buffer, no errors
        let mut bfi = BFInterpreter::new(8);
        bfi.fill_in_buff(String::from("++++"));
        //println!("\n--------------------");
        //println!("bfi: {:?}", bfi);
    }

    #[test]
    fn interpterter_run_inc_dec () {
        let progs: Vec<(String, u8)> = vec![
            // program, expected value
            (String::from("+++"), 3),
            (String::from("+++---"), 0),
        ];
        for (prog, exp_value) in progs {
            let mut bfi = BFInterpreter::new(8);
            bfi.fill_in_buff(prog);
            //println!("\n--------------------");
            //println!("bfi: {:?}", bfi);
            bfi.run();
            //println!("bfi: {:?}", bfi);
            //println!("expected_value: {}", exp_value);
            assert_eq!(bfi.mem[0], exp_value);
        }
    }

    fn interpreter_run_mv_ptr () {
        let progs: Vec<(String, usize)> = vec![
            // program, expected pointer value
            (String::from("+++>"), 1),
            (String::from("++>+-<--"), 0),
        ];
        for (prog, exp_value) in progs {
            let mut bfi = BFInterpreter::new(8);
            bfi.fill_in_buff(prog);
            //println!("\n--------------------");
            //println!("bfi: {:?}", bfi);
            bfi.run();
            //println!("bfi: {:?}", bfi);
            //println!("expected_value: {}", exp_value);
            assert_eq!(bfi.data_ptr, exp_value);
        }
    }
}
