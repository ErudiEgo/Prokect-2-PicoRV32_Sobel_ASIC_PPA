import json,click
from pathlib import Path
from reader import click_odb
from route_guard import check
@click.command()
@click.option('--reference',required=True)
@click.option('--report',required=True)
@click.option('--mode',type=click.Choice(['input','routed','antenna']),required=True)
@click.option('--diode-cell',required=True)
@click.option('--diode-pin',required=True)
@click_odb
def main(reader,reference,report,mode,diode_cell,diode_pin):
 result=check(reader.block,json.loads(Path(reference).read_text()),mode,diode_cell,diode_pin)
 Path(report).write_text(json.dumps(result,indent=2)+'\n')
 print('H3_ROUTE_GUARD_PASS',mode)
if __name__=='__main__':main()
