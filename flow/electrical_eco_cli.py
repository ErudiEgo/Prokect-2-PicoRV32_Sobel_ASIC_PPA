import click
from reader import click_odb
from electrical_eco import run
@click.command()
@click.option('--reference',required=True)
@click.option('--mode',type=click.Choice(['insert','cleanup','verify']),default='insert')
@click.option('--plan-only',is_flag=True)
@click_odb
def main(reader,reference,mode,plan_only):
 run(reader.block,mode,reference,'/design/eco_plan.json','/design/eco_pins.json',plan_only)
if __name__=='__main__':main()
