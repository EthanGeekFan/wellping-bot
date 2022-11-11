import requests
import time
import datetime
import json
import random
from yaml import load, dump

# Set the request parameters
url_base = 'https://wellping.communitiesproject.stanfordsnl.org'
dashboard = '/ssnl_dashboard?username={username}&password={password}&device_id={device_id}&timezone_offset={toffset}&pings_completed_this_week={completed_pings}'
study_file = '/study_file?username={username}&password={password}&_={timestamp}'
upload = '/ssnl_upload?password={password}&device_id={device_id}&username={username}&patient_id={username}'

# Set the user credentials
username = 'bitabjln'
password = 'fZzpCl0vjxoH3hkGedJX_hDKyqXmMTSbowJSjKZ5BwY='
device_id = 'bitabjln-0fe0eda5-a416-4015-a793-40352bda7b17-1667015036559'
toffset = '420'


def timestamp():
    return str(int(time.time() * 1000))


def get_dashboard():
    url = url_base + dashboard.format(username=username, password=password,
                                      device_id=device_id, toffset=toffset, completed_pings=8)
    r = requests.get(url)
    return r.text


def get_study_file():
    url = url_base + \
        study_file.format(username=username,
                          password=password, timestamp=timestamp())
    r = requests.get(url)
    return r.text


def upload_file(json_data):
    url = url_base + \
        upload.format(username=username, password=password,
                      device_id=device_id)
    print(url)
    r = requests.post(url, json=json_data, headers={
        'Host': 'wellping.communitiesproject.stanfordsnl.org',
        'Content-Type': 'application/json',
        'wellping-jsversion': 'js.3.5.27.1',
        'User-Agent': 'WellPing/33 CFNetwork/1402 Darwin/22.2.0',
        'beiwe-api-version': '2',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-us,en;q=0.9',
        'Connection': 'keep-alive',
        'Accept': '*/*',
        'Content-Length': '2'
    })
    print(r.request.body)
    return r.text


def generate_response(dt=datetime.datetime.now()):
    timeslot = datetime_to_timeslot(dt)
    if timeslot is None or check_duplicate(timeslot):
        return None
    # add record to status
    status = read_status()
    status['history'].append(
        {'timeslot': timeslot, 'timestamp': dt.isoformat()[:-3] + 'Z'})
    with open('status.json', 'w') as f:
        json.dump(status, f, indent=4)
    sample = json.load(open('ssnl_upload.json'))
    notification_time = (dt -
                         datetime.timedelta(minutes=15)).isoformat()[:-3] + 'Z'
    start_time = (dt -
                  datetime.timedelta(minutes=10)).isoformat()[:-3] + 'Z'
    end_time = (dt -
                datetime.timedelta(minutes=0)).isoformat()[:-3] + 'Z'
    stream_name = 'sleepModalStream' if timeslot[-1:] == "0" else 'modalStream'
    print("Stream name: ", stream_name)
    sample['unuploadedPings'][0]['id'] = sample['unuploadedPings'][0]['id'][:-1] + str(
        int(sample['unuploadedPings'][0]['id'][-1]) + 1)
    sample['unuploadedPings'][0]['notificationTime'] = notification_time
    sample['unuploadedPings'][0]['startTime'] = start_time
    sample['unuploadedPings'][0]['endTime'] = end_time
    sample['unuploadedPings'][0]['streamName'] = stream_name

    answer_base_time = dt - datetime.timedelta(minutes=10)
    answer_time_step = datetime.timedelta(seconds=5)
    for i in range(0 if stream_name == "sleepModalStream" else 2, len(sample['unuploadedAnswers'])):
        sample['unuploadedAnswers'][i]['pingId'] = sample['unuploadedPings'][0]['id']
        sample['unuploadedAnswers'][i]['date'] = (
            answer_base_time + answer_time_step * i).isoformat()[:-3] + 'Z'
        if isinstance(sample['unuploadedAnswers'][i]['data']['value'], int) and not sample['unuploadedAnswers'][i]['questionId'].startswith('soc'):
            sample['unuploadedAnswers'][i]['data']['value'] = random.randint(
                0, 100)
        print("processing answer ", i, sample['unuploadedAnswers']
              [i]['questionId'], sample['unuploadedAnswers'][i]['date'])

    return sample


def read_status():
    with open('status.json') as f:
        return json.load(f)


def check_duplicate(timeslot):
    status = read_status()
    history = status['history']
    for h in history:
        if h['timeslot'] == timeslot:
            print("duplicate timeslot", timeslot)
            print("You have already submitted this timeslot")
            return True
    return False


def datetime_to_timeslot(datetime):
    '''
    Convert a datetime object to a timeslot string
    timeslots are in the format of YYYY-mm-dd-id
    id is index of 9:00-11:00, 13:00-15:00, 17:00-19:00, 21:00-23:00 intervals
    '''
    if datetime.hour >= 9 and datetime.hour < 11:
        id = 0
    elif datetime.hour >= 13 and datetime.hour < 15:
        id = 1
    elif datetime.hour >= 17 and datetime.hour < 19:
        id = 2
    elif datetime.hour >= 21 and datetime.hour < 23:
        id = 3
    else:
        print("invalid timeslot")
        return None
    return datetime.strftime('%Y-%m-%d') + '-' + str(id)


# print(upload_file())
# print(get_dashboard())
# print(upload_file(generate_response()))
# print(json.load(open('upload_response.json')))
print(generate_response())
