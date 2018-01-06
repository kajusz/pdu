#!/usr/bin/env python3

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


from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.proto import rfc1902

class simpleSnmp():
    def __init__(self, ip, port, community):
        self.ip = ip
        self.port = port
        self.community = community

        self.authData = cmdgen.CommunityData(self.community)
        self.transportTarget = cmdgen.UdpTransportTarget((self.ip, self.port))

    def bulk(self, oids):
        ( errorIndication, errorStatus, errorIndex, varBinds ) = cmdgen.CommandGenerator().bulkCmd(
            self.authData,
            self.transportTarget,
            0, 25,
            *oids
        )
        if errorIndication:
            print(errorIndication)
        else:
            if errorStatus:
                print(errorStatus.prettyPrint(), 'at', errorIndex and varBinds[int(errorIndex)-1] or '?')
            else:
                ret = []
                print(type(varBinds))
                print(varBinds)
                for varBind in varBinds:
                    print(type(varBind))
                    print(varBind)
                    for name, val in varBind:
                        if str(name).startswith(str(oid)):
                            ret.append((name, str(val).split()))
                return ret

    def get(self, uoid):
        oid = rfc1902.ObjectIdentifier(uoid)

        ( errorIndication, errorStatus, errorIndex, varBinds ) = cmdgen.CommandGenerator().getCmd(
            self.authData,
            self.transportTarget,
            oid
        )
        if errorIndication:
            print(errorIndication)
        else:
            if errorStatus:
                print(errorStatus.prettyPrint(), 'at', errorIndex and varBinds[int(errorIndex)-1] or '?')
            else:
                print(type(varBinds))
                print(varBinds)
                for name, val in varBinds:
                    if name == oid:
                        return val

    def next(self, uoid):
        oid = rfc1902.ObjectIdentifier(uoid)

        ( errorIndication, errorStatus, errorIndex, varBinds ) = cmdgen.CommandGenerator().nextCmd(
            self.authData,
            self.transportTarget,
            oid
        )
        if errorIndication:
            print(errorIndication)
        else:
            if errorStatus:
                print(errorStatus.prettyPrint(), 'at', errorIndex and varBinds[int(errorIndex)-1] or '?')
            else:
                ret = []
                print(type(varBinds))
                print(varBinds)
                for varBind in varBinds:
                    print(type(varBind))
                    print(varBind)
                    for name, val in varBind:
                        if str(name).startswith(str(oid)):
                            ret.append((name, val))
                return ret

    def set(self, uoid, type, val):
        oid = rfc1902.ObjectIdentifier(uoid)

        if type == int:
            value = rfc1902.Integer(val)
        elif type == str:
            value = rfc1902.OctetString(val)

        errorIndication, errorStatus, errorIndex, varBinds = cmdgen.CommandGenerator().setCmd(
            self.authData,
            self.transportTarget,
            (oid, value)
        )
        if errorIndication:
            print(errorIndication)
        else:
            if errorStatus:
                print(errorStatus.prettyPrint(), 'at', errorIndex and varBinds[int(errorIndex)-1] or '?')
            else:
                print(type(varBinds))
                print(varBinds)
                for name, val in varBinds:
                    if name == oid:
                        return val

class AvocentPDU():
    def __init__(self, ip):
        self.ip = ip
        self.snmp = simpleSnmp(self.ip, 161, 'public')
        self.name = str(self.snmp.get(pmPowerMgmtPDUTablePduId))
        self.total = int(self.snmp.get(pmPowerMgmtTotalNumberOfOutlets)) + 1

    def save(self):
        return self.snmp.set(pmPowerMgmtSerialTableSave, int, 2)

    def getOidLabelStatus(self):
        status = self.getStatusAll()
        labels = self.getLabelsAll()
        ols = []
        for i, j in zip(labels, status):
            oid = i[0][-1]
            label = i[1]
            status = pmPowerMgmtOutletsTableStatusVal[j[1]]
            ols.append((oid, label, status))

        return ols

    def getOidLabelStatusCurrent(self):
        status = self.getStatusAll()
        labels = self.getLabelsAll()
        current = self.getCurrentAll()
        olsc = []
        for i, j, k in zip(labels, status, current):
            oid = int(i[0][-1])
            label = str(i[1])
            status = pmPowerMgmtOutletsTableStatusVal[str(j[1])]
            cur = float(k[1])/10
            olsc.append((oid, label, status, cur))

        return olsc

    def setLabel(self, outletId, text):
        return self.snmp.set(pmPowerMgmtOutletsTableName+(1,1,outletId,), str, text)

    def getLabelsAll(self):
        return self.snmp.next(pmPowerMgmtOutletsTableName)

    def getLabel(self, outletId):
        return str(self.snmp.get(pmPowerMgmtOutletsTableName+(1,1,outletId,)))

    def setStatusAll(self, status):
        for i in range(1,self.total):
            self.setStatus(i, status)

    def setStatus(self, outletId, status):
        return self.snmp.set(pmPowerMgmtOutletsTablePowerControl+(1,1,outletId,), int, pmPowerMgmtOutletsTablePowerControlIVal[status])

    def getStatusAll(self):
        return self.snmp.next(pmPowerMgmtOutletsTableStatus)

    def getStatus(self, outletId):
        return pmPowerMgmtOutletsTableStatusVal[str(self.snmp.get(pmPowerMgmtOutletsTableStatus+(1,1,outletId,)))]

    def getCurrentAll(self):
        return self.snmp.next(pmPowerMgmtOutletsTableCurrentValue)

    def getCurrent(self, outletId):
        return float(self.snmp.get(pmPowerMgmtOutletsTableCurrentValue+(1,1,outletId,)))/10

    def getName(self):
        return self.name

    def getCVP(self):
        ret = []
        ret.append(float(self.snmp.get(pmPowerMgmtPDUTableCurrentValue))/10)
        ret.append(int(self.snmp.get(pmPowerMgmtPDUTableVoltageValue)))
        ret.append(float(self.snmp.get(pmPowerMgmtPDUTablePowerValue))/10)
        return ret

    def invert(self, status):
        action = 1
        if status == 'on':
            action = 'off'
        elif status == 'off':
            action = 'on'
        return action

    def test(self):
#        thing = [rfc1902.ObjectIdentifier(pmPowerMgmtPDUTablePduId), rfc1902.ObjectIdentifier(pmPowerMgmtPDUTableCurrentValue), rfc1902.ObjectIdentifier(pmPowerMgmtPDUTablePowerValue), rfc1902.ObjectIdentifier(pmPowerMgmtPDUTableVoltageValue)]

        print(self.getCVP())

#        olsc = self.getOidLabelStatusCurrent()
#        print(olsc)
        status = self.getStatusAll()
        print(status)
        labels = self.getLabelsAll()
        print(labels)
        current = self.getCurrentAll()
        print(current)

        olsc = []
        for i, j, k in zip(labels, status, current):
            oid = int(i[0][-1])
            label = str(i[1])
            status = pmPowerMgmtOutletsTableStatusVal[str(j[1])]
            cur = float(k[1])/10
            olsc.append((oid, label, status, cur))

        print(olsc)

if __name__ == '__main__':
    pdu = AvocentPDU("172.21.1.140")
    pdu.test()
