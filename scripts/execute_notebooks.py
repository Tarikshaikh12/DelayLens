"""Execute every notebook in a real Jupyter kernel and preserve actual outputs."""
import argparse,json,os,sys
from pathlib import Path
import nbformat
from nbclient import NotebookClient
ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--in-process',action='store_true');args=parser.parse_args()
    spec=ROOT/'.jupyter/kernels/delaylens-review';spec.mkdir(parents=True,exist_ok=True)
    (spec/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],'display_name':'DelayLens verified Python','language':'python'}))
    os.environ['JUPYTER_PATH']=str(ROOT/'.jupyter')+os.pathsep+os.environ.get('JUPYTER_PATH','')
    results=[]
    for path in sorted((ROOT/'notebooks').glob('*.ipynb')):
        nb=nbformat.read(path,as_version=4)
        if args.in_process:
            from IPython.core.interactiveshell import InteractiveShell
            from IPython.utils.capture import capture_output
            InteractiveShell.clear_instance();shell=InteractiveShell.instance()
            count=0
            for cell in nb.cells:
                if cell.cell_type!='code':continue
                count+=1
                with capture_output(stdout=True,stderr=True,display=True) as captured:
                    result=shell.run_cell(cell.source,store_history=True)
                if result.error_before_exec or result.error_in_exec:
                    raise RuntimeError(f'{path.name} cell {count}: {result.error_before_exec or result.error_in_exec}')
                outputs=[]
                if captured.stdout:outputs.append(nbformat.v4.new_output('stream',name='stdout',text=captured.stdout))
                if captured.stderr:outputs.append(nbformat.v4.new_output('stream',name='stderr',text=captured.stderr))
                for rich in captured.outputs:
                    outputs.append(nbformat.v4.new_output('display_data',data=rich.data,metadata=rich.metadata))
                cell.outputs=outputs;cell.execution_count=count
        else:
            client=NotebookClient(nb,timeout=180,kernel_name='delaylens-review',resources={'metadata':{'path':str(ROOT)}})
            client.execute()
        nbformat.write(nb,path)
        results.append({'notebook':path.name,'runner':'IPython in-process' if args.in_process else 'Jupyter kernel','executed_code_cells':sum(c.cell_type=='code' for c in nb.cells),'error_outputs':sum(o.output_type=='error' for c in nb.cells if c.cell_type=='code' for o in c.outputs)})
        print('Executed',path.name,flush=True)
    (ROOT/'reports/review/notebook_execution.json').write_text(json.dumps(results,indent=2)+'\n')
if __name__=='__main__':main()
