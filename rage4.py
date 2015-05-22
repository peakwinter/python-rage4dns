import base64
import json
import urllib2
import urlparse

from urllib import urlencode


USERNAME = ""
ACCT_KEY = ""

RECORD_TYPES = {
    "NS": 1,
    "A": 2,
    "AAAA": 3,
    "CNAME": 4,
    "MX": 5,
    "TXT": 6,
    "SRV": 7,
    "PTR": 8,
    "SPF": 9,
    "SSHFP": 10,
    "LOC": 11,
    "NAPTR": 12,
    1: "NS",
    2: "A",
    3: "AAAA",
    4: "CNAME",
    5: "MX",
    6: "TXT",
    7: "SRV",
    8: "PTR",
    9: "SPF",
    10: "SSHFP",
    11: "LOC",
    12: "NAPTR"
}


class Domain:
    def __init__(self, name, owner_email, id=0, type=0, subnet_mask=8):
        self.id = id
        self.name = name
        self.owner_email = owner_email
        self.type = type
        self.subnet_mask = subnet_mask

    def __repr__(self):
        return '<Domain %r>' % (self.name)

    def add(self, ns1=None, ns2=None):
        data = {"name": self.name, "email": self.owner_email}
        if ns1 and ns2:
            data["ns1"] = ns1
            data["ns2"] = ns2
        response = api("rapi/createregulardomain/", "POST", data)
        if not response["status"]:
            raise Exception("Domain creation failed: %s" % response["error"])
        self.id = response["id"]

    def add_with_vanity_ns(self, nsname, nsprefix):
        response = api("rapi/createregulardomainext/", "POST", {"name": self.name,
            "email": self.owner_email, "nsname": nsname, "nsprefix": nsprefix})
        if not response["status"]:
            raise Exception("Domain creation failed: %s" % response["error"])
        self.id = response["id"]

    def add_reverse_ipv4(self):
        response = api("rapi/createreversedomain4/", "POST", {"name": self.name,
            "email": self.owner_email, "subnet": self.subnet_mask})
        if not response["status"]:
            raise Exception("Domain creation failed: %s" % response["error"])
        self.id = response["id"]

    def add_reverse_ipv6(self):
        response = api("rapi/createreversedomain6/", "POST", {"name": self.name,
            "email": self.owner_email, "subnet": self.subnet_mask})
        if not response["status"]:
            raise Exception("Domain creation failed: %s" % response["error"])
        self.id = response["id"]

    def update(self, nsname="", nsprefix=""):
        response = api("rapi/updatedomain/%s" % str(self.id), "POST", {"name": self.name,
            "email": self.owner_email, "nsname": nsname, "nsprefix": nsprefix,
            "enablevanity": nsname and nsprefix})
        if not response["status"]:
            raise Exception("Domain update failed: %s" % response["error"])
        self.id = response["id"]

    def delete(self):
        response = api("rapi/deletedomain/%s" % str(self.id), "POST")
        if not response["status"]:
            raise Exception("Domain delete failed: %s" % response["error"])

    def get_zone(self):
        response = api("rapi/exportzonefile/", "GET", {"id": str(self.id)},
            returns="raw")
        return response

    def add_record(self, record, geo=False, active=True):
        record.add(geo, active, self.id)

    def get_records(self):
        response = api("rapi/getrecords/%s" % str(self.id), "GET")
        records = []
        for x in response:
            record = Record(x["name"], x["content"], x["type"], x["ttl"],
                x["priority"], x["id"], self.id, x["failover_enabled"],
                x["failover_content"])
            records.append(record)
        return records


class Record:
    def __init__(
            self, name, content, type, ttl, priority, id=0, domain_id=0,
            failover_enabled=False, failover_content=None):
        self.id = id
        self.name = name
        self.content = content
        self.type = type
        self.ttl = ttl
        self.priority = priority
        self.domain_id = domain_id
        self.failover_enabled = failover_enabled
        self.failover_content = failover_content

    def __repr__(self):
        return '<Record %s (%s)>' % (self.name, self.type)

    def add(self, geo=False, active=True, domain_id=0):
        if domain_id:
            self.domain_id = domain_id
        data = {"name": self.name, "content": self.content, "type": self.type,
            "priority": self.priority, "active": active, "ttl": self.ttl}
        if self.failover_enabled:
            data["failover"] = self.failover_enabled
            data["failovercontent"] = self.failover_content or ""
        if geo and type(geo) in [tuple, list]:
            data["geolock"] = True
            data["geolat"], data["geolong"] = geo
        elif geo:
            data["geolock"] = True
            data["geozone"] = geo
        else:
            data["geolock"] = False
        response = api("rapi/createrecord/%s" % str(self.domain_id), "POST", data)
        if not response["status"]:
            raise Exception("Record creation failed: %s" % response["error"])
        self.id = response["id"]

    def update(self, geo=False, active=True):
        data = {"name": self.name, "priority": self.priority, "active": active,
            "ttl": self.ttl}
        if self.failover_enabled:
            data["failover"] = self.failover_enabled
            data["failovercontent"] = self.failover_content or ""
        else:
            data["failover"] = False
        if geo and type(geo) in [tuple, list]:
            data["geolock"] = True
            data["geolat"], data["geolong"] = geo
        elif geo:
            data["geolock"] = True
            data["geozone"] = geo
        else:
            data["geolock"] = False
        response = api("rapi/updaterecord/%s" % str(self.id), "POST", data)
        if not response["status"]:
            raise Exception("Record update failed: %s" % response["error"])
        self.id = response["id"]

    def delete(self):
        response = api("rapi/deleterecord/%s" % str(self.id), "POST")
        if not response["status"]:
            raise Exception("Record delete failed: %s" % response["error"])

    def failover(self, active=True):
        data = {"active": active}
        response = api("rapi/setrecordfailover/%s" % str(self.id), "POST", data)
        if not response["status"]:
            raise Exception("Record failover update failed: %s" % response["error"])


def api(endpoint, method, params={}, returns="json", username=None, key=None):
    if not username:
        username = USERNAME
    if not key:
        key = ACCT_KEY
    if not username or not key:
        raise Exception("Username and account key must be declared")
    authstr = base64.encodestring('%s:%s' % (username, key)).replace('\n', '')
    if params:
        endpoint += "?%s" % urlencode([(x, params[x]) for x in params])
    request = urllib2.Request("https://secure.rage4.com/%s" % endpoint)
    if method != "GET":
        request.get_method = lambda: method
    request.add_header("Authorization", "Basic %s" % authstr)
    request.add_header("Content-Length", str(len(authstr)))
    response = urllib2.urlopen(request)
    if returns == "json":
        return json.loads(response.read())
    else:
        return response.read()

def get_domains():
    response = api("rapi/getdomains", "GET")
    domains = []
    for x in response:
        domain = Domain(x["name"], x["owner_email"], x["id"], x["type"], x["subnet_mask"])
        domains.append(domain)
    return domains

def get_domain(id=None, name=None):
    response = None
    if id:
        response = api("rapi/getdomain/%s" % str(id), "GET")
    elif name:
        response = api("rapi/getdomainbyname/", "GET", {"name": name})
    if response:
        return Domain(response["name"], response["owner_email"], response["id"],
            response["type"], response["subnet_mask"])

def get_geo_regions():
    response = api("rapi/listgeoregions/", "GET")
    return response
