"""Build manuscript text, citation sources and an assignment-bound figure offline."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def tex(text):
    return text.replace('&', r'\&').replace('%', r'\%').replace('_', r'\_').replace('$', r'\$')

def produce():
    from build_principal_tables import produce as principal_tables
    table_outputs = principal_tables(ROOT)
    table_content = __import__("json").loads(table_outputs["principal_tables.json"])
    source = (HERE / 'manuscript_source.md').read_text()
    for marker, content in table_content['tables'].items():
        assert source.count('{{'+marker+'}}') == 1, marker
        source = source.replace('{{'+marker+'}}', content)
    refs = json.loads((HERE / 'manuscript_references.json').read_text())
    tables = json.loads((HERE / 'results_tables.json').read_text())
    audit = json.loads((HERE / 'policy_audit/evidence_audit/summary.json').read_text())
    assert tables['collection']['live_assigned'] == 1152
    assert tables['collection']['live_statuses'] == {'completed': 1143, 'incomplete': 9}
    assert audit['proposals_processed'] == 392 and audit['conversations_processed'] == 576
    assert audit['status'] == 'programmatic_evidence_pass_complete'
    restored_inputs = {}
    def read_paper(relative):
        path = ROOT / 'paper' / relative
        restored_inputs[str(path.relative_to(ROOT))] = sha(path)
        return path.read_text()
    def expand_inputs(text):
        return re.sub(r'\\input\{([^}]+)\}', lambda m: expand_inputs(read_paper(m[1])), text)
    historical = read_paper('editorial/manuscript.tex')
    earlier = historical.split(r'\section{What counts as an error, and when is it visible?}', 1)[1]
    earlier = r'\section{What counts as an error, and when is it visible?}' + earlier.split(r'\input{editorial/practical_use_expanded.tex}', 1)[0]
    related = historical.split(r'\section{Related work}', 1)[1].split(r'\section{Conclusion}', 1)[0]
    related = related.replace(r'\label{sec:related}', '')
    related = related.replace('PrefixGuard learns online warnings from structured trace views', 'PrefixGuard connects learned-event failure warnings with finite-state execution diagnosis')
    related = related.replace('Our contribution follows that distinction and asks how it changes a monitor\'s negative class and warning clock; our interaction rule and constructed eligibility subset are narrower than their procedural taxonomy.', 'Our earlier monitoring studies apply that distinction to the negative class and warning clock. The later live studies examine its consequences for intervention accounting; all selected checks remain narrower than comprehensive procedural integrity.')
    related = related.replace('our separate live follow-up', 'our live-gating studies').replace('Our separate live follow-up', 'Our live-gating studies').replace('studies tests', 'studies test')
    related = related.replace('Studies of model judges and G-Eval evaluate agreement with human judgments and identify limitations of automated evaluation', 'Studies of model judges and G-Eval examine evaluation agreement and limitations of automated assessment')
    related = re.sub(r'\\paragraph\{Agent safety and adversarial environments\.\}.*?(?=\\paragraph\{Warning, diagnosis and repair\.\})', '', related, flags=re.S)
    related = related.replace('Procedure-Aware Evaluation directly studies successful outcomes that conceal procedural violations \\citep{cao2026procedure}. Our earlier monitoring studies apply that distinction to the negative class and warning clock. The later live studies examine its consequences for intervention accounting; all selected checks remain narrower than comprehensive procedural integrity. ', '')
    related = re.sub(r'\\paragraph\{Tool capability and interactive evaluation\.\}.*?(?=\\paragraph\{Process, outcomes and apparent success\.\})', lambda m:'\\paragraph{Tool capability and interactive evaluation.} API generation, retrieval and invocation are studied by Gorilla, ToolLLM and API-Bank, while AgentBench covers interactive decision environments \\citep{patil2023gorilla,qin2023toolllm,li2023apibank,liu2023agentbench}. GAIA, WebArena, WorkArena, OSWorld, SWE-bench and AppWorld extend capability evaluation across information access, interfaces, software and stateful tools, with task distributions distinct from our policy-boundary measurements \\citep{mialon2023gaia,zhou2023webarena,drouin2024workarena,xie2024osworld,jimenez2024swebench,trivedi2024appworld}.\n\n', related, flags=re.S)
    appendices = historical.split(r'\appendix', 1)[1].split(r'\end{document}', 1)[0]
    appendices = appendices.replace(r'\clearpage', '')
    appendices = appendices.replace(r'\section{Model and execution configuration}', r'\section{Earlier model and execution configuration}')
    appendices = appendices.replace('The earlier audit contains 16,964', 'Historical accounting for the studies preceding the compact allocation contains 16,964')
    appendices = appendices.replace('Cumulative response-reported cost is', 'For these earlier studies only, cumulative response-reported cost is')
    practical = read_paper('editorial/practical_use_expanded.tex')
    practical = practical.replace("It does not reproduce the later compact study or assemble the combined paper. The combined-paper reporting checks and source builder are listed in its artifact-map appendix.", "The later compact tables and paired exports are reproduced with one command: \\texttt{python paper/combined\\_study/reproduce\\_principal.py}. It verifies the saved evidence and regenerates each principal table; full dependencies must accompany a review release.")
    earlier = expand_inputs(earlier)
    promoted = {}
    for marker,label in [('RQ1_TARGET_FIGURE','fig:expanded-targets'),('RQ1_TARGET_TABLE','tab:substantive-targets'),('RQ1_TIMING_FIGURE','fig:timing'),('RQ1_TIMING_TABLE','tab:expanded-timing'),('RQ2_CANCELLATION_TABLE','tab:policy-lab')]:
        blocks=list(re.finditer(r'\\begin\{(table|figure)\}.*?\\end\{\1\}',earlier,re.S))
        match=next(m for m in blocks if r'\label{'+label+'}' in m.group())
        promoted[marker]=match.group().replace('[t]', '[!htbp]')
        earlier=earlier[:match.start()]+earlier[match.end():]
    for heading,pointer in [
        (r'\section{What the reserved-test conversations show}',r'Main-text timing results: Figure~\ref{fig:timing}.'),
        (r'\subsection{Expanded test coverage separates warning targets}',r'Main-text results: Figure~\ref{fig:expanded-targets} and Table~\ref{tab:expanded-timing}.'),
        (r'\subsection{Changing the monitoring question changes warnings}',r'Main-text results: Table~\ref{tab:substantive-targets}.'),
        (r'\subsection{Cancellation examples: execution does not establish eligibility}',r'Main-text results: Table~\ref{tab:policy-lab}.')]:
        assert heading in earlier,heading
        earlier=earlier.replace(heading,heading+'\n'+pointer+'\n',1)
    earlier=earlier.replace('The two models move in opposite directions (Table~\\ref{tab:substantive-targets}).','The two models move in opposite directions.')
    fragments = {'EARLIER_STUDIES': earlier, 'EARLIER_RELATED_WORK': related, 'EARLIER_APPENDICES': appendices, **promoted}
    for marker, fragment in fragments.items():
        fragment = expand_inputs(fragment).replace('ruan2023toolemu', 'ruan2024toolemu')
        fragment = re.sub(r'\\includegraphics(?:\[[^\]]*\])?\{figures/', lambda m:m[0].replace('{figures/','{../figures/'), fragment)
        source = source.replace('{{'+marker+'}}', '\n```{=latex}\n'+fragment+'\n```\n')
    earlier_analysis = json.loads((ROOT / 'replication/analysis.json').read_text())
    assert earlier_analysis['totals']['completed'] == 227
    assert earlier_analysis['totals']['task_ids'] == 60
    assert earlier_analysis['replication']['state_rates']['gemini']['alerts'] == 86
    assert earlier_analysis['replication']['clean_rates']['gemini']['alerts'] == 2
    assert earlier_analysis['replication']['clean_successes'] == 49
    assert 'The 65 unresolved blocks remain a limitation' in source
    assert 'expert study is pending' not in source
    assert 'The corresponding results are shown' not in source
    cited = set(re.findall(r'@([a-z0-9]+)', source))
    for match in re.finditer(r'\\cite[pt]?\{([^}]+)\}', source):
        cited.update(match[1].split(','))
    assert cited == set(refs), (cited - set(refs), set(refs) - cited)
    assert source.count('{{FIGURE_OUTCOMES}}') == source.count('{{REFERENCES}}') == source.count('{{APPENDIX}}') == 1

    url = lambda r: r.get('url') or 'https://arxiv.org/abs/' + r['arxiv'] + r.get('version', '')
    def md_cites(match):
        keys = re.findall(r'@([a-z0-9]+)', match.group())
        return '(' + '; '.join(f"[{refs[k]['short']}, {refs[k]['year']}]({url(refs[k])})" for k in keys) + ')'
    bibliography = '## References\n\n' + '\n\n'.join(
        r['authors'].replace(' and ', '; ').replace('{','').replace('}','') + f" ({r['year']}). **{r['title']}**. " +
        (r['venue'] + '. ' if 'venue' in r else '') + f"[Source]({url(r)})."
        for _, r in sorted(refs.items(), key=lambda x: x[1]['short'])) + '\n'

    title, remainder = source.split('\n', 1)
    abstract, body = remainder.split('## Abstract\n\n', 1)[1].split('\n## 1. Introduction\n', 1)
    body = '## 1. Introduction\n' + body
    main, appendix = body.split('{{REFERENCES}}\n\n{{APPENDIX}}', 1)
    figure = r'''\begin{figure}[htbp]
\centering
\includegraphics[width=\linewidth]{figures/assignment_bounds.pdf}
\caption{Gate-minus-ungated outcome differences on a shared scale. Segments cover all compatible assignments of unresolved outcomes; diamonds mark midpoints of those bounds, not fitted estimates. Negative values indicate fewer violations or fewer reference completions.}
\label{fig:bounds}
\end{figure}'''
    main = main.replace('{{FIGURE_OUTCOMES}}', figure)
    flow = r'''\begin{figure}[htbp]
\centering
\includegraphics[width=\linewidth]{figures/evaluation_flow.pdf}
\caption{Three research questions at the action boundary. RQ1 evaluates the warning against its target and visible evidence; RQ2 compares the gate with native enforcement; RQ3 observes continuing task outcomes. Dashed replay is an offline one-step check. Block feedback returns to the actor, and the resulting live trajectory can differ from the ungated trajectory.}
\label{fig:evaluation-flow}
\end{figure}'''
    main = main.replace('{{EVALUATION_DIAGRAM}}', flow)
    def convert(text):
        text = re.sub(r'^(#{2,3})\s+(?:\d+(?:\.\d+)*|[A-D])\.\s+', r'\1 ', text, flags=re.M)
        return subprocess.check_output(['pandoc', '--from=markdown+raw_tex+tex_math_dollars', '--to=latex', '--natbib', '--syntax-highlighting=none', '--shift-heading-level=-1', '--top-level-division=section'], input=text, text=True)
    main_tex, appendix_tex = convert(main), convert(appendix)
    def table_widths(text, widths):
        layouts = iter(widths)
        def replace(match):
            layout = next(layouts)
            assert abs(sum(layout) - 1) < 0.00001
            directions = re.findall(r'\\(raggedright|raggedleft)\\arraybackslash', match.group())
            if not directions:
                simple = re.search(r'@\{\}([lr]+)@', match.group()).group(1)
                directions = ['raggedright' if c == 'l' else 'raggedleft' for c in simple]
            assert len(directions) == len(layout)
            columns = ['>{\\' + direction + r'\arraybackslash}p{(\linewidth - ' + str(2*len(layout)-2) + r'\tabcolsep) * \real{' + f'{width:.4f}' + '}}' for direction, width in zip(directions, layout)]
            return r'\begin{longtable}[]{@{}' + '\n  ' + '\n  '.join(columns) + '@{}}'
        text, count = re.subn(r'\\begin\{longtable\}\[\]\{@\{\}.*?@\{\}\}', replace, text, flags=re.S)
        assert count == len(widths)
        return text
    main_tex = table_widths(main_tex, [
        [.23,.39,.38], [.22,.17,.18,.32,.11], [.40,.11,.15,.17,.17],
        [.70,.15,.15], [.24,.19,.19,.19,.19], [.20,.14,.17,.17,.14,.18], [.70,.15,.15]])
    appendix_tex = table_widths(appendix_tex, [
        [.14,.46,.23,.17], [.25,.24,.17,.17,.17], [.14,.16,.25,.28,.17],
        [.13,.23,.23,.18,.23], [.27,.1825,.1825,.1825,.1825], [.18,.18,.18,.23,.23], [.18,.38,.44]])
    def compact_tables(text):
        def replace(match):
            block = match.group()
            declaration = re.match(r'\\begin\{longtable\}\[\](\{@\{\}.*?@\{\}\})', block, re.S)
            columns = declaration.group(1)
            rest = block[declaration.end():].strip()
            caption, rest = rest.split(r'\tabularnewline', 1)
            header = rest.split(r'\endfirsthead', 1)[0]
            rows = rest.split(r'\endlastfoot', 1)[1].split(r'\end{longtable}', 1)[0]
            return '\\begin{table}[htbp]\n\\centering\n\\small\n' + caption + '\n\\begin{tabular}' + columns + header + rows + '\\bottomrule\n\\end{tabular}\n\\end{table}'
        return re.sub(r'\\begin\{longtable\}.*?\\end\{longtable\}', replace, text, flags=re.S)
    main_tex, appendix_tex = compact_tables(main_tex), compact_tables(appendix_tex)
    labels = re.findall(r'\\label\{([^}]+)\}', main_tex + appendix_tex)
    assert len(labels) == len(set(labels)), 'Duplicate labels'
    references = set(re.findall(r'\\ref\{([^}]+)\}', main_tex + appendix_tex))
    assert references <= set(labels), references - set(labels)
    main_tex = main_tex.replace('The allocation is\n\n\\[', 'The allocation is\n\\nopagebreak\n\\[')
    abstract_tex = convert(abstract).strip()
    preamble = r'''\documentclass[10pt]{article}
\usepackage{../tmlr}
\usepackage{amsmath,amssymb,booktabs,longtable,array,calc,graphicx,microtype,xurl}
\usepackage[colorlinks=true,citecolor=blue,linkcolor=blue,urlcolor=blue]{hyperref}
\usepackage[section]{placeins}
\newcommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}
\newcommand{\ind}{\mathbf{1}}
\providecommand{\pandocbounded}[1]{#1}
\setlength{\emergencystretch}{2em}
\setlength{\LTpre}{0.6em}
\setlength{\LTpost}{0.6em}
\setlength{\LTcapwidth}{\linewidth}
\AtBeginEnvironment{longtable}{\small}
\title{MANUSCRIPT_TITLE}
\author{Anonymous authors}
\begin{document}
\maketitle
\begin{abstract}
'''
    title_tex = tex(title.removeprefix('# ')).replace(': ', r':\\', 1)
    preamble = preamble.replace('MANUSCRIPT_TITLE', title_tex)
    preamble = preamble.replace(r'\usepackage[section]{placeins}', r'\usepackage[section]{placeins}' + '\n' + r'\hypersetup{pdftitle={' + tex(title.removeprefix('# ')) + r'},pdfauthor={Anonymous authors}}')
    preamble = preamble.replace('graphicx,microtype,xurl', 'graphicx,microtype,xurl,etoolbox')
    preamble = preamble.replace('\\begin{document}', read_paper('generated/macros.tex') + '\\begin{document}')
    manuscript_tex = preamble + abstract_tex + '\n\\end{abstract}\n\\input{manuscript_body.tex}\n\\bibliographystyle{../tmlr}\n\\bibliography{manuscript_references}\n\\clearpage\n\\appendix\n\\input{manuscript_appendix.tex}\n\\end{document}\n'
    readable_tex = '\\documentclass{article}\n\\newcommand{\\ind}{\\mathbf{1}}\n' + read_paper('generated/macros.tex') + '\\begin{document}\n' + main_tex + '\nREFERENCESMARKER\n\\appendix\n' + appendix_tex + '\n\\end{document}'
    def readable_columns(match):
        count = len(re.findall(r'\\arraybackslash',match[0]))
        return r'\begin{tabular}{' + 'l'*count + '}'
    readable_tex = re.sub(r'\\begin\{tabular\}\{@\{\}.*?@\{\}\}', readable_columns, readable_tex, flags=re.S)
    readable_ast = json.loads(subprocess.check_output(['pandoc','--from=latex','--to=json'],input=readable_tex,text=True))
    def unwrap_divs(node):
        if isinstance(node,list):
            result=[]
            for item in node:
                if isinstance(item,dict) and item.get('t')=='Div':
                    anchor=item['c'][0][0]
                    if anchor:
                        result.append({'t':'RawBlock','c':['html','<a id="'+anchor+'"></a>']})
                    result.extend(unwrap_divs(item['c'][1]))
                else:
                    result.append(unwrap_divs(item))
            return result
        if isinstance(node,dict):
            return {key:unwrap_divs(value) for key,value in node.items()}
        return node
    readable_ast=unwrap_divs(readable_ast)
    readable = subprocess.check_output(['pandoc','--from=json','--to=markdown-grid_tables-simple_tables-multiline_tables-fenced_divs','--wrap=none','--markdown-headings=atx'],input=json.dumps(readable_ast),text=True)
    readable = re.sub(r'^(#+) ',r'#\1 ',readable,flags=re.M)
    readable = re.sub(r'\{reference-type="ref" reference="[^\"]+"\}', '', readable)
    readable = re.sub(r'\[@[^\]]+\]', md_cites, readable)
    readable = title + '\n\n**Working manuscript source - 26 October 2026.**\n\n## Abstract\n\n' + abstract + '\n\n' + readable.replace('REFERENCESMARKER',bibliography+'\n## Appendices\n')
    readable = re.sub(r'^:::.*\n?', '', readable, flags=re.M)
    bib = ''
    for key, r in sorted(refs.items()):
        authors = r['authors'].replace('ć', r"{\'c}").replace('è', r'{\`e}')
        fields = dict(r.get('bibtex_fields', {}))
        fields.update({'author': authors, 'title': '{' + r['title'] + '}', 'year': str(r['year']), 'url': url(r)})
        if not r.get('bibtex_fields'):
            fields['booktitle' if 'venue' in r else 'journal'] = r.get('venue', 'arXiv preprint arXiv:' + r['arxiv'])
        if 'pages' in r:
            fields['pages'] = r['pages']
        bib += '@' + r.get('entry_type', 'inproceedings' if 'venue' in r else 'article') + '{' + key + ',\n'
        bib += ',\n'.join('  ' + k + ' = {' + v + '}' for k,v in fields.items()) + '\n}\n\n'

    bib = bib.translate(str.maketrans({'’': "'", '‘': "'", '“': '``', '”': "''"}))

    # The plotted endpoints are independently tied to the frozen summaries below.
    expected = []
    for condition in ['none','broad','decomposed']:
        pressure = next(r for r in tables['live_by_condition'] if r['condition']==condition and r['pressure'])['executed_violation']
        permitted = next(r for r in tables['live_by_condition'] if r['condition']==condition and not r['pressure'])['service_complete']
        assert pressure['assigned']==permitted['assigned']==192
        expected.append((pressure['observed_positive'],pressure['missing'],permitted['observed_positive'],permitted['missing']))
    assert expected == [(21,0,181,0),(1,2,163,2),(2,1,166,3)]
    plot = r"""\documentclass{article}
\usepackage[paperwidth=6.5in,paperheight=2.6in,margin=0in]{geometry}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\pagestyle{empty}
\begin{document}
\noindent\begin{tikzpicture}
\begin{axis}[width=13.8cm,height=6.2cm,
ytick={0,1,2,3},yticklabels={Completion: decomposed,Completion: broad,Violation: decomposed,Violation: broad},ymin=-.5,ymax=3.5,
xmin=-11,xmax=0,xtick={-10,-8,-6,-4,-2,0},xlabel={Gate minus ungated (percentage points)},
xmajorgrids=true,grid style={gray!20},axis lines=left,tick label style={font=\small},enlargelimits=false]
"""
    for i,(outcome,gate) in enumerate([('service_complete','decomposed'),('service_complete','broad'),('executed_violation','decomposed'),('executed_violation','broad')]):
        row=next(r for r in tables['primary_contrasts'] if r['outcome']==outcome and r['gate']==gate)
        lo,hi=[100*x for x in row['assignment_bounds']]
        color='blue!65!black' if outcome=='executed_violation' else 'orange!80!black'
        plot+=f'\\addplot[{color},very thick] coordinates {{({lo:.8f},{i}) ({hi:.8f},{i})}};\n'
        plot+=f'\\addplot[only marks,mark=diamond*,mark size=2.2pt,{color}] coordinates {{({(lo+hi)/2:.8f},{i})}};\n'
    plot+='\\end{axis}\n\\end{tikzpicture}\n\\end{document}\n'

    outputs = {'manuscript_draft.md': readable, 'manuscript.tex': manuscript_tex,
        'manuscript_body.tex': main_tex, 'manuscript_appendix.tex': appendix_tex.rstrip() + '\n',
        'manuscript_references.bib': bib.rstrip() + '\n', 'figures/assignment_bounds.tex': plot}
    manifest = {'version': '2026-10-26-review-revision', 'scope': 'Combined warning, policy-comparison and live-gating manuscript; cohorts and frozen analyses remain separate.',
        'model_calls': 0, 'references': len(refs),
        'restored_inputs_sha256': restored_inputs,
        'principal_table_builder_sha256': sha(HERE/'build_principal_tables.py'),
        'paired_effect_builder_sha256': sha(HERE/'build_paired_effects.py'),
        'exploratory_builder_sha256': sha(HERE/'build_exploratory_followup.py'),
        'earlier_analysis_sha256': sha(ROOT/'replication/analysis.json'),
        'pdf_status': 'Not regenerated by the source builder; requires a matching full-project compile.',
        'inputs_sha256': {name:sha(HERE/name) for name in ['manuscript_source.md','manuscript_references.json','results_tables.json','policy_audit/evidence_audit/summary.json']},
        'builder_sha256':sha(Path(__file__)), 'outputs_sha256':{k:hashlib.sha256(v.encode()).hexdigest() for k,v in outputs.items()}}
    outputs['manuscript_build.json'] = json.dumps(manifest,indent=2,sort_keys=True)+'\n'
    return outputs

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
    outputs=produce()
    for name,content in outputs.items():
        path=HERE/name
        if args.check:
            assert path.read_text()==content,name
        else:
            path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content)
    print(json.dumps({'manuscript_sources_verified':True,'check_only':args.check,'outputs':len(outputs),'model_calls':0}))

if __name__=='__main__':
    main()
