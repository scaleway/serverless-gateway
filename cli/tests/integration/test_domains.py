import time

import pytest
from scaleway import ScalewayException
from scaleway.domain import v2beta1 as dom

from cli import client
from cli.infra import InfraManager

DOMAIN_ZONE = "scw.cloud"
SUBDOMAIN = "gateway-oss.fnc.dev.fr-par"
FULL_HOSTNAME = f"{SUBDOMAIN}.{DOMAIN_ZONE}"


class DomainManager:
    def __init__(self):
        self.scw_client = client.get_scaleway_client()
        self.domain = dom.DomainV2Beta1API(self.scw_client)

        self.org_id = self.scw_client.default_organization_id

    def get_dns_zone(self) -> dom.DNSZone:
        zones = self.domain.list_dns_zones_all(
            domain=DOMAIN_ZONE, dns_zone=DOMAIN_ZONE, project_id=self.org_id
        )

        matches = [z for z in zones if z.subdomain == SUBDOMAIN]
        if len(matches) != 1:
            pytest.fail(
                msg="Did not find a zone with subdomain {SUBDOMAIN}. Got: {zones}"
            )

        return matches[0]

    def add_cname_to_zone(self, cname_name: str, target: str):
        changes = [
            dom.RecordChange(
                add=dom.RecordChangeAdd(
                    records=[
                        dom.DomainRecord(
                            data=cname_name,
                            name=target,
                            priority=0,
                            ttl=600,
                            comment="Record for integration test",
                            type_=dom.DomainRecordType.CNAME,
                            geo_ip_config=None,
                            http_service_config=None,
                            weighted_config=None,
                            view_config=None,
                            id="",
                        )
                    ]
                ),
                set_=None,
                delete=None,
                clear=None,
            ),
        ]

        self.domain.update_dns_zone_records(
            dns_zone=FULL_HOSTNAME,
            changes=changes,
            disallow_new_zone_creation=True,
        )

    def get_cname_from_zone(self, cname_name: str):
        records = self.domain.list_dns_zone_records_all(
            dns_zone=FULL_HOSTNAME,
            name=cname_name,
            project_id=self.org_id,
        )

        if len(records) != 1:
            pytest.fail(f"Expected 1 DNS record, got {records}")

        return records[0]

    def delete_cname_from_zone(self, cname_name: str):
        zone = self.get_cname_from_zone(cname_name)

        changes = [
            dom.RecordChange(
                delete=dom.RecordChangeDelete(
                    id=zone.id,
                    id_fields=None,
                ),
                set_=None,
                add=None,
                clear=None,
            ),
        ]

        self.domain.update_dns_zone_records(
            dns_zone=FULL_HOSTNAME,
            changes=changes,
            disallow_new_zone_creation=True,
        )


def test_adding_domain():
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)
    endpoint = manager.get_gateway_endpoint()

    # Set up a new CNAME
    mgr = DomainManager()
    cname_name = "gateway-test"
    mgr.add_cname_to_zone(cname_name, endpoint)

    # Keep trying to add domain to the gateway, will take time to propagate and validate
    success = False
    exception = None
    for retry in range(5):
        time.sleep(10)
        try:
            container_hostname = f"{cname_name}.{FULL_HOSTNAME}"
            manager.add_custom_domain(container_hostname)

            success = True
            break
        except ScalewayException as e:
            exception = e

    if not success:
        raise exception

    # TODO - make a request

    # Remove the domain from the gateway
    # manager.delete_custom_domain(FULL_HOSTNAME)

    # Delete the CNAME
    # mgr.delete_cname_from_zone(cname_name)
