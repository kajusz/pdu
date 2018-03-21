#!/usr/bin/env python3

from flask import Flask, request, redirect, url_for
app = Flask(__name__)

# Define your pdus here
myPduConfig = (
    {'module':'AvocentPDU', 'ip':'192.168.0.1', 'user':'psuSnmp', 'auth':'authPriv', 'key':('1234567890abcdefghij', 'klmnopqrstuvwxyz1234'),},
    {'module':'ApcPDU', 'ip':'192.168.0.2', 'user':None, 'auth':None, 'key':None,},
)

import importlib

pdus = []
for pduDetails in myPduConfig:
    module = importlib.import_module(pduDetails['module'])
    pdu = getattr(module, pduDetails['module'])
    pdus.append(pdu(pduDetails['ip'], user=pduDetails['user'], auth=pduDetails['auth'], key=pduDetails['key']))

@app.route('/')
def mainPage():
    buf = '<DOCTYPE html><html><head><title>Advanced Power Distribution Management</title><style type="text/css"> span.on, span.off {font-weight:bold;} .on {color:green;} .off {color:red;}</style></head><body><h1>Advanced Power Distribution Management</h1><p>Lets turn things on and off!</p><ul>'
    for i in range(0, len(pdus)):
        ncvp  = pdus[i].getNCVP()
        buf2 = '<div><p>name = %s | current = %.1fA | voltage = %dV | power = %.1fW | <a href="/pdu%d/save">Save</a> | <a href="/pdu%d/set/all/on">all <span class="on">on</span></a> | <a href="/pdu%d/set/all/off">all <span class="off">off</span></a></p><ol>' % (*ncvp, i, i, i)

        olsc = pdus[i].getOLSC()
        for outlet, label, status, current in olsc:
            if pdus[i].currentPerOutlet and status == 'on':
                buf2 += '<li>%s is <span class="on">on</span> drawing %.1fA, <a href="/pdu%d/set/%d/off">power off</a></li>' % (label, current, i, outlet)
            else:
                invStatus = pdus[i].invert(status)
                buf2 += '<li>%s is <span class="%s">%s</span>, <a href="/pdu%d/set/%d/%s">power %s</a></li>' % (label, status, status, i, outlet, invStatus, invStatus)

        buf += buf2 + '</ol></div>'

    buf += '</ul></body></html>'
    return buf

@app.route('/pdu<int:pduId>/save')
def handlePduSave(pduId):
    pdus[pduId].save()
    return redirect(request.referrer)

@app.route('/pdu<int:pduId>/label/<int:outlet>/<string:label>')
def handlePduSetLabel(pduId, outlet, label):
    pdus[pduId].setLabel(outlet, label)
    return redirect(request.referrer)

@app.route('/pdu<int:pduId>/set/<int:outlet>/<string:status>')
def handlePduSetStatus(pduId, outlet, status):
    pdus[pduId].setStatus(outlet, status)
    return redirect(request.referrer)

@app.route('/pdu<int:pduId>/set/all/<string:status>')
def handlePduSetStatusAll(pduId, status):
    pdus[pduId].setStatusAll(status)
    return redirect(request.referrer)

@app.route('/pdu<int:pduId>/set/range/<int:start>/<int:end>/<string:status>')
def handlePduSetStatusRange(pduId, start, end, status):
    assert(start < end)
    for outlet in range(start, end+1):
        pdus[pduId].setStatus(outlet, status)
    return redirect(request.referrer)

if __name__ == '__main__':
    app.run()
