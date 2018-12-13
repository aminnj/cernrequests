from urllib.parse import urlparse, urljoin
from xml.etree import ElementTree

import requests

from cernrequests import certs


def _construct_certificate_authentication_url(login_redirect_url):
    query = urlparse(login_redirect_url).query
    certificate_authentication_part = "auth/sslclient/"
    base = urljoin(login_redirect_url, certificate_authentication_part)
    return "{}?{}".format(base, query)


def _extract_login_form(response_content):
    tree = ElementTree.fromstring(response_content)

    action = tree.findall("body/form")[0].get("action")
    form_data = dict(
        (
            (element.get("name"), element.get("value"))
            for element in tree.findall("body/form/input")
        )
    )

    return action, form_data


def get_sso_cookies(url, cert=None):
    """
    Based on https://github.com/cerndb/cern-sso-python

    :param url: URL of the CERN website you want to access
    :param cert: (certificate, key) tuple
    :return: CERN SSO cookie
    """
    ca_bundle = certs.where()
    with requests.Session() as session:
        session.cert = cert if cert else certs.default_user_certificate_paths()

        login_redirect_response = session.get(url, verify=ca_bundle)
        login_redirect_response.raise_for_status()

        redirect_url = login_redirect_response.url
        authentication_url = _construct_certificate_authentication_url(redirect_url)

        authentication_response = session.get(authentication_url, verify=ca_bundle)
        authentication_response.raise_for_status()

        action, form_data = _extract_login_form(authentication_response.content)
        session.post(url=action, data=form_data, verify=ca_bundle)

        return session.cookies
