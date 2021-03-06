generator_tools
===============

generator_tools is a package used to provide facilities for generators such as
copying and pickling.

This project has been forked from version 0.3.6
http://www.fiber-space.de/generator_tools/doc/generator_tools.html.

It has been modified to work with Python 2.7, and support for earlier Python versions has
been dropped.

INSTALLATION

Just type

          python setup.py install

while being in the root directory of the project. This will place generator_tools in
Python's site-packages directory.


DOCUMENTATION


http://www.fiber-space.de/generator_tools/doc/generator_tools.html

The same document can be found in the local installation at

     site-packages/generator_tools/doc


USAGE

Here is some simple use case:

from generator_tools.copygenerators import*
from generator_tools.picklegenerators import*

def f(start):
	i = start
	while i<start+10:
		yield i
		i+=1

>>> f_gen = f(5)
>>> f_gen.next()
5
>>> f_gen.next()
6
>>> g_gen = copy_generator(f_gen)
>>> h_gen = copy_generator(f_gen)
>>> g_gen.next()
7
>>> h_gen.next()
7
>>> pickler = GeneratorPickler("test.pkl")
>>> pickler.pickle_generator(g_gen)
>>> k_gen = pickler.unpickle_generator()
>>> list(g_gen) == list(k_gen)
True

