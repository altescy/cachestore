from __future__ import annotations

import ast
import itertools


class ASTNormalizer(ast.NodeTransformer):
    def __init__(self) -> None:
        self.global_name_counter = itertools.count()
        self.scoped_name_counter = itertools.count()
        self.global_name_mapping: dict[str, str] = {}
        self.scope_stack: list[dict[str, str]] = [{}]

    def find_name_in_scopes(self, name: str) -> str | None:
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]
        return None

    def visit_Name(self, node: ast.Name) -> ast.Name:
        new_name = self.find_name_in_scopes(node.id)
        if new_name is not None:
            node.id = new_name
        return node

    def visit_arg(self, node: ast.arg) -> ast.arg:
        new_name = self.find_name_in_scopes(node.arg)
        if new_name is not None:
            node.arg = new_name
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        if node.name not in self.global_name_mapping:
            self.global_name_mapping[node.name] = f"var{next(self.global_name_counter)}"
        node.name = self.global_name_mapping[node.name]
        self.scope_stack.append({})
        self.scoped_name_counter = itertools.count()
        for arg in node.args.args:
            new_name = f"var{next(self.scoped_name_counter)}"
            self.scope_stack[-1][arg.arg] = new_name
        self.generic_visit(node)
        self.scope_stack.pop()
        return node

    def visit_Assign(self, node: ast.Assign) -> ast.Assign:
        for target in node.targets:
            if isinstance(target, ast.Name):
                new_name = self.find_name_in_scopes(target.id)
                if new_name is None:
                    new_name = f"var{next(self.scoped_name_counter)}"
                    self.scope_stack[-1][target.id] = new_name
                target.id = new_name
        self.generic_visit(node)
        return node
