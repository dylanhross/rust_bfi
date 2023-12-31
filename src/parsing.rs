/*
    Module with functions for parsing commands
*/


use crate::dtypes;


// convert a byte into corresponding Command variant
pub fn byte_to_command (byte: u8) -> Option<dtypes::Command> {
    // set the mapping between ASCII chars and commands
    match byte {
        // +
        43 => Option::Some(dtypes::Command::IncrementByte),
        // ,
        44 => Option::Some(dtypes::Command::InputByte),
        // -
        45 => Option::Some(dtypes::Command::DecrementByte),
        // .
        46 => Option::Some(dtypes::Command::OutputByte),
        // <
        60 => Option::Some(dtypes::Command::MovePointerLeft),
        // >
        62 => Option::Some(dtypes::Command::MovePointerRight),
        // [
        91 => Option::Some(dtypes::Command::JumpRightIfZero),
        // ]
        93 => Option::Some(dtypes::Command::JumpLeftIfNonZero),
        // None for all other chars
        _ => Option::None
    }
}


#[cfg(test)]
mod tests {

    use super::*;

    #[test]
    fn no_tests_implemented () {
        assert!(false, "no tests implemented");
    }
}
