# MIT License

# Copyright (c) 2018 PLSousa

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
usage:
>>> from random import randint
>>> randint(1,100)
16
>>> from random import choice
>>> mylist = ['Paris','London','Roma','Rio']
>>> choice(mylist)
'Roma'
"""

import sys
import urandom

def _rescale(Nmin, Nmax, OldValue):
    NewRange = Nmax - Nmin  
    NewValue = OldValue * NewRange / sys.maxsize + Nmin
    return NewValue

# Return a random integer N such that Nmin <= N <= Nmax.
def randint(Nmin, Nmax):
    Oldint = urandom.getrandbits(31)
    N = round(_rescale(Nmin-0.5, Nmax+0.5, Oldint))
    return N

# Return a random element from a list.
def choice(mylist):
    index = randint(0,len(mylist)-1)
    return mylist[index]