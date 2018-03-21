#!/usr/bin/env python3

import simplesnmp

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
    def __init__(self, ip):
        self.ip = ip
        self.snmp = simplesnmp.simpleSnmp(self.ip)
        #self.snmp = simpleSnmp(self.ip, userName='tcap', authKey='tP6gB2vzUmfewDHGEL0D', privKey='vAdnuDA2cEKnDVKUKuYw', authProtocol=pysnmp.hlapi.usmHMACSHAAuthProtocol, privProtocol=pysnmp.hlapi.usmDESPrivProtocol, community=None)
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
        return str(self.snmp.get(pmPowerMgmtPDUTablePduId))

### Save
    def save(self):
        log.info('set pmPowerMgmtSerialTableSave 2')
        return self.snmp.set(pmPowerMgmtSerialTableSave, int, 2)

### Name, Current, Voltage, Power
    def getNCVP(self):
        log.info('bulk pmPowerMgmtPDUTable[PduId, CurrentValue, VoltageValue, PowerValue]')
        q = self.snmp.bulk([pmPowerMgmtPDUTablePduId, pmPowerMgmtPDUTableCurrentValue, pmPowerMgmtPDUTableVoltageValue, pmPowerMgmtPDUTablePowerValue])
        return (str(q[0][1]), float(q[1][1])/10, int(q[2][1]), float(q[3][1])/10)

### Current, Voltage, Power
    def getCVP(self):
        log.info('bulk pmPowerMgmtPDUTable[CurrentValue, VoltageValue, PowerValue]')
        q = self.snmp.bulk([pmPowerMgmtPDUTableCurrentValue, pmPowerMgmtPDUTableVoltageValue, pmPowerMgmtPDUTablePowerValue])
        return (float(q[0][1])/10, int(q[1][1]), float(q[2][1])/10)

### Label
    def getLabel(self, outletId):
        assert(outletId <= self.total)
        log.info('get pmPowerMgmtOutletsTableName %d', outletId)
        return str(self.snmp.get(pmPowerMgmtOutletsTableName+(1,1,outletId,)))

    def getLabelsAll(self):
        log.info('next pmPowerMgmtOutletsTableName')
        return self.snmp.next(pmPowerMgmtOutletsTableName)

    def setLabel(self, outletId, text):
        assert(outletId <= self.total)
		## TODO: Check string is ascii
        log.info('set pmPowerMgmtOutletsTableName %d', outletId)
        return self.snmp.set(pmPowerMgmtOutletsTableName+(1,1,outletId,), str, text)

### Status
    def getStatus(self, outletId):
        assert(outletId <= self.total)
        log.info('get pmPowerMgmtOutletsTableStatus %d', outletId)
        return pmPowerMgmtOutletsTableStatusVal[str(self.snmp.get(pmPowerMgmtOutletsTableStatus+(1,1,outletId,)))]

    def getStatusAll(self):
        log.info('next pmPowerMgmtOutletsTableStatus')
        return self.snmp.next(pmPowerMgmtOutletsTableStatus)

    def setStatus(self, outletId, status):
        assert(outletId <= self.total)
        assert(status == 'on' or status == 'off')
        log.info('set pmPowerMgmtOutletsTablePowerControl %d', outletId)
        return self.snmp.set(pmPowerMgmtOutletsTablePowerControl+(1,1,outletId,), int, pmPowerMgmtOutletsTablePowerControlIVal[status])

    def setStatusAll(self, status):
        assert(status == 'on' or status == 'off')
        for i in range(1,self.total+1):
            self.setStatus(i, status)

### Current
    def getCurrent(self, outletId):
        assert(outletId <= self.total)
        log.info('get pmPowerMgmtOutletsTableCurrentValue %d', outletId)
        return float(self.snmp.get(pmPowerMgmtOutletsTableCurrentValue+(1,1,outletId,)))/10

    def getCurrentAll(self):
        log.info('next pmPowerMgmtOutletsTableCurrentValue')
        return self.snmp.next(pmPowerMgmtOutletsTableCurrentValue)

### WHAT?
    def getLS(self, outletId):
        assert(outletId <= self.total)
        ola = self.snmp.bulk([pmPowerMgmtOutletsTableName+(1,1,outletId), pmPowerMgmtOutletsTableStatus+(1,1,outletId)])
        return (str(ola[0][1]), pmPowerMgmtOutletsTableStatusVal[str(ola[1][1])])

    def getLSC(self, outletId):
        assert(outletId <= self.total)
        ola = self.snmp.bulk([pmPowerMgmtOutletsTableName+(1,1,outletId), pmPowerMgmtOutletsTableStatus+(1,1,outletId), pmPowerMgmtOutletsTableCurrentValue+(1,1,outletId)])
        return (str(ola[0][1]), pmPowerMgmtOutletsTableStatusVal[str(ola[1][1])], float(ola[2][1])/10)

    def getOLS(self):
        ols = []
        for i in range(1,self.total+1):
            ols.append((i,)+self.getLS(i))
        return ols

    def getOLSC(self):
        ols = []
        for i in range(1,self.total+1):
            ols.append((i,)+self.getLSC(i))
        return ols

    def test(self):
#        thing = [rfc1902.ObjectIdentifier(pmPowerMgmtPDUTablePduId), rfc1902.ObjectIdentifier(pmPowerMgmtPDUTableCurrentValue), rfc1902.ObjectIdentifier(pmPowerMgmtPDUTablePowerValue), rfc1902.ObjectIdentifier(pmPowerMgmtPDUTableVoltageValue)]
        import time
        start = time.time()
        olsc = self.getOidLabelStatusCurrent()
        end = time.time()
        print(end - start)
        print(olsc)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    pdu = AvocentPDU("172.21.1.140")
    pdu.test()
