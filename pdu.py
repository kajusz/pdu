#!/usr/bin/env python3

from flask import Flask, redirect, url_for
app = Flask(__name__)

#ips = ("192.168.254.51", "192.168.254.180", "192.168.254.220",)
ips = ('172.21.1.140',)

from avocent import AvocentPDU, simpleSnmp

pdus = []
for i in ips:
    pdus.append(AvocentPDU(i))

@app.route('/')
def index():
    buf = ''
    for i in range(0, len(pdus)):
        ncvp  = pdus[i].getNCVP()
        buf2 = '<div><p>name = %s | current = %.1fA | voltage = %dV | power = %.1fW | <a href="/pdu%d/set/all/on">all on</a> | <a href="/pdu%d/set/all/off">all off</a></p><ol>' % (*ncvp, i, i)

        olsc = pdus[i].getOLSC()
        for outlet, label, status, current in olsc:
            if status == 'on':
                buf2 += '<li>%s is %s drawing %.1fA, <a href="/pdu%d/set/%d/off">power off</a></li>' % (label, status, current, i, outlet)
            elif status == 'off':
                buf2 += '<li>%s is %s, <a href="/pdu%d/set/%d/on">power on</a></li>' % (label, status, i, outlet)

        buf += buf2 + '</ol></div>'

    return buf

@app.route('/pdu<int:pduId>/label/<int:outlet>/<string:label>')
def handlePduSetLabel(pduId, outlet, label):
    pdus[pduId].setLabel(outlet, label)
    return redirect(url_for('index'))

@app.route('/pdu<int:pduId>/set/<int:outlet>/<string:status>')
def handlePduSetStatus(pduId, outlet, status):
    assert(status == 'on' or status == 'off')
    pdus[pduId].setStatus(outlet, status)
    return redirect(url_for('index'))

@app.route('/pdu<int:pduId>/set/all/<string:status>')
def handlePduSetStatusAll(pduId, status):
    assert(status == 'on' or status == 'off')
    pdus[pduId].setStatusAll(status)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run()
