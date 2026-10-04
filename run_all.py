"""Run the full pipeline: experiments -> tables -> figures."""
import os, runpy
os.makedirs('results', exist_ok=True); os.makedirs('figures', exist_ok=True)
for script in ('experiments.py', 'tables.py', 'figs.py'):
    print(f'== {script}'); runpy.run_path(script, run_name='__main__')
