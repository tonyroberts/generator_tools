import new
import copy
import types
import sys
from opcode import*

__all__ = ["Sharable",
           "GeneratorSnapshot",
           "CodeObj",
           "CopyGeneratorException",
           "copy_generator",
           "IteratorView",
           "for_iter",
           "Generatorcopy", "dbg"]

class any_obj:
    "Used to create objects for spawning arbitrary attributes by assignment"

class Sharable(object):
    sharable = True


class GeneratorSnapshot(object):
    '''
    Object used to hold data for living generators.
    '''
    def __init__(self, f_gen):
        if isinstance(f_gen, Generatorcopy):
            self._template = CodeObj(f_gen._template)
            self._offset   = f_gen._offset
            self._bounds   = f_gen._bounds

        self._uses_envelope = False
        f_code = f_gen.gi_frame.f_code
        self.gi_frame = any_obj()
        self.gi_frame.f_code   = CodeObj(f_code)
        self.gi_frame.f_lasti  = f_gen.gi_frame.f_lasti
        self.gi_frame.f_locals = {}
        self.gi_frame.f_globals = {}
        locals = f_gen.gi_frame.f_locals.items()
        for key, value in locals:
            if isinstance(value, (Generatorcopy, types.GeneratorType)):
                self.gi_frame.f_locals[key] = GeneratorSnapshot(value)
            else:
                if hasattr(value, "__gencopy__"):
                    value.__force__()
                self.gi_frame.f_locals[key] = value


    def is_copy(self):
        return hasattr(self, "_template")

class CodeObj(object):
    def __init__(self, codeobj):
        self.codeobj = codeobj

    def __getstate__(self):
        dct = {}
        dct.update((key, getattr(self.codeobj, key)) for key in dir(self.codeobj) if key.startswith("co_"))
        lst = list(dct["co_consts"])
        for i, c in enumerate(lst):
            if isinstance(c, types.CodeType):
                lst[i] = CodeObj(c)
        dct["co_consts"] = tuple(lst)
        return dct

    def __setstate__(self, dct):
        self.__dict__.update(dct)


class CopyGeneratorException(Exception): pass

if sys.version_info[:2] == (2,4):
    offset_inc = 1
elif sys.version_info[:2] == (2,5):
    offset_inc = 2
elif sys.version_info[:2] == (2,6):
    offset_inc = 2

setupcode = [opmap['SETUP_LOOP'], opmap['SETUP_EXCEPT'], opmap['SETUP_FINALLY']]

jump_op = hasjrel + hasjabs

class DeadIterator:
    def __iter__(self):
        return self

    def next(self, *args):
        raise StopIteration

class _IteratorWrapper(object):
    def __init__(self, it):
        self.recorded = []
        self.it = iter(it)

    def __getstate__(self):
        self.__force__()
        return self.recorded

    def __setstate__(self, lst):
        self.it = DeadIterator()
        self.recorded = lst

    def autowrap(self, item):
        if isinstance(item, types.GeneratorType):
            return generatorwrapper(item)
        else:
            return item

    def __force__(self):
        self.recorded += [self.autowrap(item) for item in list(self.it)]

    def next(self, cursor):
        if cursor.offset<len(self.recorded):
            item = self.recorded[cursor.offset]
            cursor.offset+=1
            return item
        cursor.offset+=1
        item = self.it.next()
        if hasattr(item, "__iter__") and not hasattr(item, "__gencopy__"):
            iw = _IteratorWrapper(item)
            cu = IteratorView(iw)
            self.recorded.append(cu)
            return cu
        elif isinstance(item, types.GeneratorType):
            item = generatorwrapper(item)
        self.recorded.append(item)
        return item


class IteratorView(object):
    '''
    Class used to represent copyable iterators.
    '''
    cloning = False
    def __init__(self, iterwrapper):
        self.offset = 0
        self.itwrap = iterwrapper
        self._bound = None

    def __force__(self):
        self.itwrap.__force__()

    def __gencopy__(self, memo = {}):
        cit = IteratorView(self.itwrap)
        if self.cloning:
            cit.offset = self.offset
        else:
            cit.offset = max(self.offset-1, 0)
        cit.request_bound()
        return cit

    def request_bound(self):
        # print self.itwrap
        # print "recorded", self.itwrap.recorded
        try:
            self._bound = id(self.itwrap.recorded[self.offset])
        except IndexError:
            if self.itwrap.recorded:
                self._bound = id(self.itwrap.recorded[-1])

    __deepcopy__ = __gencopy__

    def __iter__(self):
        return self

    def next(self):
        item = self.itwrap.next(self)
        if hasattr(item, "__gencopy__"):
            return item.__gencopy__()
        _id = id(item)
        return item

    def __repr__(self):
        return "<IteratorView at %s: %s : %s >"%(id(self), self.itwrap, self.offset)

def for_iter(iterable):
    return IteratorView(_IteratorWrapper(iterable))

class Opcode(int):
    def __init__(self, op):
        int.__init__(self, op)
        self.index_l = -1
        self.index_r = -1
        self.id = id(self)
        self.linked_to = None
        self.jump = -1

def compute_offset(offset, opcodes):
    POP     = opmap["POP_TOP"]
    LOAD    = opmap["LOAD_FAST"]
    STORE   = opmap["STORE_FAST"]
    offset +=1
    if opcodes[offset]<50:
        if opcodes[offset] == POP:
            offset += 1
            return offset
        offset+=1
    op = opcodes[offset]
    if op in [LOAD]+jump_op:
        return offset
    STOP = [POP, STORE]
    i = offset
    #print op
    while i<len(opcodes):
        op = opcodes[i]
        if op in STOP:
            if op == STORE:
                return i+3
            else:
                return i+1
        if op>=HAVE_ARGUMENT:
            i+=3
        else:
            i+=1
    return offset


class ByteCodeModifier(object):
    def __init__(self):
        self.statistics = {}
        self.statistics["FOR_ITER"] = []

    def conditional_jump(self, n, setup_offset = 0, anchor = None):
        '''
        0  LOAD_FAST       n (jump_forward_on)
        3  JUMP_IF_FALSE   4
        6  POP_TOP
        7  JUMP_ABSOLUTE   setup_offset
        10 POP_TOP
        '''
        opcode = []
        opcode.extend([opmap["LOAD_FAST"],n,0])
        opcode.extend([opmap["JUMP_IF_FALSE"],4,0])
        opcode.extend([opmap["POP_TOP"]])
        if anchor:
            op = Opcode(opmap["JUMP_ABSOLUTE"])
            op.linked_to = anchor
            opcode.extend([op,0,0])
        else:
            opcode.extend([opmap["JUMP_ABSOLUTE"]]+list(divmod(setup_offset, 256)[::-1]))
        opcode.extend([opmap["POP_TOP"]])
        return [(Opcode(op) if not isinstance(op, Opcode) else op) for op in opcode]


    def conditional_jump_ex(self, n, setup_offset = 0, anchor = None):
        '''
        0  LOAD_FAST       n   (jump_forward_on)
        3  JUMP_IF_FALSE   10
        6  LOAD_FAST       n+1 (jump_forward_off)
        9  STORE_FAST      n
        12 POP_TOP
        13 JUMP_ABSOLUTE   setup_offset
        16 POP_TOP
        '''
        opcode = []
        opcode.extend([opmap["LOAD_FAST"],n,0])
        opcode.extend([opmap["JUMP_IF_FALSE"],10,0])
        opcode.extend([opmap["LOAD_FAST"],n+1,0])
        opcode.extend([opmap["STORE_FAST"],n,0])
        opcode.extend([opmap["POP_TOP"]])
        if anchor:
            op = Opcode(opmap["JUMP_ABSOLUTE"])
            op.linked_to = anchor
            opcode.extend([op,0,0])
        else:
            opcode.extend([opmap["JUMP_ABSOLUTE"]]+list(divmod(setup_offset, 256)[::-1]))
        opcode.extend([opmap["POP_TOP"]])
        return [(Opcode(op) if not isinstance(op, Opcode) else op) for op in opcode]

    def prepare(self, bytecode, offset):
        setup_loc = []
        i = 0
        loc = 0
        while i<len(bytecode):
            op = bytecode[i]
            if op in setupcode:
                jump   = bytecode[i+1] + 256*bytecode[i+2]
                anchor = bytecode[i+jump]
                op.linked_to = anchor
                op.index_l = i
                op.index_r = i
                op.jump = jump
                if i<offset:
                    setup_loc.append(op)
                loc = op
            #elif op == opmap["BUILD_LIST"]:
            #    loc = op
            elif op == opmap["FOR_ITER"]:
                if loc == opmap["SETUP_LOOP"]:
                    op_s = loc
                    op_s.index_r = i+3
                    jump   = bytecode[i+1] + 256*bytecode[i+2]
                    anchor = bytecode[i+jump]
                    op.jump = jump
                    op.linked_to = anchor
                    op.index_l = i
                    op.index_r = i
                    offsets = self.statistics.get("FOR_ITER",[])
                    offsets.append(i)
                    self.statistics["FOR_ITER"] = offsets
            elif op in hasjabs:
                jump   = bytecode[i+1] + 256*bytecode[i+2]
                anchor = bytecode[jump]
                op.linked_to = anchor
                op.index_l = i
                op.index_r = i
            elif op in hasjrel:
                shift = bytecode[i+1]+256*bytecode[i+2]
                anchor = bytecode[i+shift]
                op.linked_to = anchor
                op.index_l = i
                op.index_r = i
            if op>=HAVE_ARGUMENT:
                i+=3
            else:
                i+=1
        return setup_loc

    def initialize_jump_absolute(self, newbytecode, start, jump_target):
        start.linked_to = jump_target
        newbytecode = [(Opcode(x) if not isinstance(x,Opcode) else x) for x in (start,0,0)] + newbytecode
        return newbytecode

    def create_new_bytecode(self, offset, nlocals, bytecode):
        # print "this offset", offset
        setup_loc = self.prepare(bytecode, offset)
        jump_targets = setup_loc+[bytecode[offset]]
        start = Opcode(opmap["JUMP_ABSOLUTE"])
        newbytecode =  []
        i = 0
        initialized = False
        while i<offset:
            op = bytecode[i]
            if op in setupcode:
                for k, item in enumerate(jump_targets):
                    if op.id == item.id:
                        break
                if not initialized:
                    if op.index_l + op.jump < offset:
                        newbytecode.append(op)
                        i+=1
                        continue
                    else:
                        newbytecode = self.initialize_jump_absolute(newbytecode, start, jump_targets[k])
                        initialized = True
                next_target = jump_targets[k+1]
                if k+2 == len(jump_targets):
                    B = self.conditional_jump_ex(nlocals, anchor = next_target)
                else:
                    B = self.conditional_jump(nlocals, anchor = next_target)
                d = op.index_r - op.index_l
                # print op.index_r, op.index_l, d
                newbytecode.extend(bytecode[i:i+d+3])
                newbytecode.extend(B)
                i+=d+3
            else:
                newbytecode.append(op)
                i+=1
        if not initialized:
            newbytecode = self.initialize_jump_absolute(newbytecode, start, jump_targets[0])
        newbytecode.extend(bytecode[offset:])
        self.adjust_offsets(newbytecode)
        return newbytecode

    def adjust_offsets(self, opcodes):
        for i, op in enumerate(opcodes):
            op.index_l = i
        i = 0
        while i<len(opcodes):
            op = opcodes[i]
            anchor = op.linked_to
            if anchor is not None:
                if op in hasjrel:
                    jump = abs(i - anchor.index_l)
                else:
                    jump = anchor.index_l

                low, high = divmod(jump, 256)[::-1]
                opcodes[i+1] = Opcode(low)
                opcodes[i+2] = Opcode(high)
                i+=3
            else:
                i+=1

class generatorwrapper(object):
    def __init__(self, g_gen, *args):
        self._g_gen = g_gen

    def _get_frame(self):
        return self._g_gen.gi_frame

    gi_frame = property(_get_frame)

    def _running(self):
        return self._g_gen.gi_running

    gi_running = property(_running)

    def __iter__(self):
        return self

    def close(self):
        return self._g_gen.close()

    def next(self):
        res = self._g_gen.next()
        return res

    def send(self, arg):
        return self._g_gen.send(arg)

    def throw(typ, val=None, tb=None):
        return self._g_gen.throw(arg, val, tb)

    def __getstate__(self):
        return GeneratorSnapshot(self._g_gen)

    def __setstate__(self, snapshot):
        self._g_gen = copy_generator(snapshot)



class Generatorcopy(generatorwrapper):
    def __init__(self, g_gen, g, offset, f_code, bounds):
        '''
        Generatorcopy is a wrapper around a generator used to store additional
        generator data.

        @param g_gen: generator object copy
        @param g: generator function according to g_gen
        @param offset: bytecode address in f_code
        @param f_code: function code object. Producer of g_gen.

        The f_code object can be used to produce new copies from g_gen.
        '''
        generatorwrapper.__init__(self, g_gen)
        self._g        = g
        self._template = f_code
        self._offset   = offset
        self._bounds   = bounds

    def next(self):
        res = self._g_gen.next()
        return res
        _id_res = id(res)              # enables more adjustments
        if id(res) in self._bounds:    # it doesn't work well though...
            self._bounds = []
            return self._g_gen.next()
        else:
            self._bounds = []
            return res

def is_sharable(loc):
    return hasattr(loc, "sharable") and loc.sharable

def copy_generator(f_gen, copy_filter = is_sharable ):
    '''
    Function used to copy a generator object.

    @param f_gen: generator object.
    @return: g_gen where g_gen is a Generatorcopy object.
    '''
    if not f_gen.gi_frame:
        raise ValueError("Can't copy closed generator")
    if isinstance(f_gen, Generatorcopy):
        return _copy_generator_copy(f_gen)
    elif isinstance(f_gen, GeneratorSnapshot):
        if f_gen.is_copy():
            gcopy = Generatorcopy(f_gen, None, f_gen._offset, f_gen._template, f_gen._bounds)
            return _copy_generator_copy(gcopy)
    elif hasattr(f_gen, "__gencopy__"):
        return f_gen.__gencopy__()

    f_code   = f_gen.gi_frame.f_code
    offset   = max(f_gen.gi_frame.f_lasti, 0)

    locals   = f_gen.gi_frame.f_locals
    argcount = f_code.co_nlocals

    none_var = ''
    if ord(f_code.co_code[offset+1]) == opmap["STORE_FAST"]:  # Python 2.5 yield expression
        oparg = f_code.co_code[offset+2]
        none_var = f_code.co_varnames[ord(oparg)]

    # print "this offset", offset
    if offset:
        bcm = ByteCodeModifier()
        # bytecode hack - insert jump to current offset
        # the offset depends on the version of the Python interpreter
        opcodes = [Opcode(ord(c)) for c in f_code.co_code]
        offset  = compute_offset(offset, opcodes)
        modified_code = "".join(chr(op) for op in bcm.create_new_bytecode(offset, argcount, opcodes))
    else:
        modified_code = f_code.co_code

    varnames  = list(f_code.co_varnames)

    if "jump_forward_on" in varnames:
        varnames.remove("jump_forward_on")
        varnames.remove("jump_forward_off")
    params  = []
    for_itercnt = 0
    bounds = []
    for i, name in enumerate(varnames):
        loc = locals.get(name)
        if isinstance(loc, types.GeneratorType):
            params.append(copy_generator(loc))
        elif hasattr(loc, "__gencopy__"):
            iterview = loc.__gencopy__()
            params.append(iterview)
            bounds.append(iterview._bound)
            for_itercnt+=1
        elif copy_filter(loc):
            params.append(loc)
        elif name == none_var:
            params.append(None)
        else:
            try:
                params.append(copy.deepcopy(loc))
            except TypeError:
                params.append(loc)

    IteratorView.cloning = False
    if offset and for_itercnt<len(bcm.statistics["FOR_ITER"]):
        for_offsets = [ o for o in bcm.statistics["FOR_ITER"] if o<=offset]
        if for_itercnt<len(for_offsets):
            raise CopyGeneratorException("Uncopyable iterator in for-loop found. Use either while-loops or IteratorView objects.")
    varnames.append("jump_forward_on")
    varnames.append("jump_forward_off")
    params.append(True)
    params.append(False)

    # create new generator function using data of the generator function
    # according to the generator object
    argcount = len( params )

    co_names = (f_code.co_names if "jump_forward_on" in f_code.co_names else f_code.co_names + ("jump_forward_on", "jump_forward_off"))

    new_code = new.code(argcount,
             f_code.co_nlocals+2,
             f_code.co_stacksize,
             f_code.co_flags,
             modified_code,
             f_code.co_consts,
             co_names,
             tuple(varnames),
             f_code.co_filename,
             f_code.co_name,
             f_code.co_firstlineno,
             f_code.co_lnotab)
    #g = new.function(new_code, globals(),)
    g = new.function(new_code, new_globals(f_gen.gi_frame),)
    g_gen = g(*params)
    return Generatorcopy(g_gen, g, offset, f_code, bounds)

def new_globals(from_frame):
    _globals = {}
    _globals.update(globals())
    _globals.update(from_frame.f_globals)
    return _globals

def _copy_generator_copy(g_gen):
    class any_obj:
        pass
    f_gen = any_obj()
    f_gen.gi_frame = any_obj()
    f_gen.gi_frame.f_code   = g_gen._template
    f_gen.gi_frame.f_locals = g_gen.gi_frame.f_locals
    f_gen.gi_frame.f_globals = new_globals(g_gen.gi_frame)

    # determine offset in f_code that corresponds to offset in g_code
    # assumption: we count the YIELD_VALUE opcodes with index < offset.
    #             Let k be this number.
    #             Then we search for the k-th YIELD_VALUE opcode in f_code. We determine
    #             the index of the 2nd opcode following YIELD_VALUE.

    g_code = g_gen._g_gen.gi_frame.f_code.co_code
    f_code = f_gen.gi_frame.f_code.co_code
    offset = g_gen.gi_frame.f_lasti

    YIELD_VALUE = chr(opmap["YIELD_VALUE"])
    i = 0
    g_yield_cnt = 0
    while i<=offset:
        c = g_code[i]
        if c == YIELD_VALUE:
            g_yield_cnt+=1
        if ord(c)>=HAVE_ARGUMENT:
            i+=3
        else:
            i+=1
    i = 0
    f_yield_cnt = 0
    while i<len(f_code):
        c = f_code[i]
        if c == YIELD_VALUE:
            f_yield_cnt+=1
            if f_yield_cnt == g_yield_cnt:
                f_gen.gi_frame.f_lasti = i #+3+offset_inc
                break
        if ord(c)>=HAVE_ARGUMENT:
            i+=3
        else:
            i+=1
    else:
        f_gen.gi_frame.f_lasti = g_gen._offset-offset_inc
        IteratorView.cloning = True
    return copy_generator(f_gen)

def foo(x):
    return x

def dbg():
    import dis

    def f():
        yield
        a = 0
        while a<100:
            a = ((yield a) or 1) + ((yield a) or 1)
        yield a

    gen_f = f()
    print "F", gen_f.next()
    print "F", gen_f.next()
    print "F", gen_f.send(5)
    print gen_f.gi_frame.f_locals
    gen_g = copy_generator(gen_f)
    print gen_g.gi_frame.f_locals
    dis.dis(gen_g._g)
    '''
    print "G", gen_g.send(None)
    print "F", gen_f.next()
    print "G", gen_g.send(22)
    print "F", gen_f.send(22)
    print "G", gen_g.send(7)
    print "F", gen_f.send(7)
    '''
    #print "G", gen_g.send(5)


    #print "G", gen_g.send(10)



if __name__ == '__main__':
    #dbg()
    def test_chain_of_copies():
        def f(x):
            r = for_iter(list(range(x)))
            for i in r:
                yield i

        gen_f = f(10)
        next(gen_f)
        gen_g = copy_generator(gen_f)
        next(gen_g)
        gen_h = copy_generator(gen_g)
        next(gen_h)
        gen_k = copy_generator(gen_h)
        assert next(gen_k) == next(gen_h)
    #test_chain_of_copies()



