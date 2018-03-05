#!/usr/bin/env python3

import logging
log = logging.getLogger(__name__)

import pysnmp.hlapi.asyncore
snmpEngine = pysnmp.hlapi.SnmpEngine()

class simpleSnmp():
    def __init__(self, ip, tag='', port=161, userName=None, authKey=None, privKey=None, authProtocol=pysnmp.hlapi.usmNoAuthProtocol, privProtocol=pysnmp.hlapi.usmNoPrivProtocol, community='public'):
        if userName == None:
            self.authData = pysnmp.hlapi.CommunityData(community)
        else:
            self.authData = pysnmp.hlapi.UsmUserData(userName, authKey=authKey, privKey=privKey, authProtocol=authProtocol, privProtocol=privProtocol)
        self.transportTarget = pysnmp.hlapi.UdpTransportTarget((ip, port), timeout=1, retries=5, tagList=tag)
        self.contextData = pysnmp.hlapi.ContextData()

    def bulk(self, uoid):
        oid = ()
        if type(uoid) == list:
            for ioid in uoid:
                oid += (pysnmp.hlapi.ObjectType(pysnmp.hlapi.ObjectIdentity(ioid)),)
        else:
            oid = pysnmp.hlapi.ObjectType(pysnmp.hlapi.ObjectIdentity(uoid))

        b = pysnmp.hlapi.getCmd(snmpEngine, self.authData, self.transportTarget, self.contextData, *oid, lookupMib=False, lexicographicMode=False)
        return self.retMany(b)

    def get(self, uoid):
        oid = pysnmp.hlapi.ObjectIdentity(uoid)
        g = pysnmp.hlapi.getCmd(snmpEngine, self.authData, self.transportTarget, self.contextData, pysnmp.hlapi.ObjectType(oid), lookupMib=False, lexicographicMode=False)
        return self.retNext(oid, g)

    def next(self, uoid):
        oid = pysnmp.hlapi.ObjectType(pysnmp.hlapi.ObjectIdentity(uoid))
        n = pysnmp.hlapi.nextCmd(snmpEngine, self.authData, self.transportTarget, self.contextData, oid, lookupMib=False, lexicographicMode=False)
        return self.retMult(n)

    def set(self, uoid, type, val):
        if type == int:
            value = pysnmp.hlapi.Integer(val)
        elif type == str:
            value = pysnmp.hlapi.OctetString(val)

        oid = pysnmp.hlapi.ObjectIdentity(uoid)
        s = pysnmp.hlapi.setCmd(snmpEngine, self.authData, self.transportTarget, self.contextData, pysnmp.hlapi.ObjectType(oid, value), lookupMib=False, lexicographicMode=False)
        return self.retNext(oid, s)

    def retNext(self, oid, g):
        errorIndication, errorStatus, errorIndex, varBinds = next(g)

        if errorIndication:
            print(errorIndication)
        else:
            if errorStatus:
                print(errorStatus.prettyPrint(), 'at', errorIndex and varBinds[int(errorIndex)-1] or '?')
            else:
                for name, val in varBinds:
                    if name == oid:
                        return val

    def retMult(self, g):
        ret = []

        for (errorIndication, errorStatus, errorIndex, varBinds) in g:
            if errorIndication:
                print(errorIndication)
            else:
                if errorStatus:
                    print(errorStatus.prettyPrint(), 'at', errorIndex and varBinds[int(errorIndex)-1] or '?')
                else:
                    for name, val in varBinds:
                        ret.append((name, val))
        return ret

    def retMany(self, g):
        ret = []

        for (errorIndication, errorStatus, errorIndex, varBinds) in g:
            if errorIndication:
                print(errorIndication)
            else:
                if errorStatus:
                    print(errorStatus.prettyPrint(), 'at', errorIndex and varBinds[int(errorIndex)-1] or '?')
                else:
                    for name, val in varBinds:
                        ret.append((name, val))
        return ret
