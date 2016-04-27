# python-rage4dns
Python bindings for RAGE4 DNS API

## How to Use
First, set your account email and API key as follows:

```
>>> import rage4
>>> rage4.USERNAME = "myname@mydomain.xyz"
>>> rage4.ACCT_KEY = "theAPIstringwouldgohere"
```

#### Get domain(s)
 - Get all domains: `rage4.get_domains()`
 - Get domain by ID (ex. ID 1): `rage4.get_domain(1)`
 - Get domain by name: `rage4.get_domain(name="mydomain.xyz")`

#### Add domain
Optional params for `add()` are NS1 and NS2. If not specified then the RAGE4 names will be used.
```
>>> domain = rage4.Domain("mydomain.xyz", "myname@mydomain.xyz")
>>> domain.add()
```

#### Delete domain
```
>>> domain = rage4.get_domain(name="mydomain.xyz")
>>> domain.delete()
```

#### Get DNS records for a domain
```
>>> domain = rage4.get_domain(name="mydomain.xyz")
>>> records = domain.get_records()
```

#### Add a DNS record to a domain
Params for the object: Name, content, record type, TTL and priority.
Optional params: `failover_enabled` and `failover_content`
Optional params for `add()`: `geo` and `active`. `geo` can either be a geocode (obtained from `rage4.get_geo_regions()`) or a tuple of latitude and longitude. Active defaults to `True`.
```
>>> domain = rage4.get_domain(name="mydomain.xyz")
>>> record = rage4.Record("www.mydomain.xyz", "127.0.0.1", rage4.RECORD_TYPES["A"],
...     3600, 1)
>>> domain.add_record(record)
```
