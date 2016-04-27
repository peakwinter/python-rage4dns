import base64
import json
try:
    # Python 3
    from urllib.request import urlopen, Request
    from urllib.parse import urlencode
except ImportError:
    # Python 2
    from urllib2 import urlopen, Request
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
        return '<Domain {0}>'.format(self.name)

    def add(self, ns1="ns35.r4ns.com", ns2="ns35.r4ns.net"):
        data = {"name": self.name, "email": self.owner_email}
        response = api("rapi/createregulardomain/", data)
        if not response["status"]:
            raise Exception("Domain creation failed: {0}".format(response["error"]))
        self.id = response["id"]

    def add_with_vanity_ns(self, nsname, nsprefix):
        response = api("rapi/createregulardomainext/", {"name": self.name,
            "email": self.owner_email, "nsname": nsname, "nsprefix": nsprefix})
        if not response["status"]:
            raise Exception("Domain creation failed: {0}".format(response["error"]))
        self.id = response["id"]

    def add_reverse_ipv4(self):
        response = api("rapi/createreversedomain4/", {"name": self.name,
            "email": self.owner_email, "subnet": self.subnet_mask})
        if not response["status"]:
            raise Exception("Domain creation failed: {0}".format(response["error"]))
        self.id = response["id"]

    def add_reverse_ipv6(self):
        response = api("rapi/createreversedomain6/", {"name": self.name,
            "email": self.owner_email, "subnet": self.subnet_mask})
        if not response["status"]:
            raise Exception("Domain creation failed: {0}".format(response["error"]))
        self.id = response["id"]

    def update(self, nsname="", nsprefix=""):
        response = api("rapi/updatedomain/{0}".format(self.id), {"name": self.name,
            "email": self.owner_email, "nsname": nsname, "nsprefix": nsprefix,
            "enablevanity": nsname and nsprefix})
        if not response["status"]:
            raise Exception("Domain update failed: {0}".format(response["error"]))
        self.id = response["id"]

    def delete(self):
        response = api("rapi/deletedomain/{0}".format(self.id))
        if not response["status"]:
            raise Exception("Domain delete failed: {0}".format(response["error"]))

    def get_zone(self):
        response = api("rapi/exportzonefile/", "GET", {"id": str(self.id)},
            returns="raw")
        return response

    def add_record(self, record, geo=False, active=True):
        record.add(geo, active, self.id)

    def get_records(self):
        response = api("rapi/getrecords/{0}".format(self.id))
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
        return '<Record {0} ({1})>'.format(self.name, self.type)

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
        response = api("rapi/createrecord/{0}".format(self.domain_id), data)
        if not response["status"]:
            raise Exception("Record creation failed: {0}".format(response["error"]))
        self.id = response["id"]

    def update(self, geo=False, active=True):
        data = {"name": self.name, "content": self.content, "priority": self.priority, "active": active,
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
        response = api("rapi/updaterecord/{0}".format(self.id), data)
        if not response["status"]:
            raise Exception("Record update failed: {0}".format(response["error"]))
        self.id = response["id"]

    def delete(self):
        response = api("rapi/deleterecord/{0}".format(self.id))
        if not response["status"]:
            raise Exception("Record delete failed: {0}".format(response["error"]))

    def failover(self, active=True):
        data = {"active": active}
        response = api("rapi/setrecordfailover/{0}".format(self.id), data)
        if not response["status"]:
            raise Exception("Record failover update failed: {0}".format(response["error"]))


def api(endpoint, params={}, returns="json", username=None, key=None):
    if not username:
        username = USERNAME
    if not key:
        key = ACCT_KEY
    if not username or not key:
        raise Exception("Username and account key must be declared")
    authstr = base64.encodestring('{0}:{1}'.format(username, key)).replace('\n', '')
    if params:
        endpoint += "?{0}".format(urlencode([(x, params[x]) for x in params]))
    request = Request("https://secure.rage4.com/{0}".format(endpoint))
    request.add_header("Authorization", "Basic {0}".format(authstr))
    response = urlopen(request)
    if returns == "json":
        return json.loads(response.read().encode("utf-8"))
    else:
        return response.read().encode("utf-8")

def get_domains():
    response = api("rapi/getdomains")
    domains = []
    for x in response:
        domain = Domain(x["name"], x["owner_email"], x["id"], x["type"], x["subnet_mask"])
        domains.append(domain)
    return domains

def get_domain(id=None, name=None):
    response = None
    if id:
        response = api("rapi/getdomain/{0}".format(id))
    elif name:
        response = api("rapi/getdomainbyname/", {"name": name})
    if response:
        return Domain(response["name"], response["owner_email"], response["id"],
            response["type"], response["subnet_mask"])

def get_geo_regions():
    response = api("rapi/listgeoregions/")
    return response
