"""
Defines a set of helper functions that make constructing hardware easier.

The set of functions includes
as_wires: converts consts to wires if needed (and does nothing to wires)
and_all_bits, or_all_bits, xor_all_bits: apply function across all bits
parity: same as xor_all_bits
mux: generate a multiplexer
concat: concatenate multiple wirevectors into one long vector
get_block: get the block of the arguments, throw error if they are different
appropriate_register_type: return the register needed to capture the given type
"""

from block import *
from wirevector import *


#-----------------------------------------------------------------
#        ___       __   ___  __   __
#  |__| |__  |    |__) |__  |__) /__`
#  |  | |___ |___ |    |___ |  \ .__/
#
def as_wires(val, block=None):
    """ Return wires from val which may be wires or int. """
    block = working_block(block)

    if isinstance(val, (int, basestring)):
        return Const(val, block=block)
    elif not isinstance(val, WireVector):
        raise PyrtlError('error, expecting a wirevector, int, or verilog-style const string')
    else:
        return val


def and_all_bits(vector):
    return _apply_op_over_all_bits('__and__', vector)


def or_all_bits(vector):
    return _apply_op_over_all_bits('__or__', vector)


def xor_all_bits(vector):
    return _apply_op_over_all_bits('__xor__', vector)


def parity(vector):
    return _apply_op_over_all_bits('__xor__', vector)


def _apply_op_over_all_bits(op, vector):
    if len(vector) == 1:
        return vector
    else:
        rest = _apply_op_over_all_bits(op, vector[1:])
        func = getattr(vector[0], op)
        return func(vector[0], rest)


def mux(select, falsecase, truecase):
    """ Multiplexer returning falsecase for select==0, otherwise truecase.

    To avoid confusion it is recommended that you use "falsecase" and "truecase"
    as named arguments because the ordering is different from the classic ternary
    operator of some languages
    """

    block = get_block(select, falsecase, truecase)
    select = as_wires(select, block=block)
    a = as_wires(falsecase, block=block)
    b = as_wires(truecase, block=block)

    if len(select) != 1:
        raise PyrtlError('error, select input to the mux must be 1-bit wirevector')
    if len(a) < len(b):
        a = a.extended(len(b))
    elif len(b) < len(a):
        b = b.extended(len(a))
    resultlen = len(a)  # both are the same length now

    outwire = WireVector(bitwidth=resultlen, block=block)
    net = LogicNet(
        op='x',
        op_param=None,
        args=(select, a, b),
        dests=(outwire,))
    outwire.block.add_net(net)
    return outwire


def get_block(*arglist):
    """ Take any number of wire vector params and return the block they are all in.

    If any of the arguments come from different blocks, throw an error.
    If none of the arguments are wirevectors, return the working_block.
    """
    block = None
    for arg in arglist:
        if isinstance(arg, WireVector):
            if block and block is not arg.block:
                raise PyrtlError('get_block passed WireVectors from differnt blocks')
            else:
                block = arg.block
    # use working block is block is still None
    block = working_block(block)
    return block


def concat(*args):
    """ Take any number of wire vector params and return a wire vector concatinating them."""

    block = get_block(*args)
    if len(args) <= 0:
        raise PyrtlError
    if len(args) == 1:
        return args[0]
    else:
        final_width = sum([len(arg) for arg in args])
        outwire = WireVector(bitwidth=final_width, block=block)
        net = LogicNet(
            op='c',
            op_param=None,
            args=tuple(args),
            dests=(outwire,))
        outwire.block.add_net(net)
        return outwire


def appropriate_register_type(t):
    """ take a type t, return a type which is appropriate for registering t (signed or unsigned)."""

    if isinstance(t, (Output, Const)):
        raise PyrtlError  # includes signed versions
    elif isinstance(t, (SignedWireVector, SignedInput, SignedRegister)):
        return SignedRegister
    elif isinstance(t, (WireVector, Input, Register)):
        return Register
    else:
        raise PyrtlError