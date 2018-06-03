#!/usr/bin/env python3

try:
    import simplesnmp
except ImportError:
    import pdu.simplesnmp as simplesnmp

import pysnmp.hlapi

SNMPv2SMIenterprises                    = (1,3,6,1,4,1,)
Avocent                                 = SNMPv2SMIenterprises+(10418,17,2,5) # Avocent + pm + pmManagement + pmPowerMgmt

pmPowerMgmtSerialTableSave              = Avocent+(2,1,20,1,)

pmPowerMgmtPDUTablePduId                = Avocent+(3,1,3,1,1,)
pmPowerMgmtPDUTableAlarm                = Avocent+(3,1,45,1,1)
pmPowerMgmtPDUTableCurrentValue         = Avocent+(3,1,50,1,1,)
pmPowerMgmtPDUTablePowerValue           = Avocent+(3,1,60,1,1,)
pmPowerMgmtPDUTableVoltageValue         = Avocent+(3,1,70,1,1,)

pmPowerMgmtTotalNumberOfOutlets         = Avocent+(4,0,)

pmPowerMgmtOutletsTableName             = Avocent+(5,1,4,)
pmPowerMgmtOutletsTableStatus           = Avocent+(5,1,5,)
pmPowerMgmtOutletsTablePowerControl     = Avocent+(5,1,6,)
pmPowerMgmtOutletsTableCurrentValue     = Avocent+(5,1,50,)

pmPowerMgmtOutletsTableStatusVal        = {'1':'off', '2':'on', '3':'offLocked', '4':'onLocked', '5':'offCycle', '6':'onPendingOff', '7':'offPendingOn', '8':'onPendingCycle', '9':'notSet', '10':'onFixed', '11':'offShutdown', '12':'tripped', }
pmPowerMgmtOutletsTablePowerControlVal  = {'1':'noAction', '2':'powerOn', '3':'powerOff', '4':'powerCycle', '5':'powerLock', '6':'powerUnlock', }
pmPowerMgmtOutletsTablePowerControlIVal = {'on':2, 'off':3, 'reboot':4, }

pmPowerMgmtPDUTableAlarmVal = {'1':'normal', '2':'blow-fuse', '3':'hw-ocp', '4':'high-critical', '5':'high-warning', '6':'low-warning', '7':'low-critical'}

pmPowerMgmtOutletsTableValidValues      = ['on', 'off', 'reboot']

def safecastInt(value, default=None):
    ret = None
    try:
        ret = int(value)
    except (ValueError, TypeError):
        ret = default
    finally:
        return ret

def safecastFloat(value, default=None):
    ret = None
    try:
        ret = float(value)
    except (ValueError, TypeError):
        ret = default
    finally:
        return ret


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

        try:
            log.debug('%s get pmPowerMgmtPDUTableAlarm', self.ip)
            alarm = self.snmp.get(pmPowerMgmtPDUTableAlarm)
            if (alarm != 1):
                log.error('%s has alarm %d = %s', self.ip, alarm, pmPowerMgmtPDUTableAlarmVal[str(alarm)])
        except:
            log.error('%s failed to connect to %s', self.ip, self.ip)

        log.debug('%s get pmPowerMgmtTotalNumberOfOutlets', self.ip)
        self.total = safecastInt(self.snmp.get(pmPowerMgmtTotalNumberOfOutlets), 0)

        self.currentPerOutlet = True
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
        log.debug('%s get pmPowerMgmtPDUTablePduId', self.ip)
        return str(self.snmp.get(pmPowerMgmtPDUTablePduId))

### Save
    def save(self):
        log.debug('%s set pmPowerMgmtSerialTableSave 2', self.ip)
        return self.snmp.set(pmPowerMgmtSerialTableSave, int, 2)

### Name, Status, Current, Voltage, Power
    def getNSCVP(self):
        log.debug('%s many pmPowerMgmtPDUTable[PduId, Alarm, CurrentValue, VoltageValue, PowerValue]', self.ip)
        q = self.snmp.many([pmPowerMgmtPDUTablePduId, pmPowerMgmtPDUTableAlarm, pmPowerMgmtPDUTableCurrentValue, pmPowerMgmtPDUTableVoltageValue, pmPowerMgmtPDUTablePowerValue])
        if q:
            return (str(q[0][1]), pmPowerMgmtPDUTableAlarmVal[str(q[1][1])], safecastFloat(q[2][1], -10.0)/10, safecastInt(q[3][1], -1), safecastFloat(q[4][1], -10.0)/10)
        else:
            return None

### Name, Current, Voltage, Power
    def getNCVP(self):
        log.debug('%s many pmPowerMgmtPDUTable[PduId, CurrentValue, VoltageValue, PowerValue]', self.ip)
        q = self.snmp.many([pmPowerMgmtPDUTablePduId, pmPowerMgmtPDUTableCurrentValue, pmPowerMgmtPDUTableVoltageValue, pmPowerMgmtPDUTablePowerValue])
        if q:
            return (str(q[0][1]), safecastFloat(q[1][1], -10.0)/10, safecastInt(q[2][1], -1), safecastFloat(q[3][1], -10.0)/10)
        else:
            return None

### Current, Voltage, Power
    def getCVP(self):
        log.debug('%s many pmPowerMgmtPDUTable[CurrentValue, VoltageValue, PowerValue]', self.ip)
        q = self.snmp.many([pmPowerMgmtPDUTableCurrentValue, pmPowerMgmtPDUTableVoltageValue, pmPowerMgmtPDUTablePowerValue])
        if q:
            return (safecastFloat(q[0][1], -10.0)/10, safecastInt(q[1][1], -1), safecastFloat(q[2][1], -10.0)/10)
        else:
            return None
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
        assert(status in pmPowerMgmtOutletsTableValidValues)
        log.debug('%s set pmPowerMgmtOutletsTablePowerControl %d', self.ip, outletId)
        return self.snmp.set(pmPowerMgmtOutletsTablePowerControl+(1,1,outletId,), int, pmPowerMgmtOutletsTablePowerControlIVal[status])

    def setStatusAll(self, status):
        assert(status in pmPowerMgmtOutletsTableValidValues)
        for i in range(1,self.total+1):
            self.setStatus(i, status)

### Current
    def getCurrent(self, outletId):
        assert(outletId <= self.total)
        log.debug('%s get pmPowerMgmtOutletsTableCurrentValue %d', self.ip, outletId)
        return safecastFloat(self.snmp.get(pmPowerMgmtOutletsTableCurrentValue+(1,1,outletId,)), -1.0)/10

    def getCurrentAll(self):
        log.debug('%s next pmPowerMgmtOutletsTableCurrentValue', self.ip)
        return self.snmp.next(pmPowerMgmtOutletsTableCurrentValue)

### Many params
    def getLS(self, outletId):
        assert(outletId <= self.total)
        log.debug('%s many pmPowerMgmtOutletsTable[Name, Status]', self.ip)
        ola = self.snmp.many([pmPowerMgmtOutletsTableName+(1,1,outletId), pmPowerMgmtOutletsTableStatus+(1,1,outletId)])
        if ola:
            return (str(ola[0][1]), pmPowerMgmtOutletsTableStatusVal[str(ola[1][1])])
        else:
            return None

    def getLSC(self, outletId):
        assert(outletId <= self.total)
        log.debug('%s many pmPowerMgmtOutletsTable[Name, Status, CurrentValue]', self.ip)
        ola = self.snmp.many([pmPowerMgmtOutletsTableName+(1,1,outletId), pmPowerMgmtOutletsTableStatus+(1,1,outletId), pmPowerMgmtOutletsTableCurrentValue+(1,1,outletId)])
        if ola:
            return (str(ola[0][1]), pmPowerMgmtOutletsTableStatusVal[str(ola[1][1])], safecastFloat(ola[2][1], -1.0)/10)
        else:
            return None

    def getOLS(self):
        ols = []
        log.debug('%s bulk pmPowerMgmtOutletsTable[Name, Status]', self.ip)
        olsc = self.snmp.bulk([pmPowerMgmtOutletsTableName, pmPowerMgmtOutletsTableStatus], self.total)
        if olsc:
            for i in range(0, self.total*2, 2):
                ols.append((int(1+i/2), str(olsc[i][1]), pmPowerMgmtOutletsTableStatusVal[str(olsc[i+1][1])]))
            return ols
        else:
            return None

    def getOLSC(self):
        ols = []
        log.debug('%s bulk pmPowerMgmtOutletsTable[Name, Status, CurrentValue]', self.ip)
        olsc = self.snmp.bulk([pmPowerMgmtOutletsTableName, pmPowerMgmtOutletsTableStatus, pmPowerMgmtOutletsTableCurrentValue], self.total)
        if olsc:
            for i in range(0, self.total*3, 3):
                ols.append((int(1+i/3), str(olsc[i][1]), pmPowerMgmtOutletsTableStatusVal[str(olsc[i+1][1])], safecastFloat(olsc[i+2][1], -1.0)/10))
            return ols
        else:
            return None
