# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function)

try:
    import numpy as np
    from numpy import any as _any

    def prodpow(bases, exponents):
        """
        Examples
        --------
        >>> prodpow([2, 3], np.array([[0, 1], [1, 2]]))
        array([ 3, 18])

        """
        exponents = np.asarray(exponents)
        return np.multiply.reduce(bases**exponents, axis=-1)

except ImportError:  # no NumPy available
    def _any(arg):
        if arg is True:
            return True
        if arg is False:
            return False
        return any(arg)

    def prodpow(bases, exponents):
        """
        Examples
        --------
        >>> prodpow([2, 3], [[0, 1], [1, 2]])
        [3, 18]

        """
        result = []
        for row in exponents:
            res = 1
            for b, e in zip(bases, row):
                res *= b**e
            result.append(res)
        return result


def get_backend(backend):
    if isinstance(backend, str):
        backend = __import__(backend)
    if backend is None:
        try:
            import numpy as backend
        except ImportError:
            import math as backend
    return backend


def intdiv(p, q):
    """ Integer divsions which rounds toward zero

    Examples
    --------
    >>> intdiv(3, 2)
    1
    >>> intdiv(-3, 2)
    -1
    >>> -3 // 2
    -2

    """
    r = p // q
    if r < 0 and q*r != p:
        r += 1
    return r


class NameSpace:
    def __init__(self, default):
        self._NameSpace_default = default
        self._NameSpace_attr_store = {}

    def __getattr__(self, attr):
        if attr.startswith('_NameSpace_'):
            return self.__dict__[attr]
        else:
            try:
                return self._NameSpace_attr_store[attr]
            except KeyError:
                return getattr(self._NameSpace_default, attr)

    def __setattr__(self, attr, val):
        if attr.startswith('_NameSpace_'):
            self.__dict__[attr] = val
        else:
            self._NameSpace_attr_store[attr] = val

    def as_dict(self):
        items = self._NameSpace_default.__dict__.items()
        result = {k: v for k, v in items if not k.startswith('_')}
        result.update(self._NameSpace_attr_store)
        return result


class AttributeDict(object):
    def __init__(self, d):
        self.__dict__.update(d)
