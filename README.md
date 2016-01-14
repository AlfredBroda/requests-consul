# requests-consul
[![Build Status](https://travis-ci.org/RulersOfAsgard/requests-consul.svg?branch=master)](https://travis-ci.org/RulersOfAsgard/requests-consul)
[![Documentation Status](https://readthedocs.org/projects/requests-consul/badge/?version=latest)](http://requests-consul.readthedocs.org/en/latest/?badge=latest)
[![Code Health](https://landscape.io/github/RulersOfAsgard/requests-consul/master/landscape.svg?style=flat)](https://landscape.io/github/RulersOfAsgard/requests-consul/master)

requests-consul is an extension for the
[requests](http://docs.python-requests.org/en/latest/) library.

It's implementing a custom transport adapter which connects to micro
services managed by [Consul](http://consul.io/)

## Example usage

```python
DC='datacenterX'
CONSUL_HOST = 'consul.mydomain'
CONSUL_PORT = 80
s = requests.Session()
s.mount('service://', ConsulServiceAdapter(dc=DC,
                                           host=CONSUL_HOST,
                                           port=CONSUL_PORT))
response = s.get('service://my_service/foo/bar')
```

## License

requests-consul is licensed under [Apache License, v2.0](https://github.com/RulersOfAsgard/requests-consul/blob/master/LICENSE).
