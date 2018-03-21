#!/usr/bin/env python3

import simplesnmp
import pysnmp.hlapi

SNMPv2SMIenterprises                    = (1,3,6,1,4,1,)

pmPowerMgmtSerialTableSave              = SNMPv2SMIenterprises+(10418,17,2,5,2,1,20,1,)

pmPowerMgmtPDUTablePduId                = SNMPv2SMIenterprises+(10418,17,2,5,3,1,3,1,1,)
pmPowerMgmtPDUTableCurrentValue         = SNMPv2SMIenterprises+(10418,17,2,5,3,1,50,1,1,)
pmPowerMgmtPDUTablePowerValue           = SNMPv2SMIenterprises+(10418,17,2,5,3,1,60,1,1,)
pmPowerMgmtPDUTableVoltageValue         = SNMPv2SMIenterprises+(10418,17,2,5,3,1,70,1,1,)

pmPowerMgmtTotalNumberOfOutlets         = SNMPv2SMIenterprises+(10418,17,2,5,4,0,)

pmPowerMgmtOutletsTableName             = SNMPv2SMIenterprises+(10418,17,2,5,5,1,4,)
pmPowerMgmtOutletsTableStatus           = SNMPv2SMIenterprises+(10418,17,2,5,5,1,5,)
pmPowerMgmtOutletsTablePowerControl     = SNMPv2SMIenterprises+(10418,17,2,5,5,1,6,)
pmPowerMgmtOutletsTableCurrentValue     = SNMPv2SMIenterprises+(10418,17,2,5,5,1,50,)

pmPowerMgmtOutletsTableStatusVal        = {'1':'off', '2':'on', '3':'offLocked', '4':'onLocked', '5':'offCycle', '6':'onPendingOff', '7':'offPendingOn', '8':'onPendingCycle', '9':'notSet', '10':'onFixed', '11':'offShutdown', '12':'tripped'}
pmPowerMgmtOutletsTablePowerControlVal  = {'1':'noAction', '2':'powerOn', '3':'powerOff', '4':'powerCycle', '5':'powerLock', '6':'powerUnlock'}
pmPowerMgmtOutletsTablePowerControlIVal = {'on':2, 'off':3}

import logging
log = logging.getLogger(__name__)

class AvocentPDU():
    def __init__(self, ip, user=None, auth=None, key=None):
        self.ip = ip
        authKey, privKey, authProtocol, privProtocol = None, None, None, None
        assert(auth in [None, 'authPriv', 'authNoPriv', 'noAuth'])
        if auth == 'authPriv':
            assert(type(key) == tuple)
            authKey = key[0]
            privKey = key[1]
            authProtocol=pysnmp.hlapi.usmHMACSHAAuthProtocol
            privProtocol=pysnmp.hlapi.usmDESPrivProtocol
        elif auth == 'authNoPriv':
            assert(type(key) == str)
            authKey = key
            privKey = None
            authProtocol=pysnmp.hlapi.usmHMACSHAAuthProtocol
            privProtocol=pysnmp.hlapi.usmNoPrivProtocol
        else:
            assert(key == None)
            authKey = None
            privKey = None
            authProtocol=pysnmp.hlapi.usmNoAuthProtocol
            privProtocol=pysnmp.hlapi.usmNoPrivProtocol

        self.snmp = simplesnmp.simpleSnmp(self.ip, userName=user, authKey=authKey, privKey=privKey, authProtocol=authProtocol, privProtocol=privProtocol)
        log.debug('%s get pmPowerMgmtTotalNumberOfOutlets', self.ip)
        self.total = int(self.snmp.get(pmPowerMgmtTotalNumberOfOutlets))

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
        log.debug('%s get pmPowerMgmtPDUTablePduId', self.ip)
        return str(self.snmp.get(pmPowerMgmtPDUTablePduId))

### Save
    def save(self):
        log.debug('%s set pmPowerMgmtSerialTableSave 2', self.ip)
        return self.snmp.set(pmPowerMgmtSerialTableSave, int, 2)

### Name, Current, Voltage, Power
    def getNCVP(self):
        log.debug('%s many pmPowerMgmtPDUTable[PduId, CurrentValue, VoltageValue, PowerValue]', self.ip)
        q = self.snmp.many([pmPowerMgmtPDUTablePduId, pmPowerMgmtPDUTableCurrentValue, pmPowerMgmtPDUTableVoltageValue, pmPowerMgmtPDUTablePowerValue])
        return (str(q[0][1]), float(q[1][1])/10, int(q[2][1]), float(q[3][1])/10)

### Current, Voltage, Power
    def getCVP(self):
        log.debug('%s many pmPowerMgmtPDUTable[CurrentValue, VoltageValue, PowerValue]', self.ip)
        q = self.snmp.many([pmPowerMgmtPDUTableCurrentValue, pmPowerMgmtPDUTableVoltageValue, pmPowerMgmtPDUTablePowerValue])
        return (float(q[0][1])/10, int(q[1][1]), float(q[2][1])/10)

### Label
    def getLabel(self, outletId):
        assert(outletId <= self.total)
        log.debug('%s get pmPowerMgmtOutletsTableName %d', self.ip, outletId)
        return str(self.snmp.get(pmPowerMgmtOutletsTableName+(1,1,outletId,)))

    def getLabelsAll(self):
        log.debug('%s next pmPowerMgmtOutletsTableName', self.ip)
        return self.snmp.next(pmPowerMgmtOutletsTableName)

    def setLabel(self, outletId, text):
        assert(outletId <= self.total)
        ## TODO: Check string is ascii
        log.debug('%s set pmPowerMgmtOutletsTableName %d', self.ip, outletId)
        return self.snmp.set(pmPowerMgmtOutletsTableName+(1,1,outletId,), str, text)

### Status
    def getStatus(self, outletId):
        assert(outletId <= self.total)
        log.debug('%s get pmPowerMgmtOutletsTableStatus %d', self.ip, outletId)
        return pmPowerMgmtOutletsTableStatusVal[str(self.snmp.get(pmPowerMgmtOutletsTableStatus+(1,1,outletId,)))]

    def getStatusAll(self):
        log.debug('%s next pmPowerMgmtOutletsTableStatus', self.ip)
        return self.snmp.next(pmPowerMgmtOutletsTableStatus)

    def setStatus(self, outletId, status):
        assert(outletId <= self.total)
        assert(status == 'on' or status == 'off')
        log.debug('%s set pmPowerMgmtOutletsTablePowerControl %d', self.ip, outletId)
        return self.snmp.set(pmPowerMgmtOutletsTablePowerControl+(1,1,outletId,), int, pmPowerMgmtOutletsTablePowerControlIVal[status])

    def setStatusAll(self, status):
        assert(status == 'on' or status == 'off')
        for i in range(1,self.total+1):
            self.setStatus(i, status)

### Current
    def getCurrent(self, outletId):
        assert(outletId <= self.total)
        log.debug('%s get pmPowerMgmtOutletsTableCurrentValue %d', self.ip, outletId)
        return float(self.snmp.get(pmPowerMgmtOutletsTableCurrentValue+(1,1,outletId,)))/10

    def getCurrentAll(self):
        log.debug('%s next pmPowerMgmtOutletsTableCurrentValue', self.ip)
        return self.snmp.next(pmPowerMgmtOutletsTableCurrentValue)

### WHAT?
    def getLS(self, outletId):
        assert(outletId <= self.total)
        log.debug('%s many pmPowerMgmtOutletsTable[Name, Status]', self.ip)
        ola = self.snmp.many([pmPowerMgmtOutletsTableName+(1,1,outletId), pmPowerMgmtOutletsTableStatus+(1,1,outletId)])
        return (str(ola[0][1]), pmPowerMgmtOutletsTableStatusVal[str(ola[1][1])])

    def getLSC(self, outletId):
        assert(outletId <= self.total)
        log.debug('%s many pmPowerMgmtOutletsTable[Name, Status, CurrentValue]', self.ip)
        ola = self.snmp.many([pmPowerMgmtOutletsTableName+(1,1,outletId), pmPowerMgmtOutletsTableStatus+(1,1,outletId), pmPowerMgmtOutletsTableCurrentValue+(1,1,outletId)])
        return (str(ola[0][1]), pmPowerMgmtOutletsTableStatusVal[str(ola[1][1])], float(ola[2][1])/10)

    def getOLS(self):
        ols = []
        log.debug('%s bulk pmPowerMgmtOutletsTable[Name, Status]', self.ip)
        olsc = self.snmp.bulk([pmPowerMgmtOutletsTableName, pmPowerMgmtOutletsTableStatus], self.total)
        for i in range(0, self.total*2, 2):
            ols.append((int(i/2), str(olsc[i][1]), pmPowerMgmtOutletsTableStatusVal[str(olsc[i+1][1])]))
        return ols

    def getOLSC(self):
        ols = []
        log.debug('%s bulk pmPowerMgmtOutletsTable[Name, Status, CurrentValue]', self.ip)
        olsc = self.snmp.bulk([pmPowerMgmtOutletsTableName, pmPowerMgmtOutletsTableStatus, pmPowerMgmtOutletsTableCurrentValue], self.total)
        for i in range(0, self.total*3, 3):
            ols.append((int(i/3), str(olsc[i][1]), pmPowerMgmtOutletsTableStatusVal[str(olsc[i+1][1])], float(olsc[i+2][1])))
        return ols

    def test(self):

        #([pmPowerMgmtOutletsTableName+(1,), pmPowerMgmtOutletsTableStatus+(1,), pmPowerMgmtOutletsTableCurrentValue+(1,)])

#        thing = [rfc1902.ObjectIdentifier(pmPowerMgmtPDUTablePduId), rfc1902.ObjectIdentifier(pmPowerMgmtPDUTableCurrentValue), rfc1902.ObjectIdentifier(pmPowerMgmtPDUTablePowerValue), rfc1902.ObjectIdentifier(pmPowerMgmtPDUTableVoltageValue)]
        import time
        start = time.time()
        olsc = self.getOLSC()
        for outlet, label, status, current in olsc:
            print(outlet, label, status, current)
        end = time.time()
        print(end - start)

        start = time.time()
        log.debug('%s bulk pmPowerMgmtOutletsTableName', self.ip)
        on = self.snmp.bulk(pmPowerMgmtOutletsTableName, self.total)
        log.debug('%s bulk pmPowerMgmtOutletsTableStatus', self.ip)
        os = self.snmp.bulk(pmPowerMgmtOutletsTableStatus, self.total)
        log.debug('%s bulk pmPowerMgmtOutletsTableCurrentValue', self.ip)
        oc = self.snmp.bulk(pmPowerMgmtOutletsTableCurrentValue, self.total)

        ols = []
        for i in range(0,self.total):
            ols.append((i+1, on[i][1], os[i][1], oc[i][1]))
        end = time.time()

        print(end - start)
#        return ols


        #print(olsc)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    pdu = AvocentPDU('192.168.254.51', user='tcap', auth='authPriv', key=('2KtsuaRKWWh1ip28X5RP', '6oYtL64RI9HqPoN99spn'))
    pdu.test()
