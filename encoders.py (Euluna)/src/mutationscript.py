#!/usr/bin/env python3
"""
Mutation Testing Script for fastapi/encoders.py

This script generates mutants using various mutation operators, runs tests against
each mutant, tracks which are killed vs survived, and generates detailed reports.

Mutation Operators Applied:
1. AOR (Arithmetic Operator Replacement)
2. ROR (Relational Operator Replacement)
3. LCR (Logical Connector Replacement)
4. CDL (Constant Replacement)
5. UOI (Unary Operator Insertion)
6. RIL (Return Statement Mutation)
7. STR (String Mutation)
8. MSI (Method Call Modification)
9. IOD (In/Not in Operator)
10. TYP (Type Check Mutation)
11. DCI (Dictionary/Container Operations)
12. FCR (Function Call Replacement)
"""

import os
import sys
import subprocess
import shutil
import time
import json
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict


@dataclass
class Mutant:
    """Represents a single mutant"""
    id: int
    operator: str
    description: str
    original_code: str
    mutated_code: str
    line_number: int
    unified_diff: str
    status: str = "NOT_TESTED"  # NOT_TESTED, KILLED, SURVIVED, ERROR, TIMEOUT
    test_output: str = ""
    routine_name: str = ""  # Function/method where mutation occurred


def is_code_line(line: str, in_docstring: bool = False, in_doc_annotation: bool = False) -> bool:
    """Check if a line contains actual code (not comments or docstrings)"""
    if in_docstring or in_doc_annotation:
        return False
    
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith('#'):
        return False
    if stripped.startswith('"""') or stripped.startswith("'''"):
        return False
    if '"""' in stripped or "'''" in stripped:
        return False
    if stripped.startswith('Doc(') or (stripped.endswith('),') and 'Doc(' in line):
        return False
    return True


def get_routine_name(lines: List[str], line_num: int) -> str:
    """Get the function/method name for a given line number"""
    for i in range(line_num - 1, -1, -1):
        line = lines[i].strip()
        if line.startswith('def '):
            func_name = line.split('(')[0].replace('def ', '').strip()
            return func_name
    return "module_level"


def generate_mutants(source_lines: List[str]) -> List[Mutant]:
    """Generate all mutants for encoders.py"""
    mutants = []
    mutant_id = 1
    
    # First pass: identify lines that are in docstrings or comments
    in_docstring = False
    docstring_marker = None
    code_lines = set()  # Line numbers that contain code (not docstrings/comments)
    
    for i, line in enumerate(source_lines):
        stripped = line.strip()
        
        # Track docstrings
        if '"""' in line:
            count = line.count('"""')
            if count == 1:
                in_docstring = not in_docstring
            elif count >= 2:
                in_docstring = False  # Docstring on single line
        elif "'''" in line:
            count = line.count("'''")
            if count == 1:
                in_docstring = not in_docstring
            elif count >= 2:
                in_docstring = False  # Docstring on single line
        
        # Check if this is a code line
        if not in_docstring and stripped and not stripped.startswith('#'):
            code_lines.add(i + 1)  # Convert to 1-indexed
    
    # AOR: Arithmetic operators
    arithmetic_ops = [('+', '-'), ('-', '+'), ('*', '/'), ('/', '*'), ('//', '/'), ('%', '//')]
    for i, line in enumerate(source_lines, 1):
        if i not in code_lines:
            continue
            
        for orig_op, new_op in arithmetic_ops:
            if f' {orig_op} ' in line or f'{orig_op}=' in line:
                mutated_line = line.replace(f' {orig_op} ', f' {new_op} ', 1)
                if mutated_line == line:
                    mutated_line = line.replace(f'{orig_op}=', f'{new_op}=', 1)
                if mutated_line != line:
                    diff = f"--- original (line {i})\n+++ mutant (line {i})\n-{line}\n+{mutated_line}"
                    routine = get_routine_name(source_lines, i)
                    mutants.append(Mutant(
                        id=mutant_id, operator="AOR",
                        description=f"Replace '{orig_op}' with '{new_op}' at line {i}",
                        original_code=line.strip(), mutated_code=mutated_line.strip(),
                        line_number=i, unified_diff=diff, routine_name=routine
                    ))
                    mutant_id += 1
    
    # ROR: Relational operators
    relational_ops = [('==', '!='), ('!=', '=='), (' < ', ' <= '), (' > ', ' >= '), 
                      ('<=', '<'), ('>=', '>'), (' is ', ' is not '), (' is not ', ' is ')]
    for i, line in enumerate(source_lines, 1):
        if i not in code_lines:
            continue
        
        for orig_op, new_op in relational_ops:
            if orig_op in line and 'import' not in line:
                mutated_line = line.replace(orig_op, new_op, 1)
                diff = f"--- original (line {i})\n+++ mutant (line {i})\n-{line}\n+{mutated_line}"
                routine = get_routine_name(source_lines, i)
                mutants.append(Mutant(
                    id=mutant_id, operator="ROR",
                    description=f"Replace '{orig_op.strip()}' with '{new_op.strip()}' at line {i}",
                    original_code=line.strip(), mutated_code=mutated_line.strip(),
                    line_number=i, unified_diff=diff, routine_name=routine
                ))
                mutant_id += 1
    
    # LCR: Logical operators
    logical_ops = [(' and ', ' or '), (' or ', ' and ')]
    for i, line in enumerate(source_lines, 1):
        if i not in code_lines:
            continue
        
        for orig_op, new_op in logical_ops:
            if orig_op in line:
                mutated_line = line.replace(orig_op, new_op, 1)
                diff = f"--- original (line {i})\n+++ mutant (line {i})\n-{line}\n+{mutated_line}"
                routine = get_routine_name(source_lines, i)
                mutants.append(Mutant(
                    id=mutant_id, operator="LCR",
                    description=f"Replace '{orig_op.strip()}' with '{new_op.strip()}' at line {i}",
                    original_code=line.strip(), mutated_code=mutated_line.strip(),
                    line_number=i, unified_diff=diff, routine_name=routine
                ))
                mutant_id += 1
    
    # CDL: Constant replacement
    constant_replacements = [
        ('= True', '= False'), ('= False', '= True'),
        ('return True', 'return False'), ('return False', 'return True'),
        (' True,', ' False,'), (' False,', ' True,'),
        (' True)', ' False)'), (' False)', ' True)'),
        ('return None', 'return {}'), ('return {}', 'return None'),
        ('return []', 'return [None]'), (' None,', ' {},'), (' None)', ' {})'),
        (' 0', ' 1'), (' 1', ' 0'),
    ]
    for i, line in enumerate(source_lines, 1):
        if i not in code_lines:
            continue
        if 'def ' in line or 'class ' in line or 'import' in line:
            continue
            
        for orig_const, new_const in constant_replacements:
            if orig_const in line:
                mutated_line = line.replace(orig_const, new_const, 1)
                diff = f"--- original (line {i})\n+++ mutant (line {i})\n-{line}\n+{mutated_line}"
                routine = get_routine_name(source_lines, i)
                mutants.append(Mutant(
                    id=mutant_id, operator="CDL",
                    description=f"Replace '{orig_const.strip()}' with '{new_const.strip()}' at line {i}",
                    original_code=line.strip(), mutated_code=mutated_line.strip(),
                    line_number=i, unified_diff=diff, routine_name=routine
                ))
                mutant_id += 1
    
    # UOI: Unary operator insertion (not)
    for i, line in enumerate(source_lines, 1):
        if i not in code_lines:
            continue
        
        if line.strip().startswith('if ') and ':' in line and 'not ' not in line:
            if_pos = line.find('if ')
            colon_pos = line.find(':', if_pos)
            if if_pos != -1 and colon_pos != -1:
                indent = line[:if_pos]
                condition = line[if_pos+3:colon_pos].strip()
                mutated_line = f"{indent}if not ({condition}):"
                diff = f"--- original (line {i})\n+++ mutant (line {i})\n-{line}\n+{mutated_line}\n"
                routine = get_routine_name(source_lines, i)
                mutants.append(Mutant(
                    id=mutant_id, operator="UOI",
                    description=f"Insert 'not' operator in condition at line {i}",
                    original_code=line.strip(), mutated_code=mutated_line.strip(),
                    line_number=i, unified_diff=diff, routine_name=routine
                ))
                mutant_id += 1
    
    # RIL: Return statement mutation
    for i, line in enumerate(source_lines, 1):
        if i not in code_lines:
            continue
        
        stripped = line.strip()
        if stripped.startswith('return ') and stripped != 'return None':
            indent = line[:line.find('return')]
            
            # Try different mutations
            mutations = [
                ('None', 'Replace return value with None'),
                ('{}', 'Replace return value with empty dict'),
                ('[]', 'Replace return value with empty list'),
            ]
            
            for mut_val, mut_desc in mutations:
                mutated_line = f"{indent}return {mut_val}"
                if mutated_line.strip() != stripped:
                    diff = f"--- original (line {i})\n+++ mutant (line {i})\n-{line}\n+{mutated_line}\n"
                    routine = get_routine_name(source_lines, i)
                    mutants.append(Mutant(
                        id=mutant_id, operator="RIL",
                        description=f"{mut_desc} at line {i}",
                        original_code=line.strip(), mutated_code=mutated_line.strip(),
                        line_number=i, unified_diff=diff, routine_name=routine
                    ))
                    mutant_id += 1
    
    # STR: String mutation
    for i, line in enumerate(source_lines, 1):
        if not is_code_line(line):
            continue
        
        if ('"' in line or "'" in line) and 'import' not in line:
            # Mutate string literals to empty strings
            if 'str(' in line and 'return str(' in line:
                mutated_line = line.replace('str(', 'lambda x: "" or str(', 1).replace(')', '))', 1)
                diff = f"--- original (line {i})\n+++ mutant (line {i})\n-{line}\n+{mutated_line}"
                routine = get_routine_name(source_lines, i)
                mutants.append(Mutant(
                    id=mutant_id, operator="STR",
                    description=f"Mutate str() call at line {i}",
                    original_code=line.strip(), mutated_code=mutated_line.strip(),
                    line_number=i, unified_diff=diff, routine_name=routine
                ))
                mutant_id += 1
    
    # MSI: Method call modification - for encoders.py specific methods
    method_mutations = [
        ('.keys()', '.values()'), ('.values()', '.keys()'), 
        ('.items()', '.keys()'), ('.append(', '.insert(0, '),
        ('.model_dump(', '.model_dump_json('), ('.dict()', '.json()'),
        ('.asdict(', '.astuple('), ('.set(', '.frozenset('),
        ('.list(', '.tuple('),
    ]
    for i, line in enumerate(source_lines, 1):
        if not is_code_line(line):
            continue
        
        for orig_method, new_method in method_mutations:
            if orig_method in line:
                mutated_line = line.replace(orig_method, new_method, 1)
                diff = f"--- original (line {i})\n+++ mutant (line {i})\n-{line}\n+{mutated_line}"
                routine = get_routine_name(source_lines, i)
                mutants.append(Mutant(
                    id=mutant_id, operator="MSI",
                    description=f"Replace '{orig_method}' with '{new_method}' at line {i}",
                    original_code=line.strip(), mutated_code=mutated_line.strip(),
                    line_number=i, unified_diff=diff, routine_name=routine
                ))
                mutant_id += 1
    
    # IOD: In/Not in operator
    for i, line in enumerate(source_lines, 1):
        if not is_code_line(line):
            continue
        
        if ' in ' in line and ' not in ' not in line and 'import' not in line and 'for ' not in line:
            mutated_line = line.replace(' in ', ' not in ', 1)
            diff = f"--- original (line {i})\n+++ mutant (line {i})\n-{line}\n+{mutated_line}"
            routine = get_routine_name(source_lines, i)
            mutants.append(Mutant(
                id=mutant_id, operator="IOD",
                description=f"Replace 'in' with 'not in' at line {i}",
                original_code=line.strip(), mutated_code=mutated_line.strip(),
                line_number=i, unified_diff=diff, routine_name=routine
            ))
            mutant_id += 1
        elif ' not in ' in line:
            mutated_line = line.replace(' not in ', ' in ', 1)
            diff = f"--- original (line {i})\n+++ mutant (line {i})\n-{line}\n+{mutated_line}"
            routine = get_routine_name(source_lines, i)
            mutants.append(Mutant(
                id=mutant_id, operator="IOD",
                description=f"Replace 'not in' with 'in' at line {i}",
                original_code=line.strip(), mutated_code=mutated_line.strip(),
                line_number=i, unified_diff=diff, routine_name=routine
            ))
            mutant_id += 1
    
    # TYP: Type check mutation
    type_checks = [
        ('isinstance(', 'not isinstance('), 
        ('is_dataclass(', 'not is_dataclass('),
        ('type(', 'str(type('),
    ]
    for i, line in enumerate(source_lines, 1):
        if not is_code_line(line):
            continue
        
        for orig_check, new_check in type_checks:
            if orig_check in line and 'not ' + orig_check not in line:
                mutated_line = line.replace(orig_check, new_check, 1)
                diff = f"--- original (line {i})\n+++ mutant (line {i})\n-{line}\n+{mutated_line}"
                routine = get_routine_name(source_lines, i)
                mutants.append(Mutant(
                    id=mutant_id, operator="TYP",
                    description=f"Negate type check '{orig_check}' at line {i}",
                    original_code=line.strip(), mutated_code=mutated_line.strip(),
                    line_number=i, unified_diff=diff, routine_name=routine
                ))
                mutant_id += 1
    
    # DCI: Dictionary/Container operations
    dict_ops = [
        ('&=', '|='), ('|=', '&='), ('-=', '+='),
        ('[key]', '.get(key, None)'), ('.get(', '['),
    ]
    for i, line in enumerate(source_lines, 1):
        if not is_code_line(line):
            continue
        
        for orig_op, new_op in dict_ops:
            if orig_op in line:
                mutated_line = line.replace(orig_op, new_op, 1)
                diff = f"--- original (line {i})\n+++ mutant (line {i})\n-{line}\n+{mutated_line}"
                routine = get_routine_name(source_lines, i)
                mutants.append(Mutant(
                    id=mutant_id, operator="DCI",
                    description=f"Replace '{orig_op}' with '{new_op}' at line {i}",
                    original_code=line.strip(), mutated_code=mutated_line.strip(),
                    line_number=i, unified_diff=diff, routine_name=routine
                ))
                mutant_id += 1
    
    # FCR: Function call replacement
    func_replacements = [
        ('int(', 'float('), ('float(', 'int('), 
        ('str(', 'repr('), ('list(', 'tuple('), ('tuple(', 'list('),
        ('set(', 'frozenset('), ('dict(', 'list('),
    ]
    for i, line in enumerate(source_lines, 1):
        if not is_code_line(line):
            continue
        
        for orig_func, new_func in func_replacements:
            if orig_func in line and 'def ' not in line and 'import' not in line:
                mutated_line = line.replace(orig_func, new_func, 1)
                diff = f"--- original (line {i})\n+++ mutant (line {i})\n-{line}\n+{mutated_line}"
                routine = get_routine_name(source_lines, i)
                mutants.append(Mutant(
                    id=mutant_id, operator="FCR",
                    description=f"Replace '{orig_func}' with '{new_func}' at line {i}",
                    original_code=line.strip(), mutated_code=mutated_line.strip(),
                    line_number=i, unified_diff=diff, routine_name=routine
                ))
                mutant_id += 1
    
    return mutants


def run_tests_for_mutant(mutant: Mutant, target_file: Path, backup_file: Path, test_timeout: int = 30) -> Tuple[str, str]:
    """Run tests for a specific mutant and return status and output"""
    try:
        # Read original file
        with open(target_file, 'r', encoding='utf-8') as f:
            original_lines = f.readlines()
        
        # Create mutated version
        mutated_lines = original_lines.copy()
        if mutant.line_number <= len(mutated_lines):
            mutated_lines[mutant.line_number - 1] = mutant.mutated_code + '\n'
        
        # Write mutated file
        with open(target_file, 'w', encoding='utf-8') as f:
            f.writelines(mutated_lines)
        
        # Run tests
        result = subprocess.run(
            ['pytest', 'tests/test_jsonable_encoder.py', '-v', '--tb=short', '-x'],
            capture_output=True,
            text=True,
            timeout=test_timeout,
            cwd=target_file.parent.parent
        )
        
        # Restore original file
        shutil.copy2(backup_file, target_file)
        
        # Determine status
        if result.returncode != 0:
            return "KILLED", result.stdout + result.stderr
        else:
            return "SURVIVED", result.stdout + result.stderr
            
    except subprocess.TimeoutExpired:
        # Restore original file
        shutil.copy2(backup_file, target_file)
        return "TIMEOUT", "Test execution timed out"
    except Exception as e:
        # Restore original file
        shutil.copy2(backup_file, target_file)
        return "ERROR", str(e)


def save_comprehensive_report(mutants: List[Mutant], output_dir: Path, run_tests: bool = False):
    """Save comprehensive mutation testing report"""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Group by operator and routine
    by_operator: Dict[str, List[Mutant]] = {}
    by_routine: Dict[str, List[Mutant]] = {}
    by_status: Dict[str, List[Mutant]] = {}
    
    for mutant in mutants:
        # By operator
        if mutant.operator not in by_operator:
            by_operator[mutant.operator] = []
        by_operator[mutant.operator].append(mutant)
        
        # By routine
        if mutant.routine_name not in by_routine:
            by_routine[mutant.routine_name] = []
        by_routine[mutant.routine_name].append(mutant)
        
        # By status
        if mutant.status not in by_status:
            by_status[mutant.status] = []
        by_status[mutant.status].append(mutant)
    
    # Create main report
    report_file = output_dir / "mutation_report.md"
    print(f"\nSaving mutation report to {report_file}...")
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Encoders.py Mutation Testing Report\n\n")
        f.write(f"**Total mutants generated:** {len(mutants)}\n\n")
        
        if run_tests:
            killed = len(by_status.get('KILLED', []))
            survived = len(by_status.get('SURVIVED', []))
            errors = len(by_status.get('ERROR', []))
            timeouts = len(by_status.get('TIMEOUT', []))
            
            f.write("## Mutation Testing Results\n\n")
            f.write(f"- **Killed:** {killed} ({killed*100//len(mutants) if mutants else 0}%)\n")
            f.write(f"- **Survived:** {survived} ({survived*100//len(mutants) if mutants else 0}%)\n")
            f.write(f"- **Errors:** {errors}\n")
            f.write(f"- **Timeouts:** {timeouts}\n")
            f.write(f"- **Mutation Score:** {killed*100//(killed+survived) if (killed+survived) > 0 else 0}%\n\n")
        
        # Operator summary
        f.write("## Mutation Operators Summary\n\n")
        f.write("| Operator | Count | Killed | Survived | Description |\n")
        f.write("|----------|-------|--------|----------|-------------|\n")
        
        operator_names = {
            "AOR": "Arithmetic Operator Replacement",
            "ROR": "Relational Operator Replacement",
            "LCR": "Logical Connector Replacement",
            "CDL": "Constant Replacement",
            "UOI": "Unary Operator Insertion",
            "RIL": "Return Statement Mutation",
            "STR": "String Mutation",
            "MSI": "Method Call Modification",
            "IOD": "In/Not in Operator",
            "TYP": "Type Check Mutation",
            "DCI": "Dictionary/Container Operations",
            "FCR": "Function Call Replacement",
        }
        
        for op in sorted(by_operator.keys()):
            muts = by_operator[op]
            killed = len([m for m in muts if m.status == 'KILLED'])
            survived = len([m for m in muts if m.status == 'SURVIVED'])
            desc = operator_names.get(op, "Unknown")
            f.write(f"| {op} | {len(muts)} | {killed} | {survived} | {desc} |\n")
        
        # Routine summary
        f.write("\n## Results by Routine/Function\n\n")
        f.write("| Routine | Total | Killed | Survived |\n")
        f.write("|---------|-------|--------|----------|\n")
        
        for routine in sorted(by_routine.keys()):
            muts = by_routine[routine]
            killed = len([m for m in muts if m.status == 'KILLED'])
            survived = len([m for m in muts if m.status == 'SURVIVED'])
            f.write(f"| {routine} | {len(muts)} | {killed} | {survived} |\n")
        
        # Survived mutants section
        if 'SURVIVED' in by_status and by_status['SURVIVED']:
            f.write("\n## Survived Mutants (For Analysis)\n\n")
            f.write("These mutants were not killed by tests and need investigation:\n\n")
            
            for mutant in by_status['SURVIVED'][:10]:  # Show first 10
                f.write(f"### Mutant #{mutant.id} - {mutant.operator}\n\n")
                f.write(f"**Routine:** `{mutant.routine_name}`  \n")
                f.write(f"**Line:** {mutant.line_number}  \n")
                f.write(f"**Description:** {mutant.description}\n\n")
                f.write("**Original:**\n```python\n")
                f.write(mutant.original_code + "\n")
                f.write("```\n\n")
                f.write("**Mutated:**\n```python\n")
                f.write(mutant.mutated_code + "\n")
                f.write("```\n\n")
                f.write("**Analysis Required:** Determine if this is an equivalent mutant or if a new test is needed.\n\n")
                f.write("---\n\n")
        
        # Detailed mutants section
        f.write("\n## All Mutants (Detailed)\n\n")
        
        for mutant in mutants:
            f.write(f"### Mutant #{mutant.id}\n\n")
            f.write(f"- **Operator:** {mutant.operator}\n")
            f.write(f"- **Routine:** {mutant.routine_name}\n")
            f.write(f"- **Line:** {mutant.line_number}\n")
            f.write(f"- **Status:** {mutant.status}\n")
            f.write(f"- **Description:** {mutant.description}\n\n")
            f.write("**Original Code:**\n```python\n")
            f.write(mutant.original_code + "\n")
            f.write("```\n\n")
            f.write("**Mutated Code:**\n```python\n")
            f.write(mutant.mutated_code + "\n")
            f.write("```\n\n")
            
            f.write(f"**Unified Diff:** See `consolidated_mutations.diff` (Mutant #{mutant.id})\n\n")
            
            if mutant.test_output and run_tests:
                f.write("<details>\n<summary>Test Output</summary>\n\n```\n")
                f.write(mutant.test_output[:1000])  # First 1000 chars
                f.write("\n```\n</details>\n\n")
            
            f.write("---\n\n")
    
    # Save JSON for programmatic analysis
    json_file = output_dir / "mutation_results.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump([asdict(m) for m in mutants], f, indent=2)
    
    # Create consolidated diff file
    consolidated_diff = output_dir / "consolidated_mutations.diff"
    with open(consolidated_diff, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("CONSOLIDATED MUTATION DIFF FILE\n")
        f.write("FastAPI encoders.py - All Mutations\n")
        f.write(f"Total Mutants: {len(mutants)}\n")
        if run_tests:
            killed = len([m for m in mutants if m.status == 'KILLED'])
            survived = len([m for m in mutants if m.status == 'SURVIVED'])
            f.write(f"Killed: {killed}, Survived: {survived}\n")
        f.write("=" * 80 + "\n\n")
        
        for mutant in mutants:
            f.write(f"Mutant #{mutant.id:03d} - {mutant.operator} - {mutant.status}\n")
            f.write(f"Description: {mutant.description}\n")
            f.write(f"Routine: {mutant.routine_name}\n")
            f.write(f"{mutant.unified_diff}\n")
            f.write("-" * 80 + "\n\n")
    
    # Extract source code for tested routines
    source_file_path = Path(__file__).parent / "fastapi" / "encoders.py"
    with open(source_file_path, 'r', encoding='utf-8') as f:
        source_lines = f.readlines()
    
    routines = {
        'isoformat': (36, 37),
        'decimal_encoder': (42, 64),
        'generate_encoders_by_class_tuples': (97, 105),
        'jsonable_encoder': (111, 345)
    }
    
    routines_source = output_dir / "tested_routines_source.py"
    with open(routines_source, 'w', encoding='utf-8') as f:
        f.write('"""\n')
        f.write("SOURCE CODE FOR TESTED ROUTINES FROM fastapi/encoders.py\n")
        f.write("=" * 80 + '\n')
        f.write('"""\n\n')
        
        for routine_name, (start, end) in routines.items():
            f.write(f"\n{'#' * 80}\n")
            f.write(f"# ROUTINE: {routine_name}\n")
            f.write(f"# Lines: {start}-{end}\n")
            f.write(f"{'#' * 80}\n\n")
            
            for i in range(start - 1, end):
                f.write(source_lines[i])
            
            f.write("\n")
    
    print(f"Saved {len(mutants)} mutants to {output_dir}")
    print(f"Report: {report_file}")
    print(f"JSON: {json_file}")
    print(f"Consolidated diff: {consolidated_diff}")
    print(f"Routines source: {routines_source}")


def main():
    """Main execution"""
    script_dir = Path(__file__).parent
    target_file = script_dir / "fastapi" / "encoders.py"
    output_dir = script_dir / "mutation_output"
    
    # Check if we should run tests
    run_tests = '--run-tests' in sys.argv
    
    if not target_file.exists():
        print(f"Error: {target_file} not found!")
        print(f"Current directory: {Path.cwd()}")
        return 1
    
    print("="*70)
    print("FastAPI encoders.py Mutation Testing Script")
    print("="*70)
    print(f"Target file: {target_file}")
    print(f"Output directory: {output_dir}")
    print(f"Run tests: {run_tests}")
    
    print(f"\nReading {target_file}...")
    with open(target_file, 'r', encoding='utf-8') as f:
        source_code = f.read()
    
    source_lines = source_code.split('\n')
    print(f"Total lines: {len(source_lines)}")
    
    print("\nGenerating mutants...")
    mutants = generate_mutants(source_lines)
    print(f"Generated {len(mutants)} mutants")
    
    if len(mutants) < 100:
        print(f"Warning: Only {len(mutants)} mutants generated (target: 100+)")
    
    if run_tests:
        print("\nRunning mutation testing (this will take a while)...")
        backup_file = target_file.with_suffix('.py.backup')
        shutil.copy2(target_file, backup_file)
        
        try:
            for i, mutant in enumerate(mutants, 1):
                print(f"Testing mutant {i}/{len(mutants)}: {mutant.operator} at line {mutant.line_number}...", end=' ')
                status, output = run_tests_for_mutant(mutant, target_file, backup_file)
                mutant.status = status
                mutant.test_output = output
                print(status)
                
                # Save progress every 10 mutants
                if i % 10 == 0:
                    save_comprehensive_report(mutants, output_dir, run_tests=True)
        finally:
            # Restore original file
            if backup_file.exists():
                shutil.copy2(backup_file, target_file)
                backup_file.unlink()
    
    save_comprehensive_report(mutants, output_dir, run_tests=run_tests)
    
    print(f"\n{'='*70}")
    print(f"✅ Mutation testing complete!")
    print(f"Total mutants: {len(mutants)}")
    if run_tests:
        killed = len([m for m in mutants if m.status == 'KILLED'])
        survived = len([m for m in mutants if m.status == 'SURVIVED'])
        print(f"Killed: {killed}")
        print(f"Survived: {survived}")
        if killed + survived > 0:
            print(f"Mutation Score: {killed*100//(killed+survived)}%")
    print(f"Output directory: {output_dir}")
    print(f"{'='*70}\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
