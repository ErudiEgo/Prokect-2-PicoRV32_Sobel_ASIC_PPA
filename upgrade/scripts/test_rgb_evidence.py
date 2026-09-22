"""Host-only checker regression using synthetic fixtures; never RTL evidence.
Temporary traces test acceptance/rejection only; no simulator, firmware or PPA run.
"""
import csv
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from evidence import golden, load_image, verify_mode
from prepare_image import write_input

class RGBContractTests(unittest.TestCase):
    def test_channels_are_independent(self):
        # Center impulse: all 8 neighbors have Sobel magnitude 80, center zero.
        plane=bytes([0,0,0,0,40,0,0,0,0])
        expected=bytes([80,80,80,80,0,80,80,80,80])
        self.assertEqual(golden(plane,3,3),expected)
        self.assertEqual(golden(plane+bytes(18),3,3,3),expected+bytes(18))
        self.assertEqual(golden(bytes(9)+plane+bytes(9),3,3,3),bytes(9)+expected+bytes(9))
        self.assertEqual(golden(bytes(18)+plane,3,3,3),bytes(18)+expected)
        self.assertEqual(golden(bytes([255])*9,3,3),bytes([255,255,255,255,0,255,255,255,255]))

    def test_input_rgb_limits_and_hashes(self):
        with tempfile.TemporaryDirectory() as t:
            d=Path(t)
            write_input(d/'max',256,256,bytes(256*256*3),{},3)
            self.assertEqual(len(load_image(d/'max')[1]),196608)
            with self.assertRaises(ValueError):
                write_input(d/'too_large',512,512,bytes(512*512*3),{},3)
            self.assertFalse((d/'too_large').exists())
            write_input(d/'gray',512,512,bytes(512*512),{})
            self.assertEqual(len(load_image(d/'gray')[1]),262144)
            (d/'max/image.hex').write_text('00\n')
            with self.assertRaises(ValueError): load_image(d/'max')

    def test_pillow_conversion_and_original(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow missing: needed only for imported images")
        with tempfile.TemporaryDirectory() as t:
            d=Path(t)
            src=Image.new('RGB',(3,1))
            src.putdata([(11,22,33),(44,55,66),(77,88,99)])
            src.save(d/'source.tiff')
            script=Path(__file__).with_name('prepare_image.py')
            subprocess.run([sys.executable,str(script),'--source',str(d/'source.tiff'),
                '--output',str(d/'rgb'),'--color','rgb'],check=True,capture_output=True)
            m,data=load_image(d/'rgb')
            self.assertEqual(data,bytes([11,44,77,22,55,88,33,66,99]))
            expected=b'P6\n3 1\n255\n'+bytes([11,22,33,44,55,66,77,88,99])
            self.assertEqual((d/'rgb/input.ppm').read_bytes(),expected)
            self.assertEqual((d/'rgb/original.ppm').read_bytes(),expected)
            again=subprocess.run([sys.executable,str(script),'--source',str(d/'source.tiff'),
                '--output',str(d/'rgb'),'--color','rgb'],capture_output=True)
            self.assertNotEqual(again.returncode,0)
            self.assertEqual(load_image(d/'rgb')[1],data)

    def trace(self,d,channels):
        # Small non-square shape with partial final tiles and byte-unaligned planes.
        w,h,tile=5,3,2
        data=bytes((i*7+c*31)%256 for c in range(channels) for i in range(w*h))
        expected=golden(data,w,h,channels)
        cycle=10; ps=[]; ts=[]
        for y in range(0,h,tile):
            for x in range(0,w,tile):
                for c in range(channels):
                    for yy in range(y,min(y+tile,h)):
                        for xx in range(x,min(x+tile,w)):
                            cycle+=1
                            sample=[cycle,xx,yy]+([c] if channels==3 else [])+[expected[c*w*h+yy*w+xx]]
                            ps.append(sample)
                cycle+=1; ts.append([cycle,x,y,min(tile,w-x),min(tile,h-y),len(ts)+1])
        e=dict(mode=1,width=w,height=h,tile=tile,memory_wait=1,pixels=w*h,tiles=len(ts),
               channels=channels,samples=w*h*channels,start_cycle=10,end_cycle=cycle+1,cycles=cycle-9)
        (d/'execution.json').write_text(json.dumps(e))
        self.write_csv(d/'pixels.csv',['cycle','x','y']+(['channel'] if channels==3 else [])+['value'],ps)
        self.write_csv(d/'tiles.csv',['cycle','x','y','width','height','ordinal'],ts)
        return expected,ps,ts

    def write_csv(self,p,header,items):
        with p.open('w',newline='') as f:
            writer=csv.writer(f);writer.writerow(header);writer.writerows(items)

    def test_evidence_contract(self):
        for channels in (1,3):
            with self.subTest(channels=channels), tempfile.TemporaryDirectory() as t:
                d=Path(t); expected,ps,ts=self.trace(d,channels)
                verify_mode(d,1,5,3,2,1,expected,channels)
                output=d/('output.ppm' if channels==3 else 'output.pgm')
                self.assertTrue(output.exists())
                if channels==3:
                    self.assertEqual(output.read_bytes(),b'P6\n5 3\n255\n'+bytes(expected[c*15+i] for i in range(15) for c in range(3)))
                # Premature completion of a tile (including missing blue output) must fail.
                ts[0][0]=ps[0][0]+1
                self.write_csv(d/'tiles.csv',['cycle','x','y','width','height','ordinal'],ts)
                with self.assertRaises(ValueError): verify_mode(d,1,5,3,2,1,expected,channels)

    def test_wrong_channel_and_pixel_rejected(self):
        for mutation in ('channel','value','duplicate','missing'):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as t:
                d=Path(t);expected,ps,ts=self.trace(d,3)
                if mutation=='channel': ps[0][3]=1
                if mutation=='value': ps[0][4]^=1
                if mutation=='duplicate': ps[1][1:4]=ps[0][1:4]
                if mutation=='missing': ps.pop()
                self.write_csv(d/'pixels.csv',['cycle','x','y','channel','value'],ps)
                with self.assertRaises(ValueError): verify_mode(d,1,5,3,2,1,expected,3)

if __name__=='__main__':
    unittest.main()
