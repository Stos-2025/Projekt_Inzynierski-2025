"""Result formatter module for STOS submission evaluation results.

This module provides functionality to format submission evaluation results
into various output formats including HTML tables, debug information,
and result summaries for display in the STOS GUI.

The formatter handles test results, compilation information, debug logs,
and generates styled HTML output with proper formatting and color coding.
"""

import ansi2html
from common.schemas import SubmissionResultSchema, TestResultSchema


def get_result_score(result: SubmissionResultSchema) -> float:
    """Calculate the percentage score for a submission result.

    Args:
        result (SubmissionResultSchema): The submission result containing test results and points.

    Returns:
        float: Percentage score (0-100) based on passed tests vs total tests.
    """
    return (
        (100 * result.points / len(result.test_results))
        if len(result.test_results) > 0
        else 0
    )


def get_result_formatted(result: SubmissionResultSchema) -> str:
    """Format submission result into STOS GUI result format.

    Creates a formatted result string containing the score, format specifications,
    and basic info message for the STOS GUI API.

    Args:
        result (SubmissionResultSchema): The submission result to format.

    Returns:
        str: Formatted result string with score and format specifications.
    """
    score = get_result_score(result)
    result_content = f"""
result={score}
infoformat=html
debugformat=html
info=All tests passed
    """
    return result_content


def get_info_formatted(result: SubmissionResultSchema) -> str:
    """Format submission result into detailed HTML info display.

    Creates a comprehensive HTML table showing test results with styling,
    color coding for pass/fail/error states, and compilation information.
    Includes CSS styling for professional presentation.

    Args:
        result (SubmissionResultSchema): The submission result to format.

    Returns:
        str: HTML formatted string with test results table and compilation info.
    """

    def trow_from_test(test: TestResultSchema) -> str:
        css_class = "failure"
        if (test.ret_code or 0) != 0:
            css_class = "eerror"
        elif test.grade:
            css_class = "success"
        name = test.test_name
        info = test.info or ""
        score = (100 if test.grade else 0)
        if test.time is None or test.memory is None or test.memory == 0 or test.ret_code is None:
            return f"<tr class='{css_class}'><td>{name}</td><td>{score}</td><td></td><td></td><td></td><td></td></tr>"
        return f"<tr class='{css_class}'><td>{name}</td><td>{score}</td><td>{test.time:.2f}</td><td>{test.memory/1024:.0f}</td><td>{test.ret_code}</td><td>{info}</td></tr>"

    score = get_result_score(result)
    
    total_time=0
    time_usage_limit = [test.time for test in result.test_results if test.time is not None]
    if any(time_usage_limit):
        total_time= sum(time_usage_limit)
    
    max_memory=0
    memory_usage_list = [test.memory for test in result.test_results if test.memory is not None]
    if any(memory_usage_list):    
        max_memory= max(memory_usage_list)
        
    border_color = "#202020"
    border_radius = "4px"
    max_width = "250px"
    info_content = f"""
<style>
    table {{ 
        border-collapse: collapse; 
        border: 1px solid {border_color};
        border-radius: {border_radius}; 
        overflow: hidden;
    }}
    th {{ 
        border: 1px solid {border_color}; 
        padding: 3px 10px; 
        background-color: #d8d8d8; 
        max-width: {max_width};
        text-align: center;
    }}
    td {{
        border-left: 1px solid {border_color}; 
        border-right: 1px solid {border_color}; 
        padding: 3px 10px; 
        max-width: {max_width};
        white-space: nowrap;
        overflow: hidden;
        text-align: right;
    }}
    .ts {{
        background-color: #d8d8d8;
        border: 1px solid {border_color};
        filter: brightness(100%) !important;
    }} 
    tr:hover td {{
    }}
    tbody tr:nth-child(odd) {{ filter: brightness(90%); }}
    .success {{ background-color: rgb(109, 156, 109); }}
    .failure {{ background-color: rgb(164, 84, 88); }}
    .eerror {{ background-color: rgb(207, 140, 75); }}
    .wrapper {{
        background-color: {border_color}; 
        border-radius: {border_radius}; 
        width: fit-content;
    }} 
</style>
    """
    if len(result.test_results) != 0:

        info_content += f"""
<div class="wrapper">
    <table>
        <tr class="ts">
            <th class="tname"></th>
            <th class="tscore"></th>
            <th class="ttime"></th>
            <th class="tmemory"></th>
            <th class="tcode"></th>
            <th class="ttinfo"></th>
        </tr>
        {''.join(trow_from_test(test) for test in result.test_results)}
        <tr class="ts">
            <td ><strong class="ttotal"></strong>:</td>
            <td>{score:.0f}</td>
            <td>{total_time:.2f}</td>
            <td>{max_memory/1024:.0f}</td>
            <td colspan="2"></td>
        </tr>
    </table>
</div>
    """
    else:
        info_content += "<strong class=\"tcompilation_error\"></strong>"
    if result.info:
        # todo: handle html escaping properly --- IGNORE ---
        converter = ansi2html.Ansi2HTMLConverter(inline=True)
        info_parsed = converter.convert(result.info, full=False)
        info_content += f"""<pre style='font-family: monospace;'>{info_parsed}</pre>"""

    info_content += """
<script>
const params = new URLSearchParams(location.search);
const lang = params.get("lang") || "pl";

const TR = {
    pl: {
        name: "Nazwa",
        score: "Wynik [%]",
        time: "Czas [s]",
        memory: "Pamięć [KiB]",
        code: "Kod",
        info: "Informacja",
        total: "Razem",
        compilation_error: "Błąd kompilacji.",
    },
    en: {
        name: "Name",
        score: "Score [%]",
        time: "Time [s]",
        memory: "Memory [KiB]",
        code: "Code",
        info: "Info",
        total: "Total",
        compilation_error: "Compilation error.",
    }
};

const t = TR[lang] || TR.pl;

document.querySelectorAll("th.tname")
    .forEach(el => el.textContent = t.name);
document.querySelectorAll("th.tscore")
    .forEach(el => el.textContent = t.score);
document.querySelectorAll("th.ttime")
    .forEach(el => el.textContent = t.time);
document.querySelectorAll("th.tmemory")
    .forEach(el => el.textContent = t.memory);
document.querySelectorAll("th.tcode")
    .forEach(el => el.textContent = t.code);
document.querySelectorAll("th.ttinfo")
    .forEach(el => el.textContent = t.info);

document.querySelectorAll("strong.ttotal")
    .forEach(el => el.textContent = t.total);
document.querySelectorAll("strong.tcompilation_error")
    .forEach(el => el.textContent = t.compilation_error);
</script>
"""

    return info_content


def get_debug_formatted(result: SubmissionResultSchema) -> str:
    """Format debug information into HTML display.

    Converts ANSI escape sequences in debug logs to HTML format
    for proper display in the STOS GUI.

    Args:
        result (SubmissionResultSchema): The submission result containing debug information.

    Returns:
        str: HTML formatted debug information or empty string if no debug info.
    """
    debug_content = ""
    if result.debug:
        converter = ansi2html.Ansi2HTMLConverter(inline=True)
        debug_parsed = converter.convert(result.debug, full=False)
        debug_content += (
            f"""<pre style='font-family: monospace;'>{debug_parsed}</pre>"""
        )
    return debug_content
