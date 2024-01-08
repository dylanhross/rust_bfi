/*
    toy brainfart interpreter
*/


mod dtypes;
mod parsing;
mod interpreter;


fn main() {
    let mut bfi = interpreter::BFInterpreter::new(8);
    bfi.run();
}
