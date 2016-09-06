import pickle
import types
import sys
import StringIO
import warnings

from copygenerators import GeneratorSnapshot, copy_generator, Generatorcopy

warnings.simplefilter("always", PendingDeprecationWarning)

__all__ = ["dump",
           "pickle_generator",
           "load",
           "unpickle_generator",
           "Pickler",
           "GeneratorPickler",
           "Unpickler",
           "GeneratorUnpickler",
           "dumps",
           "loads"]

HIGHEST_PROTOCOL = pickle.HIGHEST_PROTOCOL

def dump(obj, file, protocol=0):
    Pickler(file, protocol).dump(obj)

def dumps(obj, protocol=0):
    filelike = StringIO.StringIO()
    Pickler(filelike, protocol).dump(obj)
    return filelike.getvalue()

def pickle_generator(f_gen, filelike):
    lineno = sys._getframe(0).f_lineno +1
    warnings.warn_explicit("pickle_generator not supported in generator_tools 0.5 - use dump instead!\n" , PendingDeprecationWarning, "picklegenerators.py", lineno)
    dump(f_gen, filelike)


def load(file):
    return Unpickler(file).load()

def loads(str):
    filelike = StringIO.StringIO(str)
    return Unpickler(filelike).load()

def unpickle_generator(filelike):
    lineno = sys._getframe(0).f_lineno +1
    warnings.warn_explicit("unpickle_generator not supported in generator_tools 0.5 - use load instead!\n" , PendingDeprecationWarning, "picklegenerators.py", lineno)
    return load(filelike)

class SnapshotEnvelope(object):
    '''
    Wrapper class used to decept internal pickler memoization.

    Motivation:
        Suppose a Generator object G gets pickled. For each occurrence of G the save_generator
        method of Pickler is called. We have to create a GeneratorSnapshot object for G.
        If we cache a GeneratorSnapshot and reuse it for each occurrence of G it will be passed
        only once to load_build on unpickling. In load_build we write a generator_copy in the
        output stream but this has a local effect only. On all other occurrences the unpickled
        GeneratorSnapshot is yielded not a generator_copy.

        We try to move around this and memoize GeneratorSnapshots on ourselves while creating
        distinct instances of SnapshotEnvelope for each occurrence of G. So they look distinct
        and load_build is called for each. On each call we can write a generator_copy in the
        output.
    '''
    def __init__(self, obj):
        if isinstance(obj, SnapshotEnvelope):
            self.obj = obj.obj
        else:
            obj._uses_envelope = True
            self.obj = obj


class Pickler(pickle.Pickler, object):
    def __init__(self, file, protocol=0):
        if isinstance(file, (str, unicode)):
            lineno = sys._getframe(0).f_lineno +1
            warnings.warn_explicit("string argument not supported in generator_tools 0.5 - use filelike instead!\n" , PendingDeprecationWarning, "picklegenerators.py", lineno)
            file = open(file, "wb")
        super(Pickler, self).__init__(file, protocol)
        self._pickled_generators_memo = {}

    def save_generator(self, obj):
        snapshot = self._pickled_generators_memo.get(obj)
        if snapshot is None:
            snapshot = GeneratorSnapshot(obj)
            self._pickled_generators_memo[obj] = snapshot
        super(Pickler, self).save(SnapshotEnvelope(snapshot))

    pickle.Pickler.dispatch[types.GeneratorType] = save_generator
    pickle.Pickler.dispatch[Generatorcopy] = save_generator

    def pickle_generator(self, f_gen):
        lineno = sys._getframe(0).f_lineno +1
        warnings.warn_explicit("method pickle_generator deprecated in generator_tools 0.5 - use dump() instead!\n" , PendingDeprecationWarning, "picklegenerators.py", lineno)
        self.dump(f_gen)

class GeneratorPickler(Pickler):
    def __init__(self, filelike, protocol=None):
        lineno = sys._getframe(0).f_lineno +1
        warnings.warn_explicit("class GeneratorPickler deprecated in generator_tools 0.5 - use Pickler() instead!\n" , PendingDeprecationWarning, "picklegenerators.py", lineno)
        super(GeneratorPickler, self).__init__(filelike, protocol)


class Unpickler(pickle.Unpickler, object):
    def __init__(self, file):
        if isinstance(file, (str, unicode)):
            lineno = sys._getframe(0).f_lineno +1
            warnings.warn_explicit("string argument not supported in generator_tools 0.5 - use filelike instead!\n" , PendingDeprecationWarning, "picklegenerators.py", lineno)
            file = open(file, "rb")
        super(Unpickler, self).__init__(file)
        self._unpickled_generators_memo = {}


    def load_build(self):
        super(Unpickler, self).load_build()
        if type(self.stack[-1]) == SnapshotEnvelope:
            obj = self.stack[-1]
            gencopy = self._unpickled_generators_memo.get(id(obj.obj))
            if gencopy is None:
                gencopy = copy_generator(obj.obj, copy_filter = lambda loc: True)
                self._unpickled_generators_memo[id(obj.obj)] = gencopy
            self.stack[-1] = gencopy
        elif type(self.stack[-1]) == GeneratorSnapshot:
            obj = self.stack[-1]
            if not obj._uses_envelope:
                self.stack[-1] = copy_generator(obj, copy_filter = lambda loc: True)



    pickle.Unpickler.dispatch[pickle.BUILD] = load_build

    def unpickle_generator(self):
        lineno = sys._getframe(0).f_lineno +1
        warnings.warn_explicit("method upickle_generator deprecated in generator_tools 0.5 - use load() instead!\n" , PendingDeprecationWarning, "picklegenerators.py", lineno)
        return self.load()


class GeneratorUnpickler(Unpickler):
    def __init__(self, filelike, protocol = None):
        lineno = sys._getframe(0).f_lineno +1
        warnings.warn_explicit("class GeneratorUnpickler deprecated in generator_tools 0.5 - use Unpickler() instead!\n" , PendingDeprecationWarning, "picklegenerators.py", lineno)
        super(GeneratorUnpickler, self).__init__(filelike, protocol)



