import paramiko
from typing import Tuple


class NsoSsh(object):
    def __init__(self):
        self.nso_ip = None
        self.nso_port = None
        self.username = None
        self.password = None
        self.ssh_client = None
        self.result_path = 'src/results'

    def setup_all(self, un, pw, ip, port):
        """
        setup credentials, connection, and connect to nso
        """
        self.setup_credentials(un=un, pw=pw)
        self.setup_connection(ip=ip, port=port)
        self.connect()

    def setup_credentials(self, un, pw) -> None:
        """
        assign user credentials to the NsoSsh Obj
        """
        self.username = un
        self.password = pw

    def setup_connection(self, ip, port) -> None:
        """
        assign connection details to the NsoSsh Obj
        """
        self.nso_ip = ip
        self.nso_port = port

    def connect(self) -> Tuple[int, dict]:
        """
        establish an ssh connection context to the nso server
        """
        if self.nso_ip is None or self.username is None or self.password is None:
            msg = 'connection and credentials not yet configured!'
            return 1, {'message': msg}

        try:
            # setup ssh connection
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(hostname=self.nso_ip, username=self.username, password=self.password)
            self.ssh_client = ssh_client
        except Exception as e:
            print('failed to establish ssh connection to nso')
            return 1, {'message': str(e)}
        print(f'ssh connection established with nso: {self.nso_ip}...')
        return 0, {'result': 'success'}

    def get_file_list(self, path) -> Tuple[int, dict]:
        """
        lookup the passed in path and perform an ls
        """
        try:
            # get file list
            _stdin, stdout, _stderr = self.ssh_client.exec_command(f'cd {path} && ls')
            output = [x.rstrip() for x in stdout.readlines()]
        except Exception as e:
            print(f'failed to execute command via ssh client: cd {path} && ls')
            return 1, {'message': str(e)}
        print(f'files in {path}: {output}')
        return 0, {'result': output}

    def delete_file(self, path, file_name) -> Tuple[int, dict]:
        """
        delete a file on the server
        """
        try:
            # delete a file
            if path[-1] != '/':
                path = path + '/'
            _stdin, _rm_stdout, _stderr = self.ssh_client.exec_command(f'rm -rf {path}{file_name}')
            _stdin, ls_stdout, _stderr = self.ssh_client.exec_command(f'cd {path} && ls')
            output = [x.rstrip() for x in ls_stdout.readlines()]
            if file_name in output:
                msg = f'failed to delete file: {file_name}'
                print(msg)
                return 1, {'message': msg}
        except Exception as e:
            msg = f'failed to delete file from server: {path}{file_name} {e}'
            print(msg)
            return 1, {'message': msg}
        print(f'file deleted: {path}{file_name}...')
        return 0, {'result': 'success'}

    def transfer_files(self, remote_path, file, desc=None) -> Tuple[int, dict]:
        """
        transfer file from server to test results path
        """
        try:
            if remote_path[-1] != '/':
                remote_path = remote_path + '/'

            # transfer files
            ftp_client = self.ssh_client.open_sftp()
            if desc is None:
                ftp_client.get(f'{remote_path}{file}', f'{self.result_path}/{file}')
            else:
                ftp_client.get(f'{remote_path}{file}', f'{self.result_path}/{desc}-{file}')
            ftp_client.close()
        except Exception as e:
            msg = f'failed to transfer file: {file} {e}'
            print(msg)
            return 1, {'message': msg}
        print(f'transfer file {file} success...')
        return 0, {}

    def disconnect(self) -> None:
        # cleanup connections
        self.ssh_client.close()

    def get_files(self, filenames, path, desc=None):
        return_code, result = self.get_file_list(path=path)
        for _file in filenames:
            if _file in result['result']:
                self.transfer_files(remote_path=path, file=_file, desc=desc)


if __name__ == '__main__':
    nso = NsoSsh()
