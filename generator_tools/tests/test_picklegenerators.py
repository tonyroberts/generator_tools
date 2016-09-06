from generator_tools.picklegenerators import*
from generator_tools.copygenerators import*
import pickle

class GeneratorPickler4Test(object):
    def __init__(self, filename):
        self.filename = filename

    def pkl_device_new(self):
        return open(self.filename, "wb")

    def pkl_device_load(self):
        return open(self.filename, "rb")

    def pickle_generator(self, f_gen):
        pkl_device = self.pkl_device_new()
        return dump(f_gen, pkl_device)

    def unpickle_generator(self):
        pkl_device = self.pkl_device_load()
        return load(pkl_device)


import unittest
import test_support
import time

def pickletest(n=2, raises = None, fun_args = (), kwd_args = {}):
    gp = GeneratorPickler4Test("test.pkl")
    name = []
    def test(method):
        def test_wrap(self):
            f = method(self)
            gen_f = f(*fun_args, **kwd_args)
            for i in range(n):
                gen_f.next()
            if raises:
                self.assertRaises(raises, gp.pickle_generator, gen_f)
            else:
                time.sleep(0.05)
                gp.pickle_generator(gen_f)
                time.sleep(0.05)
                gen_g = gp.unpickle_generator()
                self.assertEqual(list(gen_g),list(gen_f))
        test_wrap.__name__ = method.__name__
        return test_wrap
    return test


class TestPickleWhileLoop(unittest.TestCase):
    @pickletest(2, fun_args = (1,))
    def test_simple_while_loop(self):
        def f(x):
            i = 0
            while i<10:
                yield i
                i+=1
        return f

    @pickletest(5)
    def test_while_sequence_5(self):
        def f():
            k = 0
            while k<3:
                yield k
                k+=1
            while k<6:
                yield k
                k+=1
            while k<9:
                yield k
                k+=1
        return f

    @pickletest(7)
    def test_while_sequence_7(self):
        def f():
            k = 0
            while k<3:
                yield k
                k+=1
            while k<6:
                yield k
                k+=1
            while k<9:
                yield k
                k+=1
        return f

    @pickletest(2)
    def test_nested_while_1(self):
        def f():
            k = 0
            while k<5:
                yield k
                j = 0
                while j<10:
                    yield (k,j)
                    j+=1
                k+=1
        return f

    @pickletest(3)
    def test_nested_while_2(self):
        def f():
            k = 0
            while k<4:
                yield k
                j = 0
                while j<2:
                    yield k,j
                    i = 0
                    while i<2:
                        yield k,j,i
                        i+=1
                    j+=1
                k+=1
        return f


    @pickletest(3)
    def test_nested_while_6(self):
        def f():
            k = 0
            while k<8:
                while k<7:
                    while k<6:
                        while k<5:
                            while k<4:
                                while k<3:
                                    while k<2:
                                        k+=1
                                        yield k
                                    k+=1
                                    yield k
                                k+=1
                                yield k
                            k+=1
                            yield k
                        k+=1
                        yield k
                    k+=1
                    yield k
                k+=1
                yield k
        return f

class TestTryStmt(unittest.TestCase):
    @pickletest(2)
    def test_simple_try_stmt(self):
        def f():
            try:
                yield 0
                yield 1
                yield 2
                1/0
            except ZeroDivisionError:
                pass
        return f

    @pickletest(3)
    def test_nested_try_stmt(self):
        def f():
            k = 0
            try:
                yield 0
                try:
                    yield 1
                    yield 2
                    k.bla
                except AttributeError:
                    pass
                yield 3
                1/0
            except ZeroDivisionError:
                yield 4
        return f

    @pickletest(3)
    def _test_try_finally(self):
        def f():
            k = 0
            try:
                yield 0
                yield 1
                k.bla
            except AttributeError:
                yield 2
                yield 3
            finally:
                yield 5
            yield 4
        return f

    @pickletest(3)
    def test_try_while(self):
        def f():
            k = 0
            try:
                while k<2:
                    yield k
                    yield k+1
                    k+=1
                yield 2
                1/0
            except ZeroDivisionError:
                pass
        return f

    @pickletest(3)
    def test_while_try_while(self):
        def f():
            k = 0
            while k<10:
                try:
                    while k<2:
                        yield k
                        yield k+1
                        k+=1
                    k+=1
                    yield 2
                    if k == 7:
                        1/0
                except ZeroDivisionError:
                    break
        return f

class TestForStmt(unittest.TestCase):

    @pickletest(3)
    def test_simple_for(self):
        def f():
            r = for_iter(range(10))
            for i in r:
                yield i
        return f


    @pickletest(77)
    def test_nested_for(self):
        def f():
            r1 = for_iter(range(10))
            for i in r1:
                r2 = for_iter(range(10))
                for j in r2:
                    yield i+j
        return f

    @pickletest(15)
    def test_sequence_of_nested_for_2(self):
        def f():
            r1 = for_iter(range(3))
            for i in r1:
                r2 = for_iter(range(3))
                for j in r2:
                    yield i+j
            r3 = for_iter(range(3))
            for i in r3:
                r4 = for_iter(range(3))
                for j in r4:
                    yield i+j
        return f


    @pickletest(77)
    def test_deep_nesting(self):
        def f():
            r1 = for_iter(range(2))
            for i1 in r1:
                r2 = for_iter(range(2))
                for i2 in r2:
                    r3 = for_iter(range(2))
                    for i3 in r3:
                        r4 = for_iter(range(2))
                        for i4 in r4:
                            r5 = for_iter(range(2))
                            for i5 in r5:
                                r6 = for_iter(range(2))
                                for i6 in r6:
                                    r7 = for_iter(range(2))
                                    for i7 in r7:
                                        yield i1+i2+i3+i4+i5+i6+i7
        return f

class TestForAndWhileStmt(unittest.TestCase):
    @pickletest(9)
    def test_for_while(self):
        def f():
            r = for_iter(range(7))
            for i in r:
                j = 0
                while j<5:
                    yield i+j
                    j+=1
                yield i-j
        return f

    @pickletest(9)
    def test_while_for(self):
        def f():
            j = 0
            while True:
                r = for_iter(range(7))
                for i in r:
                    yield i+j
                j+=1
                yield i-j
                if j == 5:
                    break
        return f

class TestForAndWhileStmtWithAddArgs(unittest.TestCase):
    @pickletest(9, fun_args = (3,4))
    def test_fun_args(self):
        def f(x,y):
            r = for_iter(range(7))
            for i in r:
                j = 0
                while j<5:
                    yield i+j+x
                    j+=1
                yield i-j-y
        return f

    @pickletest(9, fun_args = (3,4), kwd_args = {"a":9})
    def test_fun_and_kwd_args(self):
        def f(x,y,a):
            r = for_iter(range(7))
            for i in r:
                j = 0
                while j<5:
                    yield i+j+x
                    j+=1
                yield i-j-y-a
        return f

class TestMultipleGenerators(unittest.TestCase):
    def g1(self, x,y):
        r = for_iter(range(7))
        for i in r:
            j = 0
            while j<5:
                yield i+j+x
                j+=1
            yield i-j-y

    def g2(self, x,y):
        r = for_iter(range(x,y))
        for i in r:
            yield i

    def g3(self,x,y):
        r = for_iter(range(7))
        for i in r:
            yield i+x+y

    @pickletest(20, fun_args = (3,4))
    def test_fun_args(self):
        def f(x,y):
            r = for_iter(self.g1(4,5))
            for i in r:
                j = 0
                while j<5:
                    yield i+j+x
                    j+=1
                yield i-j-y

        return f


    @pickletest(15, fun_args = (3,4))
    def test_multi_gen1(self):
        def f(x,y):
            G = for_iter([self.g2(0,7), self.g2(7,14), self.g2(14, 21)])
            for h in G:
                H = for_iter(h)
                for item in H:
                    yield item
        return f

    @pickletest(20, fun_args = (3,4))
    def test_multi_gen2(self):
        def f(x,y):
            G = for_iter(self.g3(i,j) for i in [1,2] for j in [3,4])
            for h in G:
                H = for_iter(h)
                for item in H:
                    yield item + x + y
        return f

    @pickletest(5, fun_args = (3,4))
    def test_multi_gen3(self):
        def f(x,y):
            G = for_iter(self.g3(i,j) for i in [1,2] for j in [3,4])
            for h in G:
                H = for_iter(h)
                for item in H:
                    yield item + x + y
        return f

class TestPickleUnpickleSequences(unittest.TestCase):

    def test_pickle_of_unpickled(self):
        def f(x):
            r = for_iter(range(x))
            for i in r:
                yield i

        gp = GeneratorPickler4Test("test.pkl")
        gen_f = f(10)
        gen_f.next()
        gen_f.next()
        gp.pickle_generator(gen_f)
        gen_g = gp.unpickle_generator()
        gen_g.next()
        gen_f.next()
        gp.pickle_generator(gen_g)
        gen_h = gp.unpickle_generator()
        l_g = list(gen_g)
        l_h = list(gen_h)
        l_f = list(gen_f)
        self.assertEqual(l_g, l_h)
        self.assertEqual(l_g, l_f)


    def test_chain_pkl_upkl(self):
        def f(x):
            r = for_iter(range(x))
            for i in r:
                yield i
        gp = GeneratorPickler4Test("test.pkl")
        gen_f = f(10)
        gen_f.next()
        gp.pickle_generator(gen_f)
        gen_g = gp.unpickle_generator()
        gen_g.next()
        gp.pickle_generator(gen_g)
        gen_h = gp.unpickle_generator()
        gen_h.next()
        gp.pickle_generator(gen_h)
        gen_k = gp.unpickle_generator()
        self.assertEqual(gen_k.next(), gen_h.next())

    def test_chain_pkl_upkl_without_next(self):
        def f(x):
            r = for_iter(range(x))
            for i in r:
                yield i

        gen_f = f(10)
        gen_f.next()
        gen_f.next()
        gen_f.next()
        gp = GeneratorPickler4Test("test.pkl")
        gp.pickle_generator(gen_f)
        gen_g = gp.unpickle_generator()
        gp.pickle_generator(gen_g)
        gen_h = gp.unpickle_generator()
        gp.pickle_generator(gen_h)
        gen_k = gp.unpickle_generator()
        gp.pickle_generator(gen_k)
        gen_m = gp.unpickle_generator()
        l_g = list(gen_g)
        l_h = list(gen_h)
        l_k = list(gen_k)
        l_m = list(gen_m)
        self.assertEqual(l_g, l_h)
        self.assertEqual(l_h, l_k)
        self.assertEqual(l_k, l_m)


class TestPickleClasses(unittest.TestCase):
    def setUp(self):
        self.test_pkl = open("test.pkl", "wb")

    def tearDown(self):
        if not self.test_pkl.closed:
            self.test_pkl.close()

    def test_GeneratorPickler(self):
        gp = Pickler(self.test_pkl)

        def f(x):
            r = for_iter(range(x))
            for i in r:
                yield i

        gen_f = f(10)
        gen_f.next()
        gen_f.next()

        gp.dump(gen_f)

        self.test_pkl.close()
        self.test_pkl = open("test.pkl", "rb")

        up = Unpickler(self.test_pkl)
        gen_g = up.load()
        self.assertEqual(list(gen_g), list(gen_f))


class TestPicklingDependencies(unittest.TestCase):

    def test_dependent_pickles(self):
        '''
        This tests a fix of version 0.1.1

        Problem ( reported by Lorenz Quack ):

            Pickling of generators is a staged process. First gen_f is mapped onto a GeneratorSnapshot GS_f
            then GS_f is pickled. On unpickling, GS_f is reconstructed. Finally gen_f is built using
            gen_f = copy_generator(GS_f).

            Suppose you send an object X into gen_f transform gen_f into GS_f, then pickle (X, GS_f) and later
            unpickle it to reconstruct (X, GS_f). The unpickled GS_f still holds a reference on X. But this
            reference is destroyed by copy_generator(GS_f) because copy_generator makes a deepcopy.

            This behaviour can be avoided. Usually GS_f will be destroyed just after execution of copy_generator(GS_f).
            Instead of deepcopying the locals of GS_f we just move the references into gen_f.

            The following test demonstrates the behaviour.
        '''

        lst = range(10)

        def f(obj):
            while obj:
                yield obj.pop(0)

        gen_f = f(lst)
        self.assertEqual(gen_f.next(), 0)
        pickle.dump( (lst, GeneratorSnapshot(gen_f)), open("test.pkl", "wb"))

        lst_u, gen_f_u = load( open("test.pkl", "rb") )

        #gen_f_u = copy_generator(GS_f_u, copy_filter = lambda loc: True )
        self.assertEqual( gen_f_u.next(), 1)
        self.assertEqual( gen_f_u.next(), 2)
        self.assertEqual( lst_u[0], gen_f_u.next())   # lst_u is the list used in gen_f_u

    def test_generator_identity(self):
        '''
        This tests a fix of version 0.3

        Problem ( reported by Jenna Louis ):

            When a generator object G exists on different locations loc1, loc2 sameness isn't preserved when it gets
            pickled i.e. two distinct GeneratorSnapshots GS1, GS2 will be created. This glitch can be noticed
            on unpickling. The fix requires some workaround in the pickling module because load_build shall be called
            for each location of G. So we create a unique GS from G but wrap GS again into SnapshotEnvelopes
            EGS1, EGS2. They are distinct but refer to the same GS. On unpickling load_build is called for each EGSx
            and a unique generatorcopy can be reconstructed from GS.
        '''
        lst = range(10)

        def f(obj):
            while obj:
                yield obj.pop(0)

        gen_f = f(lst)
        self.assertEqual(gen_f.next(), 0)

        dump([gen_f, gen_f], open("test.pkl", "wb"))

        gen_f_u, gen_g_u = load( open("test.pkl", "rb") )
        self.assertEqual( gen_f_u, gen_g_u)





def test_main():
    test_support.run_unittest(TestPickleWhileLoop)
    test_support.run_unittest(TestTryStmt)
    test_support.run_unittest(TestForStmt)
    test_support.run_unittest(TestForAndWhileStmt)
    test_support.run_unittest(TestForAndWhileStmtWithAddArgs)
    test_support.run_unittest(TestMultipleGenerators)
    test_support.run_unittest(TestPickleUnpickleSequences)
    test_support.run_unittest(TestPickleClasses)
    test_support.run_unittest(TestPicklingDependencies)

if __name__ == '__main__':
    test_main()


