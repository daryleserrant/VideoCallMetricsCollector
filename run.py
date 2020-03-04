#!flask/bin/python
"""
Video Call Metrics Collector
Written By:  Daryle Serrant (daryle.serrant@gmail.com)
Description: Toy Application that collects video call metrics using the Daily.co API. By no means perfect,
             but gets the job done.
"""
from flask import Flask, abort, request, Response, redirect, url_for
from flask import render_template
import requests
import matplotlib.pyplot as plt
import configparser
import json
import os
from io import BytesIO
from datetime import datetime
import math
import sys

app = Flask(__name__)

# Get the base path of the file. We'll use this throughout the solution to reference
# application files.
BASE_PATH = os.path.dirname(__file__)
VIDEO_LOG_PATH = os.path.join(BASE_PATH,'video_logs')

config = configparser.ConfigParser()
config.read(os.path.join(BASE_PATH,'config.ini'))

API_KEY = config['DEFAULT']['DAILY_API_KEY']
call_stats = {}
meeting_room_url = None
participant_count = 0


def save_call_log():
    '''
    Function: save_call_log
    
    Description: This function saves the video call metrics data that was captured during
                 a video call.
    '''
    global call_stats
    global participant_count
    global meeting_room_url
    
    filename = datetime.fromtimestamp(call_stats['timestamp']).strftime('%Y_%m_%d_%H_%M_%S')+'.json'
    filepath = os.path.join(VIDEO_LOG_PATH,filename)
    
    with open(filepath,'w') as f:
        json.dump(call_stats, f)
    
    call_stats = {}
    participant_count = 0
    meeting_room_url = None
    
@app.route('/meeting/netlog',methods=['POST'])
def log_network_stats():
    '''
    Function: log_network_stats
    
    Description: This function captures video call metrics data sent from each client
                 during a video call. The metrics will be written to a JSON file later,
                 when the client navigates away from the video_call webpage. The format
                 of the data is as follows:
                 
                {'timestamp':<timestamp>,
                 'participants':[{'videoRecvBitsPerSecond':{<timestamp>:<value>},
                                  'videoSendBitsPerSecond':{<timestamp>:<value>},
                                  'videoRecvPacketLoss':{<timestamp>:<value>},
                                  'videoSendPacketLoss':{<timestamp>:<value>}}}
                 
    '''    
    global call_stats
    
    participant_log = {'videoRecvBitsPerSecond':{},
                       'videoSendBitsPerSecond':{},
                       'videoRecvPacketLoss':{},
                       'videoSendPacketLoss':{}}
    
    if request.json:
        payload = request.json
        
        if payload:
            if not call_stats:
               call_stats['timestamp'] = datetime.timestamp(datetime.now())
               call_stats['participants'] = []
            
            pid = payload['participant_id']
            
            stats = payload['netstats']['stats']['latest']
            
            if stats:
                timestamp = stats['timestamp']
                
                video_rcv_bps = math.floor(stats['videoRecvBitsPerSecond']/float(1000))
                video_snd_bps = math.floor(stats['videoSendBitsPerSecond']/float(1000))
                video_snd_pl = math.floor(stats['videoSendPacketLoss']*100)
                video_rcv_pl = math.floor(stats['videoRecvPacketLoss']*100)
                
                if pid >= len(call_stats['participants']):
                    call_stats['participants'].append(participant_log)
                    
                call_stats['participants'][pid]['videoRecvBitsPerSecond'][timestamp] = video_rcv_bps
                call_stats['participants'][pid]['videoSendBitsPerSecond'][timestamp] = video_snd_bps
                call_stats['participants'][pid]['videoSendPacketLoss'][timestamp] = video_snd_pl
                call_stats['participants'][pid]['videoRecvPacketLoss'][timestamp] = video_rcv_pl
            
            return Response(status=201)
    
    return abort(400)

@app.route('/videocall')
def render_video_call_page():
    '''
    Function: render_video_call_page
    
    Description: Renders the video call webpage where the meeting will be held
                 Client will be given a participant id that will be used for collecting metrics
                 on the video call.
    '''
    global participant_count
    
    if meeting_room_url:
        pid = participant_count
        invite_url = 'https://'+config['DEFAULT']['SERVER_NAME'] + '/videocall'
        participant_count+=1
        return render_template('video_call.html',
                               call_url=meeting_room_url,
                               invite_url=invite_url,
                               participant_id = pid)
    else:
        return "No meeting available"

@app.route('/new_meeting')
def create_meeting_room():
    '''
    Function: create_meeting_room
    
    Description: Creates a new video meeting and redirects user to the video call
                 page
    '''
    global meeting_room_url
    
    if len(call_stats) != 0:
        save_call_log()

    req_url = 'https://api.daily.co/v1/rooms'
    headers = {'authorization':'Bearer '+API_KEY}
    response = requests.post(req_url, headers=headers)
    meeting_room = json.loads(response.text)
    
    meeting_room_url = meeting_room['url']
    
    return redirect(url_for('render_video_call_page'))

@app.route('/videocalls/<string:entry>/metrics/plot.png')
def create_metrics_plot(entry):
    '''
    Function:    create_metrics_plot
    
    Description: This function returns a plot of the network statistics for a call that
                 happened in the past
                 
    Input:       entry - A video call log entry
    '''
    if len(call_stats) != 0:
        save_call_log()
    
    video_logs = []
    image = BytesIO()
    fname = entry+".json"
    
    video_logs = os.listdir(VIDEO_LOG_PATH)
    if fname in video_logs:
        call_logs = None
        fullpath = os.path.join(VIDEO_LOG_PATH,fname)
        with open(fullpath,'r') as f:
            call_logs = json.load(f)
        fig, axes = plt.subplots(nrows=4,ncols=1, figsize=(16, 10))
        
        plot_titles = ['videoRecvBitsPerSecond','videoSendBitsPerSecond','videoRecvPacketLoss',
                       'videoSendPacketLoss']
        plot_ylabels = ['kb/s','kb/s','percetage','percentage']
        
        maxlen = -sys.maxsize
        
        for i in range(len(call_logs['participants'])):
            for j in range(len(plot_titles)):
                
                tindex = list(call_logs['participants'][i][plot_titles[j]].keys())
                maxlen = max(maxlen, len(tindex))
                tvalues = list(call_logs['participants'][i][plot_titles[j]].values())
                axes[j].plot(range(len(tindex)),tvalues, label='Participant {0}'.format(i+1))
                axes[j].legend()
                
        for i in range(4):
            axes[i].set_title(plot_titles[i])
            axes[i].set_xlabel('Time in Seconds')
            axes[i].set_ylabel(plot_ylabels[i])
            axes[i].set_xticklabels([str(x) for x in range(0, 15*(maxlen+1),15)])

        axes[2].set_yticks(range(0,110,10), [str(x) for x in range(0,110,10)])
        axes[3].set_yticks(range(0,110,10), [str(x) for x in range(0,110,10)])
        plt.tight_layout()

        plt.savefig(image, transparent=True)
        
        return image.getvalue(), 200, {'Content-Type':'image/png'}
    else:
        return image.getvalue(), 404, {'Content-Type':'image/png'}
    
@app.route('/videocalls/<string:entry>/metrics')
def render_video_metrics_page(entry):
    '''
    Function: video_metrics
    
    Description: Renders the video metrics webpage where the client can
                 see plots of a prior video call.
    
    Input:       entry - A video log entry to plot
    '''
    if len(call_stats) != 0:
        save_call_log()
    
    return render_template('video_metrics.html',
                           log_entry=entry)

@app.route('/')
def render_main_page():
    '''
    Function: render_main_page
    
    Description: Renders the index page
    '''
    if len(call_stats) != 0:
        save_call_log()
    
    video_logs = [fname.split('.')[0] for fname in os.listdir(VIDEO_LOG_PATH)]
    
    return render_template('index.html',
                           video_calls = video_logs)

if __name__ == '__main__':
    if not os.path.isdir(VIDEO_LOG_PATH):
        os.mkdir(VIDEO_LOG_PATH)
        
    app.run(host=config['DEFAULT']['SERVER_HOST'],
            port=int(config['DEFAULT']['SERVER_PORT']),
            debug=bool(config['DEFAULT']['DEBUG_MODE']),
            ssl_context='adhoc')
