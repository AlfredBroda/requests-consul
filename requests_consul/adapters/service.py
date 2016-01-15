import logging
import random
from urllib.parse import urlsplit, SplitResult

from consul import Consul
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException


logger = logging.getLogger('requests_consul.adapters.service')


class NoSuchService(RequestException):
    """Service hasn't been found in Consul."""
    pass


class ConsulServiceAdapter(HTTPAdapter):
    """An Adapter which connects to Consul gets the service instances and then
    connects to a random instance.

    :param str dc: Datacenter which should be queried, if None the default
                   behaviour of :py:class:`consul.Consul` is used
    :param str host: Consul API hostname or IP address
    :param int port: Consul API port
    :param bool dc_aware: If False the `dc` parameter is ignored and all
                          registered data centers are queried
    :raises NoSuchService: If service cannot be found in Consul

    Example usage:

    .. code-block:: python

        import requests
        from requests_consul.adapters.service import ConsulServiceAdapter

        DC='datacenterX'
        CONSUL_HOST = 'consul.mydomain'
        CONSUL_PORT = 80
        s = requests.Session()
        s.mount('service://', ConsulServiceAdapter(dc=DC,
                                                   host=CONSUL_HOST,
                                                   port=CONSUL_PORT))
        response = s.get('service://my_service/foo/bar')
    """

    __attrs__ = HTTPAdapter.__attrs__ + ['dc', 'host', 'port', 'dc_aware']

    def __init__(self, dc=None, host='127.0.0.1', port=8500, dc_aware=True,
                 **kwargs):
        self.dc = dc
        self.dc_aware = dc_aware
        self.consul_host = host
        self.consult_port = port
        self._connect_to_consul(self.consul_host, self.consult_port)

        super(ConsulServiceAdapter, self).__init__(**kwargs)

    def _connect_to_consul(self, host, port):
        """Connects to the given consul instance."""
        logger.debug('Connecting to Consul %s %s', host, port)
        self.consul = Consul(host, port)

    def _fetch_instances(self, service_name):
        instances = []
        if self.dc_aware:
            instances = \
                self.consul.catalog.service(service_name, dc=self.dc)[1]
        else:
            datacenters = self.consul.catalog.datacenters()
            for dc in datacenters:
                instances.extend(self.consul.catalog.service(
                                 service_name, dc=dc)[1])
        logger.debug('Got instances: %s', instances)
        return instances

    def _build_instance_url(self, url):

        # Get the all service instances from Consul
        service_name = url.hostname
        instances = self._fetch_instances(service_name)

        # Get a random instance
        if instances:
            instance = random.choice(instances)
        else:
            raise NoSuchService
        if 'secureConnection:true' in instance['ServiceTags']:
            scheme = 'https'
        else:
            scheme = 'http'

        if url.username and url.password:
            netloc = '{}:{}@{}:{}'.format(url.username, url.password,
                                          instance['ServiceAddress'],
                                          instance['ServicePort'])
        elif url.username:
            netloc = '{}@{}:{}'.format(url.username,
                                       instance['ServiceAddress'],
                                       instance['ServicePort'])
        else:
            netloc = '{}:{}'.format(instance['ServiceAddress'],
                                    instance['ServicePort'])
        url = SplitResult(scheme=scheme, netloc=netloc, path=url.path,
                          query=url.query, fragment=url.fragment)

        return url

    def get_connection(self, url, proxies=None):
        parsed = urlsplit(url)

        if parsed.scheme != 'service':
            logger.debug(
                'Ignoring adapter, because scheme is %s', parsed.scheme)
            return super(ConsulServiceAdapter, self).get_connection(url,
                                                                    proxies)

        logger.debug('Getting random instance from Consul')
        url = self._build_instance_url(parsed).geturl()
        conn = self.poolmanager.connection_from_url(url)

        return conn
