"""Synthetic objects only. No placement/router or real ODB edit."""
import tempfile
import json
from pathlib import Path
from types import SimpleNamespace
import electrical_eco as e


class Pin:
    def __init__(self, name, direction): self.name, self.direction = name, direction
    def getName(self): return self.name
    def getIoType(self): return self.direction


class Master:
    def __init__(self, name):
        self.name = name
        self.pins = {p: Pin(p, 'OUTPUT' if p == 'X' else 'INPUT') for p in ('A', 'X', *e.PG)}
    def getName(self): return self.name
    def findMTerm(self, p): return self.pins.get(p)


class Net:
    def __init__(self, name): self.name, self.terms, self.wire, self.guides = name, [], None, ['stale']
    def getName(self): return self.name
    def getITerms(self): return self.terms
    def getBTerms(self): return []
    def isSpecial(self): return self.name in e.PG
    def getSigType(self): return 'SIGNAL'
    def setSigType(self, x): pass
    def getWire(self): return self.wire
    def clearGuides(self): self.guides = []
    def getGuides(self): return self.guides


class Term:
    def __init__(self, inst, pin): self.inst, self.pin, self.net = inst, pin, None
    def getInst(self): return self.inst
    def getMTerm(self): return self.pin
    def getIoType(self): return self.pin.getIoType()
    def getNet(self): return self.net
    def isOutputSignal(self): return self.pin.name == 'X'
    def connect(self, n):
        if self.net: self.net.terms.remove(self)
        self.net = n; n.terms.append(self)


class Inst:
    def __init__(self, master, name):
        self.master, self.name, self.xy, self.orient, self.status = master, name, [0, 0], 'R0', 'PLACED'
        self.ts = {p: Term(self, v) for p, v in master.pins.items()}
    def getName(self): return self.name
    def getMaster(self): return self.master
    def findITerm(self, p): return self.ts.get(p)
    def getITerms(self): return list(self.ts.values())
    def getLocation(self): return self.xy
    def getOrient(self): return self.orient
    def setLocation(self, *x): self.xy = list(x)
    def setOrient(self, x): self.orient = x
    def setPlacementStatus(self, x): self.status = x
    def getPlacementStatus(self): return self.status
    def isFixed(self): return self.status == 'LOCKED'


class Block:
    def __init__(self):
        self.masters = {n: Master(n) for n in (e.MASTER, e.ROOT_MASTER)}
        self.insts, self.nets = {}, {}
    def getDataBase(self): return self
    def findMaster(self, n): return self.masters.get(n)
    def findInst(self, n): return self.insts.get(n)
    def findNet(self, n): return self.nets.get(n)
    def getInsts(self): return list(self.insts.values())
    def getBTerms(self): return []
    def getDbUnitsPerMicron(self): return 1000


def netcreate(b, n):
    x = Net(n); b.nets[n] = x; return x


def instcreate(b, m, n):
    x = Inst(m, n); b.insts[n] = x; return x


def fail(call):
    try: call()
    except ValueError: return
    raise AssertionError('Expected rejection did not occur')


original_odb = e.odb
e.odb = SimpleNamespace(dbInst=SimpleNamespace(create=instcreate), dbNet=SimpleNamespace(create=netcreate),
                       dbWire=SimpleNamespace(destroy=lambda w: None))
try:
    for count in (1, 2, 3, 4, 12, 24):
        b = Block(); n = netcreate(b, 'signal')
        driver = instcreate(b, b.findMaster(e.MASTER), 'driver'); driver.findITerm('X').connect(n)
        for pg in e.PG: driver.findITerm(pg).connect(netcreate(b, pg))
        for i in range(count):
            x = instcreate(b, b.findMaster(e.MASTER), 'load' + str(i))
            x.setLocation((i % 8)*120000+50000, (i // 8)*130000+30000)
            x.findITerm('A').connect(n)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); pins, manifest, ref = root/'pins.json', root/'plan.json', root/'ref.json'
            pins.write_text(json.dumps(['driver/X'])); rows = e.plan(b, ['driver/X'])
            manifest.write_text(json.dumps(rows))
            e.run(b, 'insert', ref, manifest, pins)
            assert driver.isFixed()
            assert len(n.getITerms()) == 2  # original driver now drives just the root buffer
            old = driver.getLocation()[:]
            driver.setLocation(1, 1)
            fail(lambda: e.run(b, 'cleanup', ref, manifest, pins))
            driver.setLocation(*old)
            branch = b.findInst(rows[0]['branches'][0]['buffer']); old_branch = branch.getLocation()[:]
            branch.setLocation(1000000, 1000000)
            fail(lambda: e.run(b, 'cleanup', ref, manifest, pins))
            branch.setLocation(*old_branch)
            e.run(b, 'cleanup', ref, manifest, pins)
            e.run(b, 'verify', ref, manifest, pins)
            assert not driver.isFixed() and driver.getPlacementStatus() == 'PLACED'
            assert not n.getGuides()
            assert all(not b.findNet(x['net']).getGuides() for x in rows[0]['branches'])
            assert b.findNet('VPWR').getGuides() == ['stale']
            b.findInst('load0').findITerm('A').connect(n)
            fail(lambda: e.run(b, 'verify', ref, manifest, pins))
            corrupted = json.loads(json.dumps(rows[0])); corrupted['branches'][0]['upstream'] = corrupted['branches'][-1]['net']
            fail(lambda: e.validate_tree(corrupted, ['load'+str(i)+'/A' for i in range(count)]))
finally:
    e.odb = original_odb
print('ECO SYNTHETIC EDIT REGRESSION PASS; tree coverage, cycles, locks, distances, cleanup, corruption')
