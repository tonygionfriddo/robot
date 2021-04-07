import paramiko
import os
import datetime
from typing import Tuple


class NsoSshConnection:
    def __init__(self):
        self.nso_ip = None
        self.nso_port = None
        self.username = None
        self.password = None
        self.ssh_client = None
        self.result_path = None

    def setup_credentials(self, un, pw) -> None:
        self.username = un
        self.password = pw

    def setup_connection(self, ip, port) -> None:
        self.nso_ip = ip
        self.nso_port = port

    def setup_results_path(self) -> Tuple[int, dict]:
        """
        setup path for test results
        """
        print('creating test results directory...')
        todays_datetime = datetime.date.today()
        test_time = datetime.datetime.now()
        result_path = '../test_results/' \
                      f'{todays_datetime.month}-{todays_datetime.day}-{todays_datetime.year}_' \
                      f'{test_time.hour}:{test_time.minute}:{test_time.second}'

        try:
            os.mkdir('../test_results')
        except FileExistsError as e:
            if e.errno != 17:
                print(f'failed to create test result directory: {result_path}')
                return 1, {'message': str(e)}
        except Exception as e:
            print(f'failed to create test result directory: {result_path}')
            return 1, {'message': str(e)}

        try:
            os.mkdir(f'../test_results/{result_path}')
        except FileExistsError as e:
            if e.errno != 17:
                print(f'failed to create test result directory: {result_path}')
                return 1, {'message': str(e)}
        except Exception as e:
            print(f'failed to create test result directory: {result_path}')
            return 1, {'message': str(e)}
        print('test result directory created...')
        self.result_path = result_path
        print(f'result_path: {result_path}')
        return 0, {'result': result_path}

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
        try:
            # get file list
            _stdin, stdout, _stderr = self.ssh_client.exec_command(f'cd {path} && ls')
            output = [x.rstrip() for x in stdout.readlines()]
            print('existing nso log files:')
            print(output)
        except Exception as e:
            print(f'failed to execute command via ssh client: cd {path} && ls')
            return 1, {'message': str(e)}
        print('list files success...')
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
            msg = f'failed to remove file from server: {path}{file_name} {e}'
            print(msg)
            return 1, {'message': msg}
        print(f'delete file success: {path}{file_name}...')
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


if __name__ == '__main__':
    nso = NsoSshConnection()
