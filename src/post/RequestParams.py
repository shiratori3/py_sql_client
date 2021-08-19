#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   prepare_post.py
@Author  :   Billy Zhou
@Time    :   2021/08/18
@Version :   1.6.0
@Desc    :   None
'''


import sys
import time
import datetime
import logging
import requests
from pathlib import Path
sys.path.append(str(Path(__file__).parents[2]))

from src.manager.ConfManager import cwdPath  # noqa: E402
from src.manager.ConfManager import conf  # noqa: E402


class RequestParams(object):
    def __init__(self, conf_path=cwdPath.joinpath('conf/post'), ) -> None:
        self.conf_path = Path(conf_path)

        self.url_dict = {}
        self.payload_curpage_dict = {}
        self.headers = ''
        self.payloads = {}

    def read_conf(self, conf_fname: str) -> None:
        conf_dict = conf.read_conf_from_file(self.conf_path.joinpath(conf_fname))
        logging.debug("conf_dict: %s", conf_dict)

        # update url_dict
        self.url_dict = conf_dict['url']

        # update size
        self.page_size = conf_dict['page']['size']

        # update headers
        conf_dict['headers']['gsid'] = conf_dict['cookie']['gsid']
        conf_dict['headers']['Authorization'] = 'Bearer ' + conf_dict['cookie']['token']
        self.headers = conf_dict['headers']

    def read_url(self, url_type: str, **params) -> str:
        if self.url_dict.get(url_type):
            return self.url_dict[url_type].format(timestamp=int(round(time.time() * 1000)), **params)
        else:
            logging.error("Unvaild url_type. Return blank url.")
            return ''

    def read_payload(self, payload_conf_fname: str, show_payload=False, no_page=False, day_range: list = []) -> None:
        self._payload_conf_dict = conf.read_conf_from_file(self.conf_path.joinpath(payload_conf_fname))

        # init
        self.payload_curpage_dict[payload_conf_fname] = 1
        logging.debug("payload_dict: %s", self._payload_conf_dict)

        # change params in conf
        self._update_payload_params(day_range=day_range)

        # convert dict to str
        self._payload_str = self._payload_dict2str(payload_conf_fname, no_page=no_page)
        if show_payload:
            logging.info("payload: %s", self._payload_str)

        # add to dict of payload
        self.payloads[payload_conf_fname] = self._payload_str

    def send_request(self, send_type: str, url, payload_from_conf: str = '', request_payloads: str = '', request_headers: str = '') -> dict or requests.Response:
        if send_type.upper() not in ['POST', 'GET']:
            raise ValueError('Invaild send_type[{}]. Please input POST or GET.'.format(send_type))

        headers = request_headers if request_headers else self.headers
        if payload_from_conf or request_payloads:
            payload_data = request_payloads if request_payloads else self.payloads[payload_from_conf]
            response = requests.request(
                send_type,
                url=url,
                headers=headers,
                data=payload_data
            )
        else:
            payload_data = ''
            response = requests.request(
                send_type,
                url=url,
                headers=headers
            )

        logging.debug("response.text: %s", response.text)
        try:
            response_jsondict = response.json()
            logging.info("response_msg: %s", response_jsondict['msg'])
            if response_jsondict['code'] != 200:
                logging.error("request failed.")
                logging.info("response.text[:1000]: %s", response.text[:1000])
                logging.info("url: %s", url)
                logging.info("headers: %s", headers)
                logging.info("payload: %s", payload_data)
            else:
                return response_jsondict
        except Exception:
            logging.error('The response body does not contain valid json. Return requests.Response')
            logging.error("response.text[:1000]: %s", response.text[:1000])
            logging.error("url: %s", url)
            logging.error("headers: %s", headers)
            logging.error("payload: %s", payload_data)
            return response

    def update_payload_page(self, payload_conf_fname: str, step: int = 1):
        logging.debug(self.payloads[payload_conf_fname])
        logging.debug(self.payload_curpage_dict[payload_conf_fname])
        self.payloads[payload_conf_fname] = self.payloads[payload_conf_fname].replace(
            '"current":' + str(self.payload_curpage_dict[payload_conf_fname]) + ',"',
            '"current":' + str(self.payload_curpage_dict[payload_conf_fname] + step) + ',"'
        )

    def _update_payload_params(self, day_range: list = []) -> None:
        if day_range:
            if self._payload_conf_dict['payload'].get('lastModifiedDateRange', None) is not None:
                logging.debug("datetime.datetime.utcnow(): %s", datetime.datetime.utcnow())
                utc_now = datetime.datetime.utcnow()
                if len(day_range) == 1:
                    s_delta = datetime.timedelta(days=day_range[0] - 1)
                    e_delta = datetime.timedelta(days=-1)
                else:
                    if len(day_range) > 2:
                        logging.warning('Too many arguments for day_range. Only available for the first two')
                    s_delta = datetime.timedelta(days=day_range[0] - 1)
                    e_delta = datetime.timedelta(days=day_range[1] - 1)
                s_date = utc_now + s_delta
                e_date = utc_now + e_delta
                logging.debug("s_date: %s", s_date.strftime('%Y-%m-%d') + 'T16:00:00.000Z')
                logging.debug("e_date: %s", e_date.strftime('%Y-%m-%d') + 'T16:00:00.000Z')
                self._payload_conf_dict['payload']['lastModifiedDateRange'] = [
                    s_date.strftime('%Y-%m-%d') + 'T16:00:00.000Z',
                    e_date.strftime('%Y-%m-%d') + 'T16:00:00.000Z',
                ]
                logging.info("lastModifiedDateRange: %s", self._payload_conf_dict['payload']['lastModifiedDateRange'])
            else:
                logging.warning('No lastModifiedDateRange in payload. Invaild day_range.')

    def _payload_dict2str(self, payload_conf_fname, no_page=False):
        logging.debug("payload_conf_dict: {0}".format(self._payload_conf_dict))
        payload_param = str(self._payload_conf_dict["payload"]).replace('\'', '"').replace(' ', '').replace('None', 'null').replace('False', 'false').replace('True', 'true')
        if no_page:
            return payload_param
        else:
            return '{"page":{"current":' + str(self.payload_curpage_dict[payload_conf_fname]) + ',"size":' + str(self.page_size) + "}," + payload_param[1:-1] + "}"


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(name)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    logging.debug('start DEBUG')
    logging.debug('==========================================================')

    request_params = RequestParams()
    request_params.read_conf('settings.yaml')
    logging.debug("headers: %s", request_params.headers)

    url = request_params.read_url('urlgetSql')
    logging.info("url: %s", url)

    request_params.read_payload('excel_uncheck.yaml', show_payload=True, no_page=False)
    request_params.read_payload('poolchange_juno_error_inner.yaml', show_payload=False, no_page=True)
    request_params.read_payload('excel_check_tan_latest.yaml', show_payload=False, no_page=False, day_range=[-1, 0])
    request_params.update_payload_page('excel_check_tan_latest.yaml', step=2)
    logging.info("payloads: %s", request_params.payloads)

    logging.debug('==========================================================')
    logging.debug('end DEBUG')