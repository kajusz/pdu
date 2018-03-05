#!/usr/bin/env python3

from flask import Flask, redirect, url_for
app = Flask(__name__)

# Define your pdus here
ips = ('192.168.8.131',)

from avocent import AvocentPDU

pdus = []
for i in ips:
    pdus.append(AvocentPDU(i))

@app.route('/')
def mainPage():
    buf = '<DOCTYPE html><html><head><title>Advanced Power Distribution Management</title><style type="text/css"> span.on, span.off {font-weight:bold;} .on {color:green;} .off {color:red;}</style></head><body><h1>Advanced Power Distribution Management</h1><p>Lets turn things on and off!</p><ul>'
    for i in range(0, len(pdus)):
        ncvp  = pdus[i].getNCVP()
        buf2 = '<div><p>name = %s | current = %.1fA | voltage = %dV | power = %.1fW | <a href="/pdu%d/set/all/on">all <span class="on">on</span></a> | <a href="/pdu%d/set/all/off">all <span class="off">off</span></a></p><ol>' % (*ncvp, i, i)

        olsc = pdus[i].getOLSC()
        for outlet, label, status, current in olsc:
            if status == 'on':
                buf2 += '<li>%s is <span class="on">on</span> drawing %.1fA, <a href="/pdu%d/set/%d/off">power off</a></li>' % (label, current, i, outlet)
            elif status == 'off':
                buf2 += '<li>%s is <span class="off">off</span>, <a href="/pdu%d/set/%d/on">power on</a></li>' % (label, i, outlet)

        buf += buf2 + '</ol></div>'

    buf += '</ul></body></html>'
    return buf

@app.route('/pdu<int:pduId>/label/<int:outlet>/<string:label>')
def handlePduSetLabel(pduId, outlet, label):
    pdus[pduId].setLabel(outlet, label)
    return redirect(request.referrer)

@app.route('/pdu<int:pduId>/set/<int:outlet>/<string:status>')
def handlePduSetStatus(pduId, outlet, status):
    assert(status == 'on' or status == 'off')
    pdus[pduId].setStatus(outlet, status)
    return redirect(request.referrer)

@app.route('/pdu<int:pduId>/set/all/<string:status>')
def handlePduSetStatusAll(pduId, status):
    assert(status == 'on' or status == 'off')
    pdus[pduId].setStatusAll(status)
    return redirect(request.referrer)

@app.route('/pdu<int:pduId>/set/range/<int:start>/<int:end>/<string:status>')
def handlePduSetStatusRange(pduId, start, end, status):
    assert(status == 'on' or status == 'off')
    assert(start < end)
    for outlet in range(start, end+1):
        pdus[pduId].setStatus(outlet, status)
    return redirect(request.referrer)

if __name__ == '__main__':
    app.run()
