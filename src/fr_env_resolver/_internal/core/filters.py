# Copyright (C) 2024 Floating Rock Studio Ltd
# This file is incomplete, the intention was to have auto checks for installed solftware, access levels, etc
# # match types
# # is/=: direct compare
# # contains: list contains item
# # in: item in rlist
# # contains_expr: list contains item matching regex
# # expr_in: regex matches item in rlist
# # # numerical
# # >, >=, <, <=
# # # prefix
# # not/!: inverts the operation

# # # combiners
# # {"$and/$or": [filters]}


# # string formatting filters:
# # "${system.os}", "${user.name}", "${user.access_level}"
# # "${user.access_level}"
# # evaluates to globals()["user"]["access_level"]
# # maybe do this later?

# import logging

# logger = logging.getLogger("fr_env_resolver.filters")


# from dataclasses import dataclass, field
# from typing import List
# import re

# import winreg

# reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
# reg_key = winreg.OpenKey(reg, r"SOFTWARE\MICROSOFT\Windows\CurrentVersion\Uninstall")
# apps = []
# for i in range(winreg.QueryInfoKey(reg_key)[0]):
#     try:
#         key_name = winreg.EnumKey(reg_key, i)
#         key = winreg.OpenKey(reg_key, key_name)
#         name = winreg.QueryValueEx(key, "DisplayName")[0]
#     except Exception as e:
#         print("Error", e)
#     else:
#         apps.append(name)


# @dataclass
# class System:
#     os: str = "windows"
#     installed_apps: List[str] = apps
#     # platform, gpu, ram, etc


# @dataclass
# class Groups:
#     User: str = "user"
#     Lead: str = "lead"
#     TechArtist: str = "tech_artist"
#     Developer: str = "developer"
#     IT: str = "IT"


# @dataclass
# class User:
#     login: str = "getuser"
#     email: str
#     full_name: str
#     first_name: str
#     last_name: str
#     groups: List[str] = field(default_factory=list)
#     # region, timezone, etc?


# def _is_complex_filter(filter):
#     return isinstance(filter, dict) and next(filter.keys(), None) in ("$and", "$or", "$any")


# def _resolve_vars(string):
#     if match := re.match("^\${([_\.a-zA-Z0-9]+)}$", string):
#         var = match.group(1)
#         vars = var.split(".")

#         # TODO: constant this
#         data = {
#             "user": User(),
#             "system": System(),
#         }
#         if vars[0] in data:
#             obj = data[var]
#             for var in vars[1:]:
#                 if obj is None:
#                     return None
#                 obj = getattr(var, None)
#         else:
#             return string  # no match

#     # todo: multiple matches, expressions (var+1)
#     return string


# def _check_filter(filter):
#     if len(filter) == 3:
#         a, op, b = filter
#         a = _resolve_vars(a)
#         b = _resolve_vars(b)
#         invert = False
#         if match := re.match("(!|not )(.*)", op, re.IGNORECASE):
#             invert = True
#             op = match.group(2)

#         op = op.strip()
#         if op in ("=", "is"):
#             result = a == b
#         elif op == ">":
#             result = a > b
#         elif op == ">=":
#             result = a >= b
#         elif op == "<":
#             result = a < b
#         elif op == "<=":
#             result = a <= b

#         elif op == "in":
#             result = a in b
#         elif op == "contains":
#             result = b in a

#         elif op in ("matches", "expr"):
#             try:
#                 expr = re.compile(b)
#             except Exception as e:
#                 print(f"Invalid expression: {b} ({e})")
#                 result = False
#             else:
#                 result = bool(expr.match(a))

#         elif op == "expr_in":
#             try:
#                 expr = re.compile(a)
#             except Exception as e:
#                 print(f"Invalid expression: {a} ({e})")
#                 result = False
#             else:
#                 result = any(expr.match(v) for v in b)

#         elif op == "contains_expr":
#             try:
#                 expr = re.compile(b)
#             except Exception as e:
#                 print(f"Invalid expression: {b} ({e})")
#                 result = False
#             else:
#                 result = any(expr.match(v) for v in a)

#         if invert:
#             return not result

#     else:
#         print(f"Unsupported filter: {filter}")
#         # unknown filter
#         return False


# def check_filters(filters):
#     success = True
#     for each in filters:
#         if isinstance(each, dict):
#             # $and, $or, $any
#             for k, v in each.items():
#                 if k == "$and":
#                     if not all(check_filters(c) if _is_complex_filter(c) else _check_filter(c) for c in v):
#                         success = False
#                 if k in ("$or", "$any"):
#                     if not any(check_filters(c) if _is_complex_filter(c) else _check_filter(c) for c in v):
#                         success = False

#         elif isinstance(each, list):
#             if not _check_filter(each):
#                 success = False
#     return success
