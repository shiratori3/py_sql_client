#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   conn_info.py
@Author  :   Billy Zhou
@Time    :   2021/03/01
@Version :   1.0.0
@Desc    :   None
'''


import logging
import json
from pathlib import Path


from basic.input_check import input_default
from basic.input_check import input_pwd
from basic.input_check import input_checking_YN
from basic.RSA_encrypt import CheckRSAKeys
from basic.RSA_encrypt import Encrypt
from basic.RSA_encrypt import Decrypt


def check_conn_info(conn_name, encrypt=False,
                    pubkeyfile='', prikeyfile=''):
    # encrypt and prepare keys
    if encrypt and not (pubkeyfile and prikeyfile):
        CheckRSAKeys()

    # git上传忽略对应文件
    with open(Path.cwd().joinpath('.gitignore'), 'a+', encoding='utf-8') as f:
        rsa_ignore = False
        f.seek(0, 0)  # back to the start
        for i in f.readlines():
            logging.debug(i.replace('\n', ''))
            if i.replace('\n', '') in ['/gitignore/', '/gitignore/conn/']:
                rsa_ignore = True
                break
        if not rsa_ignore:
            f.write('\n/gitignore/conn/\n')

    # get dict of connection info
    conn_path = Path.cwd().joinpath('gitignore\\conn')
    json_path = conn_path.joinpath('conn_info.json')
    connfile_path = conn_path.joinpath(conn_name + '.txt')
    if not conn_path.exists():
        Path.mkdir(conn_path, parents=True)
    if not json_path.exists():
        with open(json_path, 'w') as f:
            json.dump({}, f)
    with open(json_path) as f:
        data = f.read()
        if data:
            conn_dict = json.loads(data)
        else:
            conn_dict = {}

    # connection called conn_name exist or not
    if not conn_dict.get(conn_name):
        print('Connection not exist. Creating a new connection')
        conn_info = create_conn_info(conn_name, encrypt, pubkeyfile)
        if connfile_path.exists():
            conn_dict[conn_name] = str(connfile_path.resolve())
    else:
        print('Opening existing connection.')
        with open(conn_dict[conn_name]) as file_obj:
            if encrypt and prikeyfile:
                data = Decrypt(prikeyfile, file_obj.read())
            else:
                data = file_obj.read()
        logging.debug('data: %s', data)
        conn_info = json.loads(data)

    with open(json_path, 'w') as f:
        json.dump(conn_dict, f)

    logging.debug(conn_dict)
    logging.debug(conn_info)
    return conn_info


def create_conn_info(conn_name, encrypt=False, pubkeyfile=''):
    host = input_default(input('Please input host: '), 'localhost')
    database = input_default(input('Please input database: '), 'master')
    username = input_default(input('Please input username: '), 'sa')
    pwd = input_pwd().strip()

    conn_info = {
        'host': host,
        'user': username,
        'database': database,
        'pwd': pwd,
    }
    logging.debug(conn_info)

    if input_checking_YN('Save the connection into file?') == 'Y':
        print('Saving connection to ' + conn_name + '.txt')
        conn_path = Path.cwd().joinpath('gitignore\\conn')
        connfile_path = conn_path.joinpath(conn_name + '.txt')
        with open(connfile_path, 'w') as file_obj:
            if encrypt and pubkeyfile:
                file_obj.write(Encrypt(pubkeyfile, json.dumps(conn_info)))
            else:
                json.dump(conn_info, file_obj)
    else:
        print('Unsave.')
    return conn_info


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(name)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    logging.debug('start DEBUG')
    logging.debug('==========================================================')

    # conn = check_conn_info()

    pubkeyfile = Path.cwd().joinpath('gitignore\\rsa\\public.pem')
    prikeyfile = Path.cwd().joinpath('gitignore\\rsa\\private.pem')
    conn = check_conn_info(
            'localhost', encrypt=True,
            pubkeyfile=pubkeyfile, prikeyfile=prikeyfile)

    logging.debug('==========================================================')
    logging.debug('end DEBUG')
