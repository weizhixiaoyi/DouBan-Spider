import requests
import time
import json


def get_ip():
    targetUrl = "http://piping.mogumiao.com/proxy/api/get_ip_bs?appKey=c03bc78309b94c0c82154f88638d4bc6&count=10&expiryDate=0&format=1&newLine=2"
    response = requests.get(targetUrl)
    response_text = response.text
    response_json = json.loads(response_text)
    print(response)
    print(response_json)

    ip_list = []
    for info in response_json['msg']:
        ip = info['ip']
        port = info['port']
        ip_port = 'https://' + ip + ":" + port
        print(ip_port)
        ip_list.append(ip_port)

    ip_file_path = 'ip_list.txt'
    with open(ip_file_path, 'w') as f:
        for ip in ip_list:
            f.write(ip + '\n')


if __name__ == '__main__':
    while True:
        get_ip()
        time.sleep(60 * 2)
