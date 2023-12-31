/*
    module where basic datatypes are defined
*/


#[derive(Debug)]
pub enum Command {
    MovePointerRight,
    MovePointerLeft,
    IncrementByte,
    DecrementByte,
    OutputByte,
    InputByte,
    JumpRightIfZero,
    JumpLeftIfNonZero,
}
