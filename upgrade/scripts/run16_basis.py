"""Check RUN16 RTL identity only. This is not a new ASIC sign-off or RGB test."""
import hashlib
from pathlib import Path
from evidence import sha

RUN16_COMMIT='e9ff741064810c1ce893745581a2d89917b0b238'
RUN16_BLOBS={
    'rtl/native_bus_arbiter.v':'5fd6eb974a0203a25757bb398064a75fcb6639bc',
    'rtl/picorv32_sobel_soc.v':'75a491960841e036814b0067f201480d3353a317',
    'rtl/sobel_core.v':'8b74596d5e12ec90f44964087c39d3aba8570c2c',
    'rtl/sobel_mmio.v':'239f38483e8787e6a97561a01f4feeec136aca61',
    'rtl/sobel_tile.v':'110a2b47be28e2c1335daf1f58ed2177c0ef6868',
    'third_party/picorv32/picorv32.v':'cc45fa998f1857b06a856ea59b931f6c37e06b34',
}

def validate_run16_rtl(root):
    files={}
    for name,blob in RUN16_BLOBS.items():
        p=root/name
        data=p.read_bytes().replace(b'\r\n',b'\n')
        digest=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if digest!=blob:
            raise ValueError(f'RTL differs from RUN16: {name}; reassess the physical basis')
        files[name]={'sha256':sha(p),'run16_git_blob_lf':blob}
    return {'status':'RTL_SOURCE_MATCH_ONLY','baseline_commit':RUN16_COMMIT,
            'baseline_run':'picorv32_sobel_dma_clk50_baseline_06','files':files,
            'limits':'Not an RGB functional/physical PASS. RUN16 retains one fanout violation; power is vectorless; external RAM excluded.'}

if __name__=='__main__':
    import json
    print(json.dumps(validate_run16_rtl(Path(__file__).resolve().parents[1]),indent=2))
