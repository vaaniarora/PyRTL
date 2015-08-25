"""
Defines MemBlock, a block of memory that can be read (async) and written (sync)
"""

import collections
import core
import wire
import helperfuncs
import conditional


# ------------------------------------------------------------------------
#
#         ___        __   __          __        __   __
#   |\/| |__   |\/| /  \ |__) \ /    |__) |    /  \ /  ` |__/
#   |  | |___  |  | \__/ |  \  |     |__) |___ \__/ \__, |  \
#


# MemBlock supports any number of the following operations:
# read: d = mem[address]
# write: mem[address] = d
# write with an enable: mem[address] = MemBlock.EnabledWrite(d,enable=we)
# Based on the number of reads and writes a memory will be inferred
# with the correct number of ports to support that

# _MemAssignment is the type returned from assignment by |= or <<=
_MemAssignment = collections.namedtuple('_MemAssignment', 'rhs, is_conditional')


class _MemIndexed(wire.WireVector):
    """ Object used internally to route memory assigns correctly.

    The normal PyRTL user should never need to be aware that this class exists,
    hence the underscore in the name.  It presents a very similar interface to
    wiresVectors (all of the normal wirevector operations should still work),
    but if you try to *set* the value with <<= or |= then it will generate a
    _MemAssignment object rather than the normal wire assignment. """

    def __init__(self, mem, index):
        self.mem = mem
        self.index = index

    def __ilshift__(self, other):
        return _MemAssignment(rhs=other, is_conditional=False)

    def __ior__(self, other):
        return _MemAssignment(rhs=other, is_conditional=True)

    def logicop(self, other, op):
        return helperfuncs.as_wires(self).logicop(other, op)

    def __invert__(self):
        return helperfuncs.as_wires(self).__invert__()

    def __getitem__(self, item):
        return helperfuncs.as_wires(self).__getitem__(item)

    def __len__(self):
        return self.mem.bitwidth

    def sign_extended(self, bitwidth):
        return helperfuncs.as_wires(self).sign_extended(bitwidth)

    def zero_extended(self, bitwidth):
        return helperfuncs.as_wires(self).zero_extended(bitwidth)


class _MemReadBase(object):
    """This is the base class for the memories and ROM blocks and
    it implements the read and initialization operations needed for
    both of them"""

    # FIXME: right now read port is built unconditionally (no read enable)

    def __init__(self,  bitwidth, addrwidth, name=None, onlysync=False, block=None):

        self.block = core.working_block(block)
        name = core.next_tempvar_name(name)

        if bitwidth <= 0:
            raise core.PyrtlError('bitwidth must be >= 1')
        if addrwidth <= 0:
            raise core.PyrtlError('addrwidth must be >= 1')

        self.bitwidth = bitwidth
        self.name = name
        self.addrwidth = addrwidth
        self.readport_nets = []
        self.id = core.next_memid()
        self.onlysync = onlysync

    def __getitem__(self, item):
        from helperfuncs import as_wires

        # Check if memories marked as "sync" are only addressed directly by registers.
        # Note that this can be conservitive because it eliminates registers feeding
        # wirevectors that feed memories, as well as "non computing" transforms such
        # as bit-slice and concat.
        if self.onlysync and not isinstance(item, wire.Register):
            print repr(self.onlysync)
            raise core.PyrtlError('only registers allowed as index to '
                                  'memory with "onlysync" set to True')

        item = as_wires(item, bitwidth=self.addrwidth, truncating=False, block=self.block)
        if len(item) > self.addrwidth:
            raise core.PyrtlError('memory index bitwidth > addrwidth')
        return _MemIndexed(mem=self, index=item)

    def _readaccess(self, addr):
        # FIXME: add conditional read ports
        return self._build_read_port(addr)

    def _build_read_port(self, addr):
        data = wire.WireVector(bitwidth=self.bitwidth, block=self.block)
        readport_net = core.LogicNet(
            op='m',
            op_param=(self.id, self),
            args=(addr,),
            dests=(data,))
        self.block.add_net(readport_net)
        self.readport_nets.append(readport_net)
        return data

    def __setitem__(self, key, value):
        raise core.PyrtlInternalError("error, invalid call __setitem__ made on _MemReadBase")

    def _make_copy(self, block):
        pass


class MemBlock(_MemReadBase):
    """ An object for specifying read and write enabled block memories """
    # FIXME: write ports assume that only one port is under control of the conditional

    EnabledWrite = collections.namedtuple('EnabledWrite', 'data, enable')
    """ Allows for an enable bit for each write port

    Usage:
    mem[address] = MemBlock.EnabledWrite(d,enable=we)

    When the address of a memory is assigned to using a EnableWrite object
    items will only be written to the memory when the enable WireVector is
    set to high (1)
    """

    # data <<= memory[addr]  (infer read port)
    # memory[addr] <<= data  (infer write port)
    def __init__(self, bitwidth, addrwidth, name=None, onlysync=False, block=None):
        """ Create MemBlock.

        :param int bitwidth: Defines the bitwidth of each element in the memory
        :param int addrwidth: The number of bits used to address an element of the
         memory. This also defines the size of the memory
        :param bool onlysync: if true check that it is only addressed by registers
        :param basestring or None name: Name of the memory. Defaults to an autogenerated
         name
        :param block: the block to add it to. Defaults to the working block
        """
        super(MemBlock, self).__init__(bitwidth, addrwidth, name, onlysync, block)
        self.writeport_nets = []

    def __setitem__(self, item, assignment):
        if isinstance(assignment, _MemAssignment):
            self._assignment(item, assignment.rhs, is_conditional=assignment.is_conditional)
        else:
            raise core.PyrtlError('error, assigment to memories should use "<<=" not "=" operator')

    def _assignment(self, item, val, is_conditional):
        from helperfuncs import as_wires

        # Check for register-only addresses when onlysync is true
        if self.onlysync and not isinstance(item, wire.Register):
            raise core.PyrtlError('only registers allowed as index to '
                                  'memory with "onlysync" set to True')

        item = as_wires(item, bitwidth=self.addrwidth, truncating=False, block=self.block)
        if len(item) > self.addrwidth:
            raise core.PyrtlError('error, memory index bitwidth > addrwidth')
        addr = item

        if isinstance(val, MemBlock.EnabledWrite):
            data, enable = val.data, val.enable
        else:
            data, enable = val, wire.Const(1, bitwidth=1, block=self.block)
        data = as_wires(data, bitwidth=self.bitwidth, truncating=False, block=self.block)
        enable = as_wires(enable, bitwidth=1, truncating=False, block=self.block)

        if len(data) != self.bitwidth:
            raise core.PyrtlError('error, write data larger than memory  bitwidth')
        if len(enable) != 1:
            raise core.PyrtlError('error, enable signal not exactly 1 bit')

        if is_conditional:
            conditional.ConditionalUpdate._build_write_port(self, addr, data, enable)
        else:
            self._build_write_port(addr, data, enable)

    def _build_write_port(self, addr, data, enable):
        writeport_net = core.LogicNet(
            op='@',
            op_param=(self.id, self),
            args=(addr, data, enable),
            dests=tuple())
        self.block.add_net(writeport_net)
        self.writeport_nets.append(writeport_net)

    def _make_copy(self, block=None):
        if block is None:
            block = self.block
        return MemBlock(self.bitwidth, self.addrwidth, self.name, block)


class RomBlock(_MemReadBase):
    """ PyRTL Read Only Memory.

    RomBlocks are the read only memory format in PyRTL
    By default, they synthesize down to transistor-based
    logic during synthesis
    """
    def __init__(self, bitwidth, addrwidth, romdata, name=None, onlysync=False, block=None):
        """ Create a RomBlock
        :param int bitwidth: The bitwidth of each item stored in the ROM
        :param int addrwidth: The bitwidth of the address bus (determines number of addresses)
        :param function or iterable romdata: This can either be a function or an array that maps
          an address as an input to a result as an output
        """
        super(RomBlock, self).__init__(bitwidth, addrwidth, name, onlysync, block)
        self.initialdata = romdata

    def _get_read_data(self, address):
        import types
        if address < 0 or address > 2**self.addrwidth - 1:
            raise core.PyrtlError("Error: Invalid address, " + str(address) + " specified")
        if isinstance(self.initialdata, types.FunctionType):
            try:
                value = self.initialdata(address)
            except Exception:
                raise core.PyrtlError("Invalid data function for RomBlock")
        else:
            try:
                value = self.initialdata[address]
            except TypeError:
                raise core.PyrtlError("invalid type for RomBlock data object")
            except IndexError:
                raise core.PyrtlError("An access to rom " + self.name +
                                      " index " + str(address) + " is out of range")

        if value < 0 or value >= 2**self.bitwidth:
            raise core.PyrtlError("invalid value for RomBlock data")

        return value

    def _make_copy(self, block=None):
        if block is None:
            block = self.block
        return RomBlock(self.bitwidth, self.addrwidth, self.initialdata, self.name, block,)
