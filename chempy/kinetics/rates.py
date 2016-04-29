# -*- coding: utf-8 -*-
"""
This module collects object representing rate expressions. It is based
on the ``chemp.util._expr`` module. The API is somewhat cumbersome since
it tries to be compatible with pure python, SymPy and the underlying
units library of ChemPy (``quantities``). Consider the API to be provisional.
"""

from __future__ import (absolute_import, division, print_function)

import math


from ..util._expr import Expr


class RateExpr(Expr):
    """ Baseclass for rate expressions, see source code of e.g. MassAction & Radiolytic. """

    kw = {'rxn': None, 'ref': None}

    @classmethod
    def subclass_from_callback(cls, cb, cls_attrs=None):
        """ Override RateExpr.__call__

        Parameters
        ----------
        cb : callback
            With signature (variables, all_args, backend) -> scalar
            where `variables` is a dict, `all_args` a tuple and `backend` a module.
        cls_attrs : dict, optional
            Attributes to set in subclass, e.g. parameter_keys, nargs

        Examples
        --------
        >>> from chempy import Reaction
        >>> rxn = Reaction({'O2': 1, 'H2': 1}, {'H2O2': 1})  # d[H2O2]/dt = p0*exp(-p1/T)*sqrt([O2])
        >>> def cb(variables, all_args, backend):
        ...     O2, T = variables['O2'], variables['temperature']
        ...     p0, p1 = all_args
        ...     return p0*backend.sqrt(O2)*backend.exp(-p1/T)
        >>> MyRateExpr = RateExpr.subclass_from_callback(cb, dict(parameter_keys=('temperature',),nargs=2))
        >>> k = MyRateExpr([1.3e9, 4317.2], rxn=rxn)
        >>> print('%.5g' % k({'temperature': 298.15, 'O2': 1.1e-3}))
        22.186

        """
        class _RateExpr(cls):

            def __call__(self, variables, backend=math):
                return cb(variables, self.all_args(variables), backend)
        for k, v in (cls_attrs or {}).items():
            setattr(_RateExpr, k, v)
        return _RateExpr


class Radiolytic(RateExpr):
    argument_names = ('radiolytic_yield',)  # [amount/energy]
    parameter_keys = ('doserate', 'density')

    def g_value(self, variables, backend):  # for subclasses
        return self.arg(variables, 0)

    def __call__(self, variables, backend=math):
        return self.g_value(variables, 0)*variables['doserate']*variables['density']


class MassAction(RateExpr):
    argument_names = ('rate_constant',)

    def rate_coeff(self, variables, backend):  # for subclasses
        return self.arg(variables, 0)

    def __call__(self, variables, backend=math):
        prod = self.rate_coeff(variables, backend)
        for k, v in self.rxn.reac.items():
            prod *= variables[k]**v
        return prod

    @classmethod
    def subclass_from_callback(cls, cb, cls_attrs=None):
        """ Override MassAction.rate_coeff

        Parameters
        ----------
        cb : callback
            With signature (variables, all_args, backend) -> scalar
            where `variables` is a dict, `all_args` a tuple and `backend` a module.
        cls_attrs : dict, optional
            Attributes to set in subclass, e.g. parameter_keys, nargs

        Examples
        --------
        >>> from functools import reduce
        >>> from operator import add
        >>> from chempy import Reaction # d[H2]/dt = 10**(p0 + p1/T + p2/T**2)*[e-]**2
        >>> rxn = Reaction({'e-': 2}, {'OH-': 2, 'H2': 1}, None, {'H2O': 2})
        >>> def cb(variables, all_args, backend):
        ...     T = variables['temperature']
        ...     return 10**reduce(add, [p*T**-i for i, p in enumerate(all_args)])
        >>> MyMassAction = MassAction.subclass_from_callback(cb, dict(parameter_keys=('temperature',), nargs=-1))
        >>> k = MyMassAction([9, 300, -75000], rxn=rxn)
        >>> print('%.5g' % k({'temperature': 293., 'e-': 1e-10}))
        1.4134e-11

        """
        class _MassAction(cls):

            def rate_coeff(self, variables, backend=math):
                return cb(variables, self.all_args(variables), backend)
        for k, v in (cls_attrs or {}).items():
            setattr(_MassAction, k, v)
        return _MassAction


class ArrheniusMassAction(MassAction):
    argument_names = ('A', 'Ea_over_R')
    parameter_keys = ('temperature',)

    def rate_coeff(self, variables, backend):
        A, Ea_over_R = self.all_args(variables)
        return A*backend.exp(-Ea_over_R/variables['temperature'])


class EyringMassAction(ArrheniusMassAction):
    argument_names = ('kB_h_times_exp_dS_R', 'dH_over_R')

    def rate_coeff(self, variables, backend):
        kB_h_times_exp_dS_R, dH_over_R = self.all_args(variables)
        T = variables['temperature']
        return T * kB_h_times_exp_dS_R * backend.exp(-dH_over_R/T)