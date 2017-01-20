#!/usr/bin/python
from flask import Flask, jsonify, request
import json
import datetime
import time

app = Flask(__name__)

OFFSET_KEY = 'offset'

max_offset = 100
offset_interval = 10
my_time = time.time() - 86400*30


@app.route('/ckpt/api/v1.0/events', methods=['GET','POST'])
def get_tasks():
    response = {
        'my_time':my_time,
        'events':[]
    }
    print 'req header:', request.headers
    print 'req raw data:', request.data
    body = {}
    if isinstance(request.data, basestring) and len(request.data) > 0:
        body = json.loads(request.data)
        print 'req body:', body
    offset = -1
    if OFFSET_KEY in request.headers:
        try:
            offset = int(request.headers[OFFSET_KEY])
        except:
            offset = 0
    elif OFFSET_KEY in body:
        offset = int(body[OFFSET_KEY])
    if offset < 0:
        raise ValueError('No offset in header or body')
    if offset < max_offset:
        for i in range(offset_interval):
            response['events'].append('this is event {}'.format(i + offset))
        response['next_offset'] = offset + offset_interval
    else:
        response['next_offset'] = offset

    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6111)
