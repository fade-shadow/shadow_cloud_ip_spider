#!/usr/bin/env python
# coding:utf-8
"""
@Time    : 2020/12/17 下午5:03
@Author  : Shadow
@Email   : 
@Software: PyCharm
"""
import json

import requests
from bs4 import BeautifulSoup


def get_cloud_ip_info(*search_keys):
    """
    爬取云ip并转换
    :param search_keys: 要搜索的关键字，可传入多个，如：Aliyun、Tencent cloud
    :return:
    """
    url = "https://bgp.he.net/search"
    headers = {
        'Connection': "keep-alive",
        'Cache-Control': "max-age=0",
        'DNT': "1",
        'Upgrade-Insecure-Requests': "1",
        'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36",
        'Sec-Fetch-Mode': "navigate",
        'Sec-Fetch-User': "?1",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        'Sec-Fetch-Site': "same-origin",
        'Referer': "https://bgp.he.net/cc",
        'Accept-Encoding': "gzip, deflate, br",
        'Accept-Language': "zh-CN,zh;q=0.9",
        'Cookie': "__utma=83743493.875054967.1571191220.1571191220.1571191220.1; __utmc=83743493; __utmz=83743493.1571191220.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); c=BAgiEzIxMC44My4yNDAuMTc4--35a94759c90411c56d1cb4d2ccc7635406aad645; _bgp_session=BAh7BjoPc2Vzc2lvbl9pZEkiJTQyMDc5NmEwMjEzMjYxMTgwYWFkY2IzZTY2N2Q3MWE2BjoGRUY%3D--a1439e2764d2221213a863c3951e693c6bc75b55,__utma=83743493.875054967.1571191220.1571191220.1571191220.1; __utmc=83743493; __utmz=83743493.1571191220.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); c=BAgiEzIxMC44My4yNDAuMTc4--35a94759c90411c56d1cb4d2ccc7635406aad645; _bgp_session=BAh7BjoPc2Vzc2lvbl9pZEkiJTQyMDc5NmEwMjEzMjYxMTgwYWFkY2IzZTY2N2Q3MWE2BjoGRUY%3D--a1439e2764d2221213a863c3951e693c6bc75b55; _bgp_session=BAh7BjoPc2Vzc2lvbl9pZEkiJTQyMDc5NmEwMjEzMjYxMTgwYWFkY2IzZTY2N2Q3MWE2BjoGRUY%3D--a1439e2764d2221213a863c3951e693c6bc75b55",
        'If-None-Match': "d2a3cd416366cb5595c8c436a73af375",
        'Postman-Token': "9a64bcf4-effc-4117-9783-c3084a3ea4a7,2cb5fae9-7afd-43c0-b862-1d44f98e6493",
        'Host': "bgp.he.net",
        'cache-control': "no-cache"
    }

    cloud_ip_dict = {}
    for search_key in search_keys:
        params = {
            "search[search]": search_key,
            "commit": "Search"
        }
        response = requests.request("GET", url, headers=headers, params=params)
        soup = BeautifulSoup(response.content, "html.parser")
        tr_list = soup.select("#search > table > tbody tr")
        del tr_list[0]  # 删除标题栏

        for tr_result in tr_list:
            ip_str = tr_result.select("td a")[0].text
            if ":" in ip_str or "/" not in ip_str:  # 忽略ipv6和非ipv4信息
                continue

            td_result = tr_result.select("td")[1]
            company = td_result.text.strip()
            # country = td_result.select("img")[0]["title"]

            # 转换
            ip_list = transform_cloud_ip(ip_str)

            if cloud_ip_dict.__contains__(company):
                cloud_ip_dict[company].extend(ip_list)
            else:
                cloud_ip_dict[company] = ip_list

    return cloud_ip_dict


def ip_bit_cala(ip_x, mask):
    a = (255 << mask) & 255  # "a<<b":a的各二进制位向左移动b位，高位丢弃，低位补0
    b = 1 << mask
    x = ip_x & a
    ip_x_list = [0] * b

    for i in range(b):
        ip_x_list[i] = x
        x += 1
    return ip_x_list


def transform_cloud_ip(ip_str):
    """
    将8.209.16.0/20 转化成 8.209.16.*、8.209.17.*、……的形式返回
    :param ip_str: ip+掩码数
    :return:
    """
    ip_and_mask = ip_str.split('/')
    mask = int(ip_and_mask[1])
    ip_str_list = ip_and_mask[0].split('.')

    ip_list = []

    if mask < 8:
        ip_x_list = ip_bit_cala(int(ip_str_list[0]), 8 - mask)
        for ip_x in ip_x_list:
            ip = str(ip_x) + ".*.*.*"
            ip_list.append(ip)
    elif mask == 8:
        ip = ip_str_list[0] + '.*.*.*'
        ip_list.append(ip)
    elif mask < 16:
        ip_x_list = ip_bit_cala(int(ip_str_list[1]), 16 - mask)
        for ip_x in ip_x_list:
            ip = ip_str_list[0] + '.' + str(ip_x) + ".*.*"
            ip_list.append(ip)
    elif mask == 16:
        ip = ip_str_list[0] + '.' + ip_str_list[1] + '.*.*'
        ip_list.append(ip)
    elif mask < 24:
        ip_x_list = ip_bit_cala(int(ip_str_list[2]), 24 - mask)
        for ip_x in ip_x_list:
            ip = ip_str_list[0] + '.' + ip_str_list[1] + '.' + str(ip_x) + ".*"
            ip_list.append(ip)
    elif mask == 24:
        ip = ip_str_list[0] + '.' + ip_str_list[1] + '.' + ip_str_list[2] + '.*'
        ip_list.append(ip)
    else:
        ip_x_list = ip_bit_cala(int(ip_str_list[3]), 32 - mask)
        for ip_x in ip_x_list:
            ip = ip_str_list[0] + '.' + ip_str_list[1] + '.' + ip_str_list[2] + '.' + str(ip_x)
            ip_list.append(ip)

    return ip_list


if __name__ == "__main__":
    with open("cloud_ip.json", "w") as fo:
        cloud_ip_dict = get_cloud_ip_info("Aliyun", '"Tencent cloud"', '"Huawei Public Cloud"')
        json.dump(cloud_ip_dict, fo, ensure_ascii=False)
