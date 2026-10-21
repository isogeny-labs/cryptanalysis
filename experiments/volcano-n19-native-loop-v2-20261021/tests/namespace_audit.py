"""Static audit of the globals that arm_n2x.sage and diagnosis/profile_n.sage share with v3.

Both scripts execute v3 arm.sage (minus `main()`) in their own module globals, and v3 arm.sage
`load`s ../volcano-ic/run.sage (which loads ic.sage) and tau.sage into those same globals
(run.sage also loads tau.sage and nbsat.sage inside one function; both are included). So any
module-level name is shared. Two failure modes are checked:

* clobber: the script binds a name before the v3 code runs, the v3 code (or a file it loads)
  rebinds it, and the script reads it afterwards. This is v1's defect: `_argv` (bound at
  arm_n2x.sage line 36, rebound by v3 arm.sage line 62, read at line 41).
* shadow: the script binds, after the v3 code, a name that v3 code outside v3's own `main`
  reads as a global, which would change the baseline's behaviour inside N2X or the profile.

Imports of the same module under the same name are not collisions. Sources are parsed after
the emulated preparse (sage_emulation.preparse), so the parser sees what Python runs.
"""
import ast
import os

import sage_emulation as se

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
EXPERIMENTS = os.path.dirname(EXP)
V3_ARM = os.path.join(EXPERIMENTS, 'volcano-n19-native-tau6-v3-20261020', 'arm.sage')
VIC = os.path.join(EXPERIMENTS, 'volcano-ic')
LOADED = [os.path.join(VIC, f) for f in ('run.sage', 'ic.sage', 'tau.sage', 'nbsat.sage')]


def parse(path, strip_main=False):
    text = open(path).read()
    if strip_main:
        text = text.rstrip()
        assert text.endswith('\nmain()')
        text = text[:-len('main()')]
    if path.endswith('.sage'):
        text = se.preparse(text)
    return ast.parse(text, path)


def _targets(node, out):
    if isinstance(node, ast.Name):
        out.add(node.id)
    elif isinstance(node, (ast.Tuple, ast.List)):
        for e in node.elts:
            _targets(e, out)
    elif isinstance(node, ast.Starred):
        _targets(node.value, out)


def stmt_bindings(stmt):
    """Module-level names one top-level statement binds, and {name: module} for imports."""
    out, imports = set(), {}
    for node in ast.walk(stmt) if not isinstance(stmt, (ast.FunctionDef, ast.ClassDef)) else [stmt]:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                _targets(t, out)
        elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
            _targets(node.target, out)
        elif isinstance(node, (ast.For, ast.comprehension)):
            _targets(node.target, out)
        elif isinstance(node, ast.withitem) and node.optional_vars is not None:
            _targets(node.optional_vars, out)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for a in node.names:
                name = a.asname or a.name.split('.')[0]
                out.add(name)
                imports[name] = (getattr(node, 'module', None), a.name)
        elif isinstance(node, ast.NamedExpr):
            _targets(node.target, out)
    return out, imports


def global_decls(tree):
    """Names declared `global` inside any function: rebound at module level when it runs."""
    return {n for node in ast.walk(tree) if isinstance(node, ast.Global) for n in node.names}


def module_bindings(tree):
    names, imports = set(), {}
    for stmt in tree.body:
        b, i = stmt_bindings(stmt)
        names |= b
        imports.update(i)
    return names | global_decls(tree), imports


def global_reads(nodes, exclude_functions=()):
    """Names read as globals in `nodes` (module statements and the bodies of their functions)."""
    reads = set()

    def fn_locals(fn):
        loc = {a.arg for a in ast.walk(fn.args) if isinstance(a, ast.arg)}
        glob = set()
        for n in ast.walk(fn):
            if isinstance(n, ast.Global):
                glob |= set(n.names)
            elif isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
                loc.add(n.id)
            elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n is not fn:
                loc.add(n.name)
            elif isinstance(n, (ast.Import, ast.ImportFrom)):
                loc |= {a.asname or a.name.split('.')[0] for a in n.names}
        return loc - glob

    def visit(node, local):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            if getattr(node, 'name', None) in exclude_functions:
                return
            inner = local | (fn_locals(node) if not isinstance(node, ast.Lambda)
                             else {a.arg for a in ast.walk(node.args) if isinstance(a, ast.arg)})
            for d in getattr(node, 'decorator_list', []):
                visit(d, local)
            for child in (node.body if isinstance(node.body, list) else [node.body]):
                visit(child, inner)
            return
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id not in local:
            reads.add(node.id)
        for child in ast.iter_child_nodes(node):
            visit(child, local)

    for n in nodes:
        visit(n, set())
    return reads


def v3_namespace():
    """Names the v3 code binds in the shared globals, its imports, and its global reads outside main."""
    names, imports, reads = set(), {}, set()
    for path, strip in [(V3_ARM, True)] + [(p, False) for p in LOADED]:
        if not os.path.exists(path):
            continue
        tree = parse(path, strip)
        b, i = module_bindings(tree)
        names |= b
        imports.update(i)
        reads |= global_reads(tree.body, exclude_functions=('main',) if path == V3_ARM else ())
    return names, imports, reads


def split_at_v3(tree):
    """Index of the top-level statement that executes the v3 code (v2 call or v1 exec)."""
    for k, stmt in enumerate(tree.body):
        src = ast.dump(stmt)
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            f = stmt.value.func
            if isinstance(f, ast.Name) and f.id in ('exec', '_exec_v3_definitions'):
                return k
        del src
    raise AssertionError('no top-level statement executes the v3 code')


def audit(script):
    """{'clobbered': [...], 'shadowed': [...]} for one consumer script (empty lists = clean)."""
    tree = parse(script)
    k = split_at_v3(tree)
    before, b_imports = set(), {}
    for stmt in tree.body[:k]:
        b, i = stmt_bindings(stmt)
        before |= b
        b_imports.update(i)
    after = set()
    for stmt in tree.body[k + 1:]:
        after |= stmt_bindings(stmt)[0]
    # reads after the v3 code: later module statements and every function body (all run later)
    later = tree.body[k + 1:] + [s for s in tree.body[:k] if isinstance(s, (ast.FunctionDef, ast.ClassDef))]
    reads_after = global_reads(later)
    v3_names, v3_imports, v3_reads = v3_namespace()
    same_import = {n for n in before & v3_names if n in b_imports and v3_imports.get(n) == b_imports[n]}
    clobbered = sorted(((before & v3_names) - same_import - after) & reads_after)
    shadowed = sorted((after & v3_reads) - {'main'})
    return {'clobbered': clobbered, 'shadowed': shadowed, 'split_statement_line': tree.body[k].lineno}
