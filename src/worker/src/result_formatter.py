import ansi2html
from common.schemas import SubmissionResultSchema

def get_result_score(result: SubmissionResultSchema) -> float:
    return 100*result.points / len(result.test_results) if len(result.test_results) > 0 else 0


def get_result_formatted(result: SubmissionResultSchema) -> str:
    score = get_result_score(result)
    result_content = \
f"""
result={score}
infoformat=html
debugformat=html
info=All tests passed
"""
    return result_content
    
    
def get_info_formatted(result: SubmissionResultSchema) -> str:
    score = get_result_score(result)
    info_content = \
f"""
<style>

    table {{ 
        border-collapse: collapse; 
        border: 1px solid #202020;
        border-radius: 5px; 
        overflow: hidden;
    }}
    th {{ 
        border: 1px solid #202020; 
        padding: 3px 10px; 
        background-color: #d8d8d8; 
        max-width: 350px;
    }}
    td {{
        border-left: 1px solid #202020; 
        border-right: 1px solid #202020; 
        padding: 3px 10px; 
        max-width: 350px;
        white-space: nowrap;
        overflow: hidden;
    }}
    tr:hover td {{
    }}
    tbody tr:nth-child(even) {{ filter: brightness(90%); }}
    .success {{ background-color: #6fb65d; }}
    .failure {{ background-color: #b65d62; }}
    .eerror {{ background-color: #e69c53; }}

</style>
<b>Score:</b> {score:.2f}%
<br>
<br>
"""
    if len(result.test_results) != 0:
        info_content += \
f"""
<div style="background-color: #202020; border-radius: 5px; width: fit-content;">
    <table>
        <tr>
            <th>Test Name</th>
            <th>Return Code</th>
            <th>Time [s]</th>
            <th>Maxrss [kB]</th>
            <th>Info</th>
        </tr>
        {''.join(f"<tr class='{'success' if test.grade else ('failure' if test.ret_code >= 0 else 'eerror')}'><td>{test.test_name}</td><td>{test.ret_code if test.ret_code >= 0 else ''}</td><td>{test.time:.2f}</td><td>{test.memory:.0f}</td><td>{test.info}</td></tr>" for test in result.test_results)}
    </table>
</div>
"""
    if result.info:
        converter = ansi2html.Ansi2HTMLConverter(inline=True)
        info_parsed = converter.convert(result.info, full=False)
        info_content += f"""<pre style='font-family: monospace;'>{info_parsed}</pre>"""
    
    return info_content

def get_debug_formatted(result: SubmissionResultSchema) -> str:
    debug_content = f"""Compiling...Running...OK"""
    return debug_content

    



