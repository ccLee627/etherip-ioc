#!/usr/bin/python3
import argparse
import pandas
import logging
import os

from templates import cmd_template, ai_template, bi_template, bo_template

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

parser = argparse.ArgumentParser(description="Generate Sirius Ether IP - IOC.")

parser.add_argument('spreadsheet', help='Excel spreadsheet location.')
parser.add_argument('--plc-ip', required=True, dest='plc_ip', help='PLC IP.')
parser.add_argument('--plc-name', required=True, dest='plc_name', help='Name used to identify the PLC.')
parser.add_argument('--plc-module', required=True, dest='plc_module', help='Modulus of the variables to be archived in PLC.')

parser.add_argument('--sheet', required=True, help='Sheet name.')
parser.add_argument('--ioc-name', required=True, help='IOC name.')

parser.add_argument('--col-pv', default='EPICS', help='PV column name.')
parser.add_argument('--col-desc', default='Descrição', help='Desc column name.')
parser.add_argument('--col-tag', default='TAG', help='Desc column name.')
parser.add_argument('--col-inout', default='Input/Output', help='Input/Output column name.')
parser.add_argument('--col-dtype', default='Tipo de dado', help='Data type column name.')
parser.add_argument('--col-egu', default='EGU', help='EPICS egu column name.')

parser.add_argument('--epics-ca-server-port', default=5064, help='EPICS_CA_SERVER_PORT value.',
                    type=int)
parser.add_argument('--arch', choices=['linux-x86_64', 'linux-arm'], default='linux-x86_64',
                    help='System architecture.')

args = parser.parse_args()

logger.info('Args, {}.'.format(vars(args)))

path = os.path.dirname(os.path.abspath(__file__))

def generate(sheet):
    logger.info('Sheet: {}'.format(sheet.head()))
    logger.info('Generating {}.cmd file. At {}.'.format(args.ioc_name, path + '/../database'))
    
    with open(path + '/../iocBoot/' + args.ioc_name + '.cmd', 'w+') as f:
        f.write(cmd_template.safe_substitute(
            arch=args.arch,
            database=args.ioc_name,
            plc=args.plc_name,
            ip=args.plc_ip,
            epics_ca_server_port=args.epics_ca_server_port,
            module=args.plc_module
        ))
    tags = {}
    logger.info('Generating {}.db file. At {}.'.format(args.ioc_name, path + '/../database'))
    with open(path + '/../database/' + args.ioc_name + '.db', 'w+') as f:
        for pv, desc, tag, inout, dtype, egu in \
                zip(
                    sheet[args.col_pv],
                    sheet[args.col_desc],
                    sheet[args.col_tag],
                    sheet[args.col_inout],
                    sheet[args.col_dtype],
                    sheet[args.col_egu]
                ):

            if not tag or tag == '':
                logger.error('Tag not defined! {}'.format(pv))
                continue
            if tag == 'N/A':
                logger.warning('Tag not set! {}'.format(pv))
                continue
        
            if tag not in tags:
                tags[tag] = [pv]
            else:
                tags[tag].append(pv)
        
            if dtype == 'Digital':
                if inout == 'Input' or dtype == 'Control':
                    f.write(bi_template.safe_substitute(
                        pv=pv,
                        tag=tag,
                        desc=desc,
                        scan='1',
                        highname='True', 
                        lowname='False' 
                    ))
                else:
                # elif dtype == 'Output':
                    f.write(bo_template.safe_substitute(
                        pv=pv,
                        tag=tag,
                        desc=desc,
                        scan='1',
                        highname='True', 
                        lowname='False' 
                    ))
            elif dtype == 'Analog':
                if inout == 'Input':
                    f.write(ai_template.safe_substitute(
                        pv=pv,
                        tag=tag,
                        desc=desc,
                        scan='1',
                        prec='3',
                        egu=egu
                    ))
                else:
                # elif dtype == 'Output':
                    logger.warning('Type Analog Out Not - Supported {}.'.format(pv))

        for tag, vals in tags.items():
            if len(vals) > 1:
                logger.error('Tag {} already exist {}.'.format(tag, tags[tag]))
if __name__ == '__main__':
    sheet = pandas.read_excel(args.spreadsheet, sheet_name=args.sheet, dtype=str)
    sheet = sheet.replace('nan', '')
    generate(sheet) 

