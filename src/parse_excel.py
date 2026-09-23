import argparse
def main():
 p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--db',required=True);p.parse_args(); print('Excel parsing is a source-specific adapter; use ingest_csv for normalized files.')
if __name__=='__main__':main()
