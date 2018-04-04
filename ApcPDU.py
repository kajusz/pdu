#!/usr/bin/env python3

try:
    import simplesnmp
except ImportError:
    import pdu.simplesnmp as simplesnmp

import pysnmp.hlapi

SNMPv2SMIenterprises                    = (1,3,6,1,4,1,)
Apc                                     = SNMPv2SMIenterprises+(318,1,1,) # apc + products + hardware

sPDUMasterConfigPDUName                 = Apc+(4,3,3,0,)
rPDULoadStatusLoad                      = Apc+(12,2,3,1,1,2,1)
rPDUIdentDevicePowerWatts               = Apc+(12,1,16,0,)
rPDUIdentDeviceLinetoLineVoltage        = Apc+(12,1,15,0,)

sPDUOutletControlTableSize              = Apc+(4,4,1,0,)

sPDUOutletName                          = Apc+(4,5,2,1,3,)
sPDUOutletCtl                           = Apc+(4,4,2,1,3,)

sPDUOutletCtlVal                        = {'1':'on', '2':'off', '3':'outletReboot', '4':'outletUnknown', '5':'outletOnWithDelay', '6':'outletOffWithDelay', '7':'outletRebootWithDelay', }
sPDUOutletCtlIVal                       = {'on':1, 'off':2, 'reboot':3, }

sPDUMasterControlSwitch                 = Apc+(4,2,1,0,)

sPDUMasterControlSwitchVal              = {'1':'on', '2':'onSeq', '3':'off', '4':'reboot', '5':'rebootSeq', '6':'noCommand', '7':'offSeq', }
sPDUMasterControlSwitchIVal             = {'on':1, 'off':3, 'reboot':4, }

sPDUCtlValidValues                      = ['on', 'off', 'reboot']

import logging
log = logging.getLogger(__name__)

class ApcPDU():
    def __init__(self, ip, user=None, auth=None, key=None):
        self.ip = ip
        authKey, privKey, authProtocol, privProtocol = None, None, None, None
        assert(auth in [None, 'authPriv', 'authNoPriv', 'noAuth'])
        if auth == 'authPriv':
            assert(type(key) == tuple)
            authKey = key[0]
            privKey = key[1]
            authProtocol=pysnmp.hlapi.usmHMACDESAuthProtocol
            privProtocol=pysnmp.hlapi.usmDESPrivProtocol
        elif auth == 'authNoPriv':
            assert(type(key) == str)
            authKey = key
            privKey = None
            authProtocol=pysnmp.hlapi.usmHMACDESAuthProtocol
            privProtocol=pysnmp.hlapi.usmNoPrivProtocol
        else:
            assert(key == None)
            authKey = None
            privKey = None
            authProtocol=pysnmp.hlapi.usmNoAuthProtocol
            privProtocol=pysnmp.hlapi.usmNoPrivProtocol

        self.snmp = simplesnmp.simpleSnmp(self.ip, userName=user, authKey=authKey, privKey=privKey, authProtocol=authProtocol, privProtocol=privProtocol, community='private')
        log.debug('%s get sPDUOutletControlTableSize', self.ip)
        self.total = int(self.snmp.get(sPDUOutletControlTableSize))
        self.currentPerOutlet = False
        self.numberingStart = 1

### Invert
    def invert(self, status):
        action = 1
        if status == 'on':
            action = 'off'
        elif status == 'off':
            action = 'on'
        else:
            action = 'off'
        return action

### Name
    def getName(self):
        log.debug('%s get sPDUMasterConfigPDUName', self.ip)
        return str(self.snmp.get(sPDUMasterConfigPDUName))

### Name, Current, Voltage, Power
    def getNCVP(self):
        log.debug('%s many sPDUMasterConfigPDUName, rPDULoadStatusLoad, rPDULoadStatusLoad[LinetoLineVoltage, PowerWatts]', self.ip)
        q = self.snmp.many([sPDUMasterConfigPDUName, rPDULoadStatusLoad, rPDUIdentDeviceLinetoLineVoltage, rPDUIdentDevicePowerWatts])
        return (str(q[0][1]), float(q[1][1])/10, int(q[2][1]), float(q[3][1]))

### Current, Voltage, Power
    def getCVP(self):
        log.debug('%s many rPDULoadStatusLoad, rPDUIdentDevice[LinetoLineVoltage, PowerWatts]', self.ip)
        q = self.snmp.many([rPDULoadStatusLoad, rPDUIdentDeviceLinetoLineVoltage, rPDUIdentDevicePowerWatts])
        return (float(q[0][1])/10, int(q[1][1]), float(q[2][1]))

### Label
    def getLabel(self, outletId):
        assert(outletId <= self.total)
        log.debug('%s get sPDUOutletName %d', self.ip, outletId)
        return str(self.snmp.get(sPDUOutletName+(outletId,)))

    def getLabelsAll(self):
        log.debug('%s next sPDUOutletName', self.ip)
        return self.snmp.next(sPDUOutletName)

    def setLabel(self, outletId, text):
        assert(outletId <= self.total)
        assert(len(text) <= 20)
        log.debug('%s set sPDUOutletName %d', self.ip, outletId)
        return self.snmp.set(sPDUOutletName+(outletId,), str, text)

### Status
    def getStatus(self, outletId):
        assert(outletId <= self.total)
        log.debug('%s get sPDUOutletCtl %d', self.ip, outletId)
        return sPDUOutletCtlVal[str(self.snmp.get(sPDUOutletCtl+(outletId,)))]

    def getStatusAll(self):
        log.debug('%s next sPDUOutletCtl', self.ip)
        return self.snmp.next(sPDUOutletCtl)

    def setStatus(self, outletId, status):
        assert(outletId <= self.total)
        assert(status in sPDUCtlValidValues)
        log.debug('%s set sPDUOutletCtl %d %s %d', self.ip, outletId, status, sPDUOutletCtlIVal[status])
        return self.snmp.set(sPDUOutletCtl+(outletId,), int, sPDUOutletCtlIVal[status])

    def setStatusAll(self, status):
        assert(status in sPDUCtlValidValues)
        log.debug('%s set sPDUMasterControlSwitch %s %s', self.ip, status, sPDUMasterControlSwitchIVal[status])
        return self.snmp.set(sPDUMasterControlSwitch, int, sPDUMasterControlSwitchIVal[status])

### Many params
    def getLS(self, outletId):
        assert(outletId <= self.total)
        log.debug('%s many sPDUOutlet[Name, Ctl] %d', self.ip, outletId)
        ola = self.snmp.many([sPDUOutletName+(outletId), sPDUOutletCtl+(outletId)])
        return (str(ola[0][1]), sPDUOutletCtlVal[str(ola[1][1])])

    def getLSC(self, outletId):
        return self.getLS(outletId)+(0,)

    def getOLS(self):
        ols = []
        log.debug('%s bulk sPDUOutlet[Name, Ctl]', self.ip)
        olsc = self.snmp.bulk([sPDUOutletName, sPDUOutletCtl], self.total)
        for i in range(0, self.total*2, 2):
            ols.append((int(1+i/2), str(olsc[i][1]), sPDUOutletCtlVal[str(olsc[i+1][1])]))
        return ols

    def getOLSC(self):
        ols = []
        log.debug('%s bulk sPDUOutlet[Name, Ctl]', self.ip)
        olsc = self.snmp.bulk([sPDUOutletName, sPDUOutletCtl], self.total)
        for i in range(0, self.total*2, 2):
            ols.append((int(1+i/2), str(olsc[i][1]), sPDUOutletCtlVal[str(olsc[i+1][1])], 0))
        return ols
