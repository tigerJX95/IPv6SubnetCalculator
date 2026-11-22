# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
import unittest
from ipaddress import IPv6Network
from core.reverse_zones import reverse_zones
from core.ipv6_core import InputError


class ReverseZoneTests(unittest.TestCase):
    def test_known_48_zone(self):
        result = reverse_zones('2001:db8:abcd::/48')
        self.assertEqual(result.zones, ('d.c.b.a.8.b.d.0.1.0.0.2.ip6.arpa',))

    def test_non_nibble_57_has_eight_exact_60_partitions(self):
        result = reverse_zones('2001:db8:abcd::/57')
        self.assertEqual(len(result.zones), 8)
        self.assertTrue(all(n.prefixlen==60 and n.subnet_of(result.network) for n in result.networks))
        self.assertEqual(sum(n.num_addresses for n in result.networks), result.network.num_addresses)
        self.assertEqual(len(set(result.zones)), 8)

    def test_all_129_prefixes_round_trip_names_and_no_address_enumeration(self):
        for prefix in range(129):
            result = reverse_zones('::/'+str(prefix))
            self.assertLessEqual(len(result.networks), 8)
            self.assertEqual(sum(n.num_addresses for n in result.networks), 2**(128-prefix))
            self.assertEqual(result.networks[0].network_address, result.network.network_address)
            self.assertEqual(result.networks[-1].broadcast_address, result.network.broadcast_address)
            for n, zone in zip(result.networks, result.zones):
                labels = zone.removesuffix('ip6.arpa').strip('.').split('.') if zone != 'ip6.arpa' else []
                digits = ''.join(reversed(labels)).ljust(32, '0')
                self.assertEqual(int(digits,16), int(n.network_address))
                self.assertEqual(len(labels)*4, n.prefixlen)

    def test_host_bits_and_equivalent_address_notations(self):
        result = reverse_zones('2001:0DB8:ABCD::1/48')
        self.assertEqual(result.network, IPv6Network('2001:db8:abcd::/48'))
        self.assertEqual(result.zones, reverse_zones('2001:db8:abcd::/48').zones)
        self.assertEqual(reverse_zones('2001:db8::192.0.2.1/128').zones,
                         reverse_zones('2001:db8::c000:201/128').zones)
        self.assertEqual(reverse_zones('::/0').zone_text(), 'ip6.arpa')

    def test_invalid_input_rejected(self):
        for value in ('','::1','192.0.2.0/24','::/129','fe80::%eth0/64','bad','a'*10000):
            with self.subTest(value=value[:30]), self.assertRaises(InputError) as error:reverse_zones(value)
            self.assertEqual(error.exception.field,'network')

    def test_equivalent_address_data_across_conversion_tools(self):
        from core.address_conversion import convert_address
        from core.address_utilities import reverse_dns, offset_address
        from core.nat64 import convert_nat64
        variants = ('2001:db8:abcd:1::c000:221',
                    '2001:0DB8:ABCD:0001:0000:0000:C000:0221',
                    '2001:db8:abcd:1::192.0.2.33')
        first = variants[0]
        for value in variants:
            self.assertEqual(convert_address(value).compressed, first)
            self.assertEqual(reverse_dns(value).name, reverse_dns(first).name)
            self.assertEqual(str(offset_address(value,'0').address), first)
            self.assertEqual(str(convert_nat64(value, '2001:db8:abcd:1::/96',extract=True).ipv4),'192.0.2.33')
