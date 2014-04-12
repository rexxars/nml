__license__ = """
NML is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

NML is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with NML; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA."""

"""
Abstract base classes that implements common functionality for output classes
"""
import StringIO

class OutputBase(object):
    """
    Base class for output to a data file.

    The file is opened with L{open}. Once that is done, data can be written
    using the L{file} data member. When finished writing, the file should be
    closed with L{close}.

    Derived classes should implement L{open_file} to perform the actual opening
    of the file. L{pre_close} is called to warn them of pending closure of the
    file.

    @ivar filename: Name of the data file.
    @type filename: C{str}

    @ivar file: Memory output file handle, if opened.
    @type file: C{file} or C{None}
    """
    def __init__(self, filename):
        self.filename = filename
        self.file = None

    def open(self):
        """
        Open the output file. Data gets stored in-memory.
        """
        self.file = StringIO.StringIO()

    def open_file(self):
        """
        Construct the file handle of the disk output file.

        @return: File handle of the opened file.
        @rtype: C{file}
        """
        raise NotImplementedError("Implement me in %s" % type(self))


    def pre_close(self):
        """
        File is about to be closed, last chance to append data.
        """
        pass

    def close(self):
        """
        Close the memory file, copy collected output to the real file.
        """
        self.pre_close()

        real_file = self.open_file()
        real_file.write(self.file.getvalue())
        real_file.close()
        self.file.close()

    def skip_sprite_checks(self):
        """
        Return whether sprites need detailed parsing.
        """
        return False

class BinaryOutputBase(OutputBase):
    """
    Base class for output to a binary data file.

    @ivar in_sprite: Set to true if we are currently outputting a sprite.
                        Outputting anything when not in a sprite causes an assert.
    @type in_sprite: C{bool}

    @ivar byte_count: Number of bytes written in the current sprite.
    @type byte_count: C{int}

    @ivar expected_count: Number of bytes expected in the current sprite.
    @type expected_count: C{int}
    """
    def __init__(self, filename):
        OutputBase.__init__(self, filename)
        self.in_sprite = False
        self.expected_count = 0
        self.byte_count = 0

    def pre_close(self):
        assert not self.in_sprite

    def prepare_byte(self, value):
        """
        Normalize the provided value to an unsigned byte value.

        @param value: Value to normalize.
        @type  value: C{int}

        @return: Normalized value (0..255).
        @rtype:  C{int}

        @precond: Must be outputting a sprite.
        """
        assert self.in_sprite
        if -0x80 <= value < 0 : value += 0x100
        assert value >= 0 and value <= 0xFF
        self.byte_count += 1
        return value

    def prepare_word(self, value):
        """
        Normalize the provided value to an unsigned word value.

        @param value: Value to normalize.
        @type  value: C{int}

        @return: Normalized value (0..65535).
        @rtype:  C{int}

        @precond: Must be outputting a sprite.
        """
        assert self.in_sprite
        if -0x8000 <= value < 0: value += 0x10000
        assert value >= 0 and value <= 0xFFFF
        self.byte_count += 2
        return value

    def prepare_dword(self, value):
        """
        Normalize the provided value to an unsigned double word value.

        @param value: Value to normalize.
        @type  value: C{int}

        @return: Normalized value (0..0xFFFFFFFF).
        @rtype:  C{int}

        @precond: Must be outputting a sprite.
        """
        assert self.in_sprite
        if -0x80000000 <= value < 0: value += 0x100000000
        assert value >= 0 and value <= 0xFFFFFFFF
        self.byte_count += 4
        return value

    def print_varx(self, value, size):
        """
        Print a variable sized value.

        @param value: Value to output.
        @type  value: C{int}

        @param size: Size of the output (1..4), 3 means extended byte.
        @type  size: C{int}
        """
        if size == 1:
            self.print_bytex(value)
        elif size == 2:
            self.print_wordx(value)
        elif size == 3:
            self.print_bytex(0xFF)
            self.print_wordx(value)
        elif size == 4:
            self.print_dwordx(value)
        else:
            assert False

    def print_bytex(self, byte, pretty_print = None):
        """
        Output an unsigned byte.

        @param byte: Value to output.
        @type  byte: C{int}
        """
        raise NotImplementedError("Implement print_bytex() in %r" % type(self))

    def print_wordx(self, byte):
        """
        Output an unsigned word (2 bytes).

        @param byte: Value to output.
        @type  byte: C{int}
        """
        raise NotImplementedError("Implement print_wordx() in %r" % type(self))

    def print_dwordx(self, byte):
        """
        Output an unsigned double word (4 bytes).

        @param byte: Value to output.
        @type  byte: C{int}
        """
        raise NotImplementedError("Implement print_dwordx() in %r" % type(self))

    def newline(self, msg = "", prefix = "\t"):
        """
        Output a line separator, prefixed with L{prefix}, C{"// "}, and the
        L{msg}, if the latter is not empty.

        @param msg: Optional message to output first.
        @type  msg: C{str}

        @param prefix: Additional white space in front of the comment.
        @type  prefix: C{str}
        """
        raise NotImplementedError("Implement newline() in %r" % type(self))

    def comment(self, msg):
        """
        Output a textual comment at a line by itself.

        @param msg: Comment message.
        @type  msg: C{str}

        @note: Only use if no bytes have been written to the current line.
        """
        raise NotImplementedError("Implement comment() in %r" % type(self))


    def start_sprite(self, expected_size):
        """
        Note to the output stream that a sprite is about to be written.

        @param expected_size: Expected size of the sprite data.
        @type  expected_size: C{int}
        """
        assert not self.in_sprite
        self.in_sprite = True
        self.expected_count = expected_size
        self.byte_count = 0

    def end_sprite(self):
        """
        Note to the output stream that a sprite has been written. The number of
        bytes denoted as expected size with the L{start_sprite} call, should
        have been written.
        """
        assert self.in_sprite
        self.in_sprite = False
        self.newline()
        assert self.expected_count == self.byte_count, "Expected %d bytes to be written to sprite, got %d" % (self.expected_count, self.byte_count)

