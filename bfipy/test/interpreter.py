"""
    bfipy/test/interpreter.py

    unit tests for bfipy/interpreter.py module
"""


from unittest import TestCase, main as utmain


from bfipy.interpreter import BFI, Command


class TestBFI(TestCase):

    def test_parse_command(self):
        """ test BFI._parse_command method """
        # expected output
        bfi = BFI()
        for i in range(256):
            bfi.in_buf.append(i)
        for b in bfi.in_buf:
            match b.to_bytes():
                case b'>': 
                    self.assertEqual(bfi._parse_command(b), Command.MovePointerRight,
                                     msg="{} should map to Command.MovePointerRight".format(b))
                case b'<': 
                    self.assertEqual(bfi._parse_command(b), Command.MovePointerLeft,
                                     msg="{} should map to Command.DecrementByte".format(b))
                case b'+': 
                    self.assertEqual(bfi._parse_command(b), Command.IncrementByte,
                                     msg="{} should map to Command.IncrementByte".format(b))
                case b'-': 
                    self.assertEqual(bfi._parse_command(b), Command.DecrementByte,
                                     msg="{} should map to Command.DecrementByte".format(b))
                case b'.': 
                    self.assertEqual(bfi._parse_command(b), Command.OutputByte,
                                     msg="{} should map to Command.OutputByte".format(b))
                case b',': 
                    self.assertEqual(bfi._parse_command(b), Command.InputByte,
                                     msg="{} should map to Command.InputByte".format(b))
                case b'[': 
                    self.assertEqual(bfi._parse_command(b), Command.JumpRightIfZero,
                                     msg="{} should map to Command.JumpRightIfZero".format(b))
                case b']': 
                    self.assertEqual(bfi._parse_command(b), Command.JumpLeftIfZero,
                                     msg="{} should map to Command.JumpLeftIfZero".format(b))  
                case _:
                    self.assertIsNone(bfi._parse_command(b),
                                      msg="{} should map to None".format(b))   
    
    def test_run_move_ptr_right(self):
        """ test the BFI.run method with '>', should move the data pointer right """
        bfi = BFI(mem_sz=3)
        bfi.in_buf = bytearray(b'>')
        # data pointer is 0 before run()
        self.assertEqual(bfi.ptr, 0,
                         "data pointer should be 0 before run()")
        bfi.run()
        # make sure correct flags are set after running
        self.assertFalse(bfi.flg_run,
                         msg="run flag should be False")
        self.assertTrue(bfi.flg_trm,
                        msg="terminated flag should be True")
        self.assertFalse(bfi.flg_err,
                         msg="error flag should be False")
        # data pointer is 1 after run()
        self.assertEqual(bfi.ptr, 1,
                         "data pointer should be 1 after run()")
        
    def test_run_overrun_mem_sz(self):
        """ test the BFI.run method, overrun the memory size """
        bfi = BFI(mem_sz=3)
        bfi.in_buf = bytearray(b'>>>>')
        bfi.run()
        # make sure correct flags are set after running
        self.assertFalse(bfi.flg_run,
                         msg="run flag should be False")
        self.assertTrue(bfi.flg_trm,
                        msg="terminated flag should be True")
        self.assertTrue(bfi.flg_err,
                        msg="error flag should be True")
        self.assertEqual(bfi.err_msg, "data pointer overran memory size", 
                         msg="should have gotten memory overrun error message")
        
    def test_run_move_ptr_left(self):
        """ test the BFI.run method with '<', should move the data pointer left """
        bfi = BFI(mem_sz=3)
        bfi.in_buf = bytearray(b'><')
        # data pointer is 0 before run()
        self.assertEqual(bfi.ptr, 0,
                         "data pointer should be 0 before run()")
        bfi.run()
        # make sure correct flags are set after running
        self.assertFalse(bfi.flg_run,
                         msg="run flag should be False")
        self.assertTrue(bfi.flg_trm,
                        msg="terminated flag should be True")
        self.assertFalse(bfi.flg_err,
                         msg="error flag should be False")
        # data pointer is 0 after run()
        self.assertEqual(bfi.ptr, 0,
                         "data pointer should be 0 after run()")
    
    def test_run_underrun_mem_sz(self):
        """ test the BFI.run method, underrun the memory size """
        bfi = BFI(mem_sz=3)
        bfi.in_buf = bytearray(b'<')
        bfi.run()
        # make sure correct flags are set after running
        self.assertFalse(bfi.flg_run,
                         msg="run flag should be False")
        self.assertTrue(bfi.flg_trm,
                        msg="terminated flag should be True")
        self.assertTrue(bfi.flg_err,
                        msg="error flag should be True")
        self.assertEqual(bfi.err_msg, "data pointer underran memory size", 
                         msg="should have gotten memory underrun error message")
    
    def test_run_increment_byte(self):
        """ test the BFI.run() method with '+', should increment byte with rollover """
        increments = [
            # (number of increments, expected byte 0 value)
            (0, 0),
            (1, 1),
            (255, 255),
            (256, 0),
        ]
        for n_inc, exp_val in increments:
            bfi = BFI(mem_sz=3)
            bfi.in_buf = bytearray([int.from_bytes(b'+') for _ in range(n_inc)])
            bfi.run()
            self.assertEqual(bfi.mem[0], exp_val,
                             msg="after {} increments byte should have value {} (had: {})".format(n_inc, exp_val, bfi.mem[0]))

    def test_run_decrement_byte(self):
        """ test the BFI.run() method with '-', should decrement byte with rollover """
        increments = [
            # (number of decrements, expected byte 0 value)
            (0, 1),
            (1, 0),
            (2, 255),
            (3, 254),
        ]
        for n_inc, exp_val in increments:
            bfi = BFI(mem_sz=3)
            bfi.in_buf = bytearray([int.from_bytes(b'+')] + [int.from_bytes(b'-') for _ in range(n_inc)])
            bfi.run()
            self.assertEqual(bfi.mem[0], exp_val,
                             msg="after {} decrements byte should have value {} (had: {})".format(n_inc, exp_val, bfi.mem[0]))

    def test_run_output_byte(self):
        """ test the BFI.run() method with '.', should add expected values to output buffer """
        progs_and_outs = [
                # (program, expected output byte)
                (b'.', 0),
                (b'+.', 1),
                (b'+++++.', 5),
                (b'-.', 255),
                (b'++----.', 254),
            ]
        for prog, exp_out_byte in progs_and_outs:
            bfi = BFI(mem_sz=3)
            bfi.in_buf = bytearray(prog)
            bfi.run()
            self.assertEqual(len(bfi.out_buf), 1,
                             msg="after run() output buffer should have length 1")
            self.assertEqual(bfi.out_buf[0], exp_out_byte,
                            msg="prog: {} should produce output {} (was: {})".format(prog, exp_out_byte, bfi.out_buf[0]))

    def test_run_input_byte(self):
        """ test the BFI.run() method with ',', should raise an error since it is not implemented yet """

        with self.assertRaises(NotImplementedError, 
                               msg="should have gotten a NotImplementedError for InputByte command"):
            bfi = BFI(mem_sz=3)
            bfi.in_buf = bytearray(b',')
            bfi.run()


# run all tests in this module if invoked directly
if __name__ == "__main__":
    utmain(verbosity=2)

