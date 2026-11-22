# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
import random
import unittest
from core.prefix_demand import prefix_for_demand
from core.ipv6_core import InputError


class PrefixDemandTests(unittest.TestCase):
    def test_300_subnets_minimum_and_nibble_alternative(self):
        result = prefix_for_demand('300')
        self.assertEqual((result.minimum_prefix, result.aligned_prefix), (55, 52))
        self.assertEqual((result.capacity(55), result.capacity(52)), (512, 4096))
        self.assertEqual(result.required, 300)

    def test_reserve_ceil_and_power_boundary(self):
        self.assertEqual(prefix_for_demand('3', '64', '10').required, 4)
        self.assertEqual(prefix_for_demand('256', '64', '1').minimum_prefix, 55)
        self.assertEqual(prefix_for_demand('256', '64', '0').minimum_prefix, 56)
        self.assertEqual(prefix_for_demand('1', '128', '100').minimum_prefix, 127)

    def test_full_ipv6_space_zero_and_128_prefixes(self):
        self.assertEqual(prefix_for_demand(str(2**128), '128').minimum_prefix, 0)
        self.assertEqual(prefix_for_demand('1', '0').minimum_prefix, 0)
        self.assertEqual(prefix_for_demand('1', '128').minimum_prefix, 128)
        for args in (('2','0','0'), (str(2**128),'128','1')):
            with self.assertRaises(InputError):prefix_for_demand(*args)

    def test_invalid_bounded_ascii_integers_report_fields(self):
        for value in ('', '0', '-1', '1.5', '１', '1_000', str(2**128+1), '9'*10000):
            with self.subTest(value=value[:30]), self.assertRaises(InputError) as error:prefix_for_demand(value)
            self.assertEqual(error.exception.field, 'count')
        for value in ('/64','129','-1','64.0','0x40'):
            with self.assertRaises(InputError) as error:prefix_for_demand('1', value)
            self.assertEqual(error.exception.field, 'target')
        for value in ('101','-1','0.5','１',''):
            with self.assertRaises(InputError) as error:prefix_for_demand('1', '64', value)
            self.assertEqual(error.exception.field, 'reserve')

    def test_seeded_minimality_and_exact_reserve_without_float(self):
        rng = random.Random(137)
        for _ in range(300):
            count = rng.randrange(1, 2**64)
            reserve = rng.randrange(101)
            result = prefix_for_demand(str(count), '128', str(reserve))
            required = count + (count*reserve+99)//100
            self.assertEqual(result.required, required)
            capacity = result.capacity(result.minimum_prefix)
            self.assertGreaterEqual(capacity, required)
            self.assertLess(capacity//2, required)
            self.assertEqual(result.aligned_prefix % 4, 0)
            self.assertLessEqual(result.aligned_prefix, result.minimum_prefix)
