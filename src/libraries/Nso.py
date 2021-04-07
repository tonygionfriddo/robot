import requests
from requests.auth import HTTPBasicAuth
import json
import os
import xmltodict
from jinja2 import Template


class NsoLibs:
    def __init__(self, hostname, un, pw):
        self.hostname = hostname
        self.un = un
        self.pw = pw

    def get_device_list(self):
        """
        return a list of devices from the nso cdb
        :return:
        """
        error = {}
        device_list = []
        headers = {"Accept": "application/vnd.yang.collection+json"}
        r = requests.get(
            url=f'http://{self.hostname}:8080/api/running/devices/device',
            auth=HTTPBasicAuth(self.un, self.pw),
            headers=headers
        )
        print(r.status_code)
        print(r.text)
        if r.status_code == 200:
            response = json.loads(r.text)
            if len(response['collection']['tailf-ncs:device']) > 0:
                for _device in response['collection']['tailf-ncs:device']:
                    device_list.append(_device['name'])
        else:
            error = {
                'message': 'failed to retrieve device list'
            }
        return device_list, error

    def check_api_running(self):
        headers = {"Accept": "application/vnd.yang.datastore+json"}
        r = requests.get(
            url=f'http://{self.hostname}:8080/api/running/',
            auth=HTTPBasicAuth(self.un, self.pw),
            headers=headers
        )
        print(r.status_code)
        print(r.text)

    def compare_config(self, device):
        headers = {"Accept": "application/vnd.yang.data+json"}
        r = requests.post(
            url=f'http://{self.hostname}:8080/api/running/devices/device/{device}/_operations/compare-config',
            auth=HTTPBasicAuth(self.un, self.pw),
            headers=headers
        )
        print(r.status_code)
        print(r.text)
        if json.loads(r.text):
            response = json.loads(r.text)
            print(type(response))
            return 1, {'message': 'config diff found', 'config-diff': response['tailf-ncs:output']['diff']}
        else:
            return 0, {}

    def check_sync(self, device):
        headers = {"Accept": "application/vnd.yang.data+json"}
        r = requests.post(
            url=f'http://{self.hostname}:8080/api/running/devices/device/{device}/_operations/check-sync',
            auth=HTTPBasicAuth(self.un, self.pw),
            headers=headers
        )
        print(r.status_code)
        print(r.text)
        response = json.loads(r.text)
        if response['tailf-ncs:output']['result'] == 'out-of-sync':
            return 1, {'message': f'{device} is out of sync'}
        else:
            return 0, {'message': f'{device} is in sync'}

    def get_device_dict(self, device_name):
        error = {}
        headers = {"Accept": "application/vnd.yang.data+json"}
        r = requests.get(
            url=f'http://{self.hostname}:8080/api/running/devices/device/{device_name}',
            auth=HTTPBasicAuth(self.un, self.pw),
            headers=headers
        )
        if r.status_code != 200:
            error = {"message": "failed to get device data"}
            return {}, error
        else:
            return json.loads(r.text), error

    def check_api(self):
        headers = {"Accept": "application/vnd.yang.api+json"}
        r = requests.get(
            url=f'http://{self.hostname}:8080/api',
            auth=HTTPBasicAuth(self.un, self.pw),
            headers=headers
        )
        print(r.status_code)
        print(r.text)

    def check_api_operational(self):
        headers = {"Accept": "application/vnd.yang.datastore+json"}
        r = requests.get(
            url=f'http://{self.hostname}:8080/api/operational',
            auth=HTTPBasicAuth(self.un, self.pw),
            headers=headers
        )
        print(r.status_code)
        print(r.text)

    def get_packages(self):
        pkg_list = []
        error = {}
        headers = {"Accept": "application/vnd.yang.data+json"}
        r = requests.get(
            url=f'http://{self.hostname}:8080/api/operational/packages',
            auth=HTTPBasicAuth(self.un, self.pw),
            headers=headers
        )
        if r.status_code == 200:
            response = json.loads(r.text)
            for _pkg in response['tailf-ncs:packages']['package']:
                pkg_list.append(_pkg['name'])
        else:
            error = {
                'message': 'failed to retrieve package list'
            }
        return pkg_list, error

    def reload_packages(self):
        error = {}
        headers = {"Accept": "application/vnd.yang.data+json"}
        r = requests.post(
            url=f'http://{self.hostname}:8080/api/operational/packages/_operations/reload',
            auth=HTTPBasicAuth(self.un, self.pw),
            headers=headers
        )
        if r.status_code == 200:
            response = json.loads(r.text)
            for _result in response['tailf-ncs:output']['reload-result']:
                if _result['result'] != 'true':
                    error = {f"message': f'failed to reload package: {_result['package']}"}
                    return False, error
        return True, error

    def post_device_config(self, device_name, template, config):
        print(os.getcwd())
        path = f"{os.getenv('HOME')}/pytest-bdd/src/nso_bdd_test_pkg/xml/{template}"
        with open(path) as file:
            xml_data = xmltodict.parse(file.read())

        payload = xmltodict.unparse(xml_data)

        template = Template(payload)
        rendered_template = template.render(config=config)

        headers = {"Accept": "application/vnd.yang.datastore+xml"}
        r = requests.patch(
            url=f'http://{self.hostname}:8080/api/running/devices/device/{device_name}/config/',
            auth=HTTPBasicAuth(self.un, self.pw),
            headers=headers,
            data=rendered_template
        )

        if r.status_code != 204:
            print(rendered_template)
            print(r.status_code)
            print(r.text)
            return 1, {'message': 'error posting config'}

        return 0, {}

    def remove_device_trace(self, device_name, xml_file):
        print(os.getcwd())
        error = {}
        path = f"{os.getenv('HOME')}/pytest-bdd/src/nso_bdd_test_pkg/xml/{xml_file}"
        with open(path) as file:
            xml_data = xmltodict.parse(file.read())

        payload = xmltodict.unparse(xml_data)
        headers = {"Accept": "application/vnd.yang.data+json"}
        r = requests.patch(
            url=f'http://{self.hostname}:8080/api/running/devices/device/{device_name}/trace',
            auth=HTTPBasicAuth(self.un, self.pw),
            headers=headers,
            data=payload
        )
        if r.status_code == 400:
            response = xmltodict.parse(r.text)
            if response['errors']['error']['error-message'] == 'patch to a nonexistent resource':
                return 0, error
            else:
                error['message'] = response['errors']['error']['error-message']
                return 1, error
        elif r.status_code != 204:
            error = {"message": f"failed to remove device trace: {device_name}"}
            return 1, error
        return 0, error

    def install_device_trace(self, device_name, xml_file):
        error = {}
        path = f"{os.getenv('HOME')}/pytest-bdd/src/nso_bdd_test_pkg/xml/{xml_file}"
        with open(path) as file:
            xml_data = xmltodict.parse(file.read())

        payload = xmltodict.unparse(xml_data)
        headers = {"Accept": "application/vnd.yang.data+json"}
        r = requests.put(
            url=f'http://{self.hostname}:8080/api/running/devices/device/{device_name}/trace',
            auth=HTTPBasicAuth(self.un, self.pw),
            headers=headers,
            data=payload
        )
        if r.status_code != 204:
            error = {"message": f"failed to install device trace: {device_name}"}
            return 1, error

        return 0, error

    def sync_from_device(self, device_name):
        error = {}
        headers = {"Accept": "application/vnd.yang.data+json"}
        r = requests.post(
            url=f'http://{self.hostname}:8080/api/running/devices/device/{device_name}/_operations/sync-from',
            auth=HTTPBasicAuth(self.un, self.pw),
            headers=headers
        )
        if r.status_code != 200:
            error = {"message": f"failed to sync from device: {device_name}"}
            return 1, error
        else:
            response = json.loads(r.text)
            if str(response['tailf-ncs:output']['result']).lower() != 'true':
                error = {"message": f"failed to sync from device: {device_name}"}
                return 1, error
            else:
                return 0, error

    def get_device_config_dict(self, device_name, path):
        error = {}
        headers = {"Accept": "application/vnd.yang.data+json"}
        r = requests.get(
            url=f'http://{self.hostname}:8080/api/running/devices/device/{device_name}{path}',
            auth=HTTPBasicAuth(self.un, self.pw),
            headers=headers
        )
        if r.status_code != 200:
            error = {"message": "failed to get device data"}
            return {}, error
        else:
            return json.loads(r.text), error


if __name__ == '__main__':
    nso = NsoLibs(hostname='192.168.20.60', un='root', pw='dvrlab')
    if_config = { "interface_id": 2, "address": "86.1.1.1", "mask": "255.255.255.0"}
    nso.post_device_config(device_name='csr1000v', template='delete/interface_config.xml', config=if_config)


    """
    return_code, error = nso.compare_config(device='csr1000v')
    print(return_code)
    print(error)

    return_code, message = nso.check_sync(device='csr1000v')
    print(return_code)
    print(message)
    
    return_code, error = nso.compare_config()
    print(return_code)
    print(error)
    
    get device list
    device_list, error = nso.get_device_list()
    print(f'device_list: {device_list}')
    print(f'error: {error}')

    get package list
    pkg_list, error = nso.get_packages()
    print(f'pkg _list: {pkg_list}')
    print(f'error: {error}')
    
    result, error = nso.post_cisco_interface_config(device_name='csr1000v', xml_file='interface_config.xml')

    nso.install_device_trace(device_name='csr1000v', xml_file='set_trace.xml')
    device_data, error = nso.post_device_config(device_name='csr1000v', config_path='ios:native/interface/', xml_file='mtu_config.xml')
    print(device_data)
    
    result, error = nso.remove_device_trace(device_name='csr1000v', xml_file='remove_trace.xml')
    print(result)
    """
