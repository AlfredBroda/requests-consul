# -*- coding: utf-8 -*-
import json
from unittest import TestCase
from urllib.parse import urlsplit, parse_qs

from ddt import ddt, data, unpack
import responses

from requests_consul.adapters.service import ConsulServiceAdapter, \
    NoSuchService


def service_list_callback(request):
    query = parse_qs(urlsplit(request.url).query)
    headers = {'X-Consul-Index': '1'}
    if not query.get('dc'):
        with open('tests/fixtures/dc1.json', 'r') as file:
            body = json.load(file)
    else:
        dc = query['dc'][0]
        with open('tests/fixtures/{}.json'.format(dc), 'r') as file:
            body = json.load(file)

    return 200, headers, json.dumps(body)


def no_such_service_callback(request):
    headers = {'X-Consul-Index': '1'}
    body = []
    return 200, headers, json.dumps(body)


@ddt
class TestConsulServiceAdapter(TestCase):

    def setUp(self):
        consul_url = 'http://127.0.0.1:8500/v1/catalog/service/dummy'
        responses.add_callback(responses.GET,
                               consul_url,
                               callback=service_list_callback,
                               content_type='application/json',
                               )
        responses.add(responses.GET,
                      'http://127.0.0.1:8500/v1/catalog/datacenters',
                      body='["dc1","dc2"]',
                      status=200,
                      content_type='application/json')

        no_service_url = 'http://127.0.0.1:8500/v1/catalog/service/notex'
        responses.add_callback(responses.GET,
                               no_service_url,
                               callback=no_such_service_callback,
                               content_type='application/json',
                               )

    @responses.activate
    def test_get_connection_single_host(self):
        adapter = ConsulServiceAdapter()

        conn = adapter.get_connection('service://dummy/')
        self.assertEqual(conn.host, '127.0.0.1')
        self.assertEqual(conn.port, 111)

    @data(('dc2', '127.0.1.1'), ('dc1', '127.0.0.1'))
    @unpack
    @responses.activate
    def test_get_instances(self, dc, required_ip):
        """Test fetching instances for a given data center. Used DC: {0}"""
        adapter = ConsulServiceAdapter(dc=dc)
        instances = adapter._fetch_instances('dummy')
        first_instance_ip = instances[0]['ServiceAddress']
        self.assertEqual(first_instance_ip, required_ip)

    @responses.activate
    def test_get_instances_all_dc(self):
        """Test getting instances from ALL known datacenters."""
        adapter = ConsulServiceAdapter(dc_aware=False)
        instances = adapter._fetch_instances('dummy')
        ips = [instance['ServiceAddress'] for instance in instances]
        ips.sort()
        self.assertListEqual(ips, ['127.0.0.1', '127.0.1.1'])

    @responses.activate
    def test_get_notexisting_service(self):
        adapter = ConsulServiceAdapter(dc_aware=False)
        with self.assertRaises(NoSuchService):
            adapter.get_connection('service://notex')
