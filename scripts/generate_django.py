import argparse
import re
import sys
from pathlib import Path

import yaml

SCHEMA_PREFIX = "#/components/schemas/"
RELATION_TYPES = {"ForeignKey", "OneToOneField", "ManyToManyField"}
ACRONYMS = {"pdf", "pptx", "docx", "txt", "md", "ai"}
TIMESTAMP_FIELDS = ("created_at", "updated_at")
AUTH_TOKEN = "AUTH_USER_MODEL"
MAX_INDEX_NAME = 30
HTTP_METHODS = ("get", "post", "put", "patch", "delete")
PARSER_NAMES = ("FormParser", "JSONParser", "MultiPartParser")

SUPPORT_MODULE = """from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


def not_implemented():
    return Response({'detail': 'Not implemented.'}, status=status.HTTP_501_NOT_IMPLEMENTED)


def save_or_conflict(serializer, **kwargs):
    try:
        with transaction.atomic():
            return serializer.save(**kwargs)
    except IntegrityError:
        raise ValidationError({'detail': ['This change conflicts with an existing object.']}) from None
"""


def ref_name(ref):
    return ref[len(SCHEMA_PREFIX):]


def enum_label(value):
    text = value.replace("_", " ")
    return text.upper() if value in ACRONYMS else text.capitalize()


def snake(name):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def model_meta(schema):
    return schema["x-django-model"]


def auth_model_name(context):
    return context["auth_user_model"].split(".")[1]


def column_names(schema):
    names = [name for name, prop in schema["properties"].items() if "x-django-field" in prop]
    if model_meta(schema).get("timestamps"):
        names.extend(TIMESTAMP_FIELDS)
    return names


def relation_target(field, context):
    target = field["to"]
    return auth_model_name(context) if target == AUTH_TOKEN else target


def register_name(seen, name, owner):
    if name in seen:
        raise ValueError(f"duplicate index or constraint name {name!r} on {seen[name]} and {owner}")
    seen[name] = owner


def validate_model(name, schema, context):
    meta = model_meta(schema)
    if meta["app"] not in context["apps"]:
        raise ValueError(f"{name}: app {meta['app']!r} is not declared under x-django.apps")
    known = set(column_names(schema)) | {"id", "pk"}
    refs = list(meta.get("ordering") or [])
    for index in meta.get("indexes") or []:
        refs.extend(index["fields"])
    for constraint in meta.get("constraints") or []:
        if constraint["type"] == "unique":
            refs.extend(constraint["fields"])
    for ref in refs:
        if ref.lstrip("-") not in known:
            raise ValueError(f"{name}: unknown field {ref!r} referenced in Meta")
    str_field = meta.get("str_field")
    if str_field and str_field not in known:
        raise ValueError(f"{name}: str_field {str_field!r} is not a column")
    for prop_name, prop in schema["properties"].items():
        field = prop.get("x-django-field")
        if not field:
            continue
        if "$ref" in prop and ref_name(prop["$ref"]) not in context["enums"]:
            raise ValueError(f"{name}.{prop_name}: {prop['$ref']} is not an x-django-enum schema")
        if field["type"] in RELATION_TYPES and relation_target(field, context) not in context["models"]:
            raise ValueError(f"{name}.{prop_name}: relation target {field['to']!r} is not a model")


def check_names(context):
    seen = {}
    accessors = {}
    for name, schema in context["models"].items():
        meta = model_meta(schema)
        for index in meta.get("indexes") or []:
            if len(index["name"]) > MAX_INDEX_NAME:
                raise ValueError(f"{name}: index name {index['name']!r} is longer than {MAX_INDEX_NAME}")
            register_name(seen, index["name"], name)
        for constraint in meta.get("constraints") or []:
            register_name(seen, constraint["name"], name)
        for prop_name, prop in schema["properties"].items():
            field = prop.get("x-django-field")
            if not field or field["type"] not in RELATION_TYPES or not field.get("related_name"):
                continue
            key = (relation_target(field, context), field["related_name"])
            if key in accessors:
                raise ValueError(
                    f"reverse accessor {key[1]!r} on {key[0]} is used by both "
                    f"{accessors[key]} and {name}.{prop_name}"
                )
            accessors[key] = f"{name}.{prop_name}"


def app_dependencies(context):
    deps = {app: set() for app in context["apps"]}
    for schema in context["models"].values():
        app = model_meta(schema)["app"]
        for prop in schema["properties"].values():
            field = prop.get("x-django-field")
            if not field:
                continue
            if field["type"] in RELATION_TYPES:
                target = context["models"][relation_target(field, context)]
                deps[app].add(model_meta(target)["app"])
            if "$ref" in prop:
                deps[app].add(context["enums"][ref_name(prop["$ref"])]["app"])
    for app in deps:
        deps[app].discard(app)
    return deps


def order_apps(context):
    deps = app_dependencies(context)
    state = {}
    order = []

    def visit(app, trail):
        if state.get(app) == "done":
            return
        if state.get(app) == "active":
            cycle = trail[trail.index(app):] + [app]
            raise ValueError("circular app dependency: " + " -> ".join(cycle))
        state[app] = "active"
        for dep in sorted(deps[app]):
            visit(dep, trail + [app])
        state[app] = "done"
        order.append(app)

    for app in sorted(deps):
        visit(app, [])
    return order


def django_route(path):
    return re.sub(r"\{(\w+)\}", lambda match: f"<int:{snake(match.group(1))}>", path.strip("/"))


def action_name(url_path):
    return re.split(r"[/(]", url_path)[0].replace("-", "_")


def normalize_filters(entries):
    pairs = []
    for entry in entries:
        if isinstance(entry, dict):
            pairs.extend(entry.items())
        else:
            pairs.append((entry, entry))
    return pairs


def register_viewsets(spec, context, endpoints):
    prefixes = {app: config["url_prefix"] for app, config in spec["x-django"]["apps"].items()}
    for tag in spec.get("tags", []):
        app = tag.get("x-django-app")
        for config in tag.get("x-django-viewsets") or []:
            model = config["model"]
            if model not in context["models"] or model_meta(context["models"][model])["app"] != app:
                raise ValueError(f"{config['name']}: model {model!r} is not a model of app {app!r}")
            parsers = config.get("parser_classes") or []
            for parser in parsers:
                if parser not in PARSER_NAMES:
                    raise ValueError(f"{config['name']}: unsupported parser {parser!r}")
            route = "/".join(part for part in (prefixes[app], config["route"]) if part)
            endpoints[app]["viewsets"][config["name"]] = {
                "name": config["name"],
                "model": model,
                "route": route,
                "scope": config["queryset_scope"],
                "filters": normalize_filters(config.get("filterset_fields") or []),
                "search": config.get("search_fields") or [],
                "ordering": config.get("ordering_fields") or [],
                "parsers": parsers,
                "collection": {},
                "detail": {},
                "actions": {},
            }


def match_viewset(path, app, endpoints):
    segments = path.strip("/").split("/")
    for viewset in endpoints[app]["viewsets"].values():
        route = viewset["route"].split("/")
        if segments == route:
            return viewset, "collection"
        if len(segments) == len(route) + 1 and segments[:-1] == route and segments[-1].startswith("{"):
            return viewset, "detail"
    return None, None


def is_plain_create(operation, viewset):
    body = operation.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
    return body.get("$ref") == SCHEMA_PREFIX + viewset["model"] and "__" not in viewset["scope"]


def register_operations(spec, endpoints):
    for path, item in spec["paths"].items():
        for method in HTTP_METHODS:
            operation = item.get(method)
            if not operation:
                continue
            app = operation["tags"][0]
            where = f"{method.upper()} {path}"
            if "x-django-action" in operation:
                action = operation["x-django-action"]
                viewset = endpoints[app]["viewsets"].get(action["viewset"])
                if viewset is None:
                    raise ValueError(f"{where}: unknown viewset {action['viewset']!r}")
                entry = viewset["actions"].setdefault(
                    action["url_path"],
                    {
                        "name": action_name(action["url_path"]),
                        "detail": action["detail"],
                        "url_path": action["url_path"],
                        "methods": [],
                    },
                )
                if method not in entry["methods"]:
                    entry["methods"].append(method)
            elif "x-django-view" in operation:
                view = operation["x-django-view"]
                route = django_route(path)
                entry = endpoints[app]["views"].setdefault(
                    view["name"],
                    {
                        "name": view["name"],
                        "module": view.get("module"),
                        "route": route,
                        "methods": [],
                        "public": operation.get("security") == [],
                    },
                )
                if entry["route"] != route:
                    raise ValueError(f"{where}: view {view['name']} is already mounted at {entry['route']}")
                entry["methods"].append(method)
            else:
                viewset, kind = match_viewset(path, app, endpoints)
                if viewset is None:
                    raise ValueError(f"{where}: not an action or view and matches no viewset route")
                if kind == "collection":
                    if method not in ("get", "post"):
                        raise ValueError(f"{where}: collection routes support only get and post")
                    viewset["collection"][method] = {
                        "plain": is_plain_create(operation, viewset) if method == "post" else True
                    }
                else:
                    if method == "post":
                        raise ValueError(f"{where}: detail routes do not support post")
                    viewset["detail"][method] = {"plain": True}


def build_context(spec):
    schemas = spec["components"]["schemas"]
    config = spec["x-django"]
    enums = {}
    for key, schema in schemas.items():
        meta = schema.get("x-django-enum")
        if meta:
            if meta["app"] not in config["apps"]:
                raise ValueError(f"enum {meta['name']}: app {meta['app']!r} is not declared under x-django.apps")
            enums[key] = {"name": meta["name"], "app": meta["app"], "values": list(schema["enum"])}
    context = {
        "schemas": schemas,
        "apps": list(config["apps"]),
        "auth_user_model": config["auth_user_model"],
        "enums": enums,
        "models": {name: schema for name, schema in schemas.items() if "x-django-model" in schema},
    }
    if auth_model_name(context) not in context["models"]:
        raise ValueError(f"auth_user_model {context['auth_user_model']!r} is not a model in the spec")
    for name, schema in context["models"].items():
        validate_model(name, schema, context)
    check_names(context)
    context["app_order"] = order_apps(context)
    endpoints = {app: {"viewsets": {}, "views": {}} for app in context["apps"]}
    register_viewsets(spec, context, endpoints)
    register_operations(spec, endpoints)
    context["endpoints"] = endpoints
    return context


def render_enum(enum):
    lines = [f"class {enum['name']}(models.TextChoices):"]
    for value in enum["values"]:
        lines.append(f"    {value.upper()} = {value!r}, {enum_label(value)!r}")
    return "\n".join(lines)


def render_target(app, field, context):
    if field["to"] == AUTH_TOKEN:
        return "settings.AUTH_USER_MODEL"
    target = field["to"]
    target_app = model_meta(context["models"][target])["app"]
    return repr(target if target_app == app else f"{target_app}.{target}")


def render_field(app, model_name, field_name, prop, context, imports):
    spec = dict(prop["x-django-field"])
    field_type = spec.pop("type")
    enum = context["enums"].get(ref_name(prop["$ref"])) if "$ref" in prop else None
    args = []
    kwargs = []

    if field_type in RELATION_TYPES:
        args.append(render_target(app, spec, context))
        spec.pop("to")
    on_delete = spec.pop("on_delete", None)
    if on_delete:
        kwargs.append(f"on_delete=models.{on_delete}")

    validators = []
    min_value = spec.pop("min_value", None)
    max_value = spec.pop("max_value", None)
    if min_value is not None:
        validators.append(f"MinValueValidator({min_value!r})")
    if max_value is not None:
        validators.append(f"MaxValueValidator({max_value!r})")

    factory = spec.pop("default_factory", None)
    if factory:
        kwargs.append(f"default={factory}")

    if enum:
        longest = max(len(value) for value in enum["values"])
        max_length = spec.get("max_length")
        if max_length is not None and max_length < longest:
            raise ValueError(
                f"{model_name}.{field_name}: max_length {max_length} is shorter than "
                f"the longest {enum['name']} value ({longest})"
            )
        if enum["app"] != app:
            imports.setdefault(enum["app"], set()).add(enum["name"])
        kwargs.append(f"choices={enum['name']}.choices")

    for key, value in spec.items():
        if key == "default" and enum and value in enum["values"]:
            kwargs.append(f"default={enum['name']}.{value.upper()}")
        else:
            kwargs.append(f"{key}={value!r}")

    if validators:
        kwargs.append(f"validators=[{', '.join(validators)}]")

    return f"    {field_name} = models.{field_type}({', '.join(args + kwargs)})"


def render_constraint(constraint):
    kind = constraint["type"]
    if kind == "unique":
        parts = [f"fields={constraint['fields']!r}", f"name={constraint['name']!r}"]
        if constraint.get("condition"):
            parts.append(f"condition={constraint['condition']}")
        return f"models.UniqueConstraint({', '.join(parts)})"
    if kind == "check":
        return f"models.CheckConstraint(condition={constraint['condition']}, name={constraint['name']!r})"
    raise ValueError(f"unsupported constraint type {kind!r}")


def render_meta(meta):
    lines = []
    if meta.get("ordering"):
        lines.append(f"        ordering = {meta['ordering']!r}")
    indexes = meta.get("indexes") or []
    if indexes:
        lines.append("        indexes = [")
        for index in indexes:
            lines.append(
                f"            models.Index(fields={index['fields']!r}, name={index['name']!r}),"
            )
        lines.append("        ]")
    constraints = meta.get("constraints") or []
    if constraints:
        lines.append("        constraints = [")
        for constraint in constraints:
            lines.append(f"            {render_constraint(constraint)},")
        lines.append("        ]")
    if not lines:
        return []
    return ["", "    class Meta:", *lines]


def render_model(app, name, schema, context, imports):
    meta = model_meta(schema)
    base = meta.get("base")
    lines = [f"class {name}({base['name'] if base else 'models.Model'}):"]
    for field_name, prop in schema["properties"].items():
        if "x-django-field" in prop:
            lines.append(render_field(app, name, field_name, prop, context, imports))
    if meta.get("timestamps"):
        lines.append("    created_at = models.DateTimeField(auto_now_add=True)")
        lines.append("    updated_at = models.DateTimeField(auto_now=True)")
    lines.extend(render_meta(meta))
    if meta.get("str_field"):
        lines.extend(["", "    def __str__(self):", f"        return str(self.{meta['str_field']})"])
    return "\n".join(lines)


def app_models(app, context):
    return {
        name: schema
        for name, schema in context["models"].items()
        if model_meta(schema)["app"] == app
    }


def render_app_models(app, context):
    models = app_models(app, context)
    imports = {}
    blocks = [render_enum(enum) for enum in context["enums"].values() if enum["app"] == app]
    blocks.extend(render_model(app, name, schema, context, imports) for name, schema in models.items())
    body = "\n\n\n".join(blocks)

    django_lines = {"from django.db import models"}
    if "settings.AUTH_USER_MODEL" in body:
        django_lines.add("from django.conf import settings")
    validators = [name for name in ("MaxValueValidator", "MinValueValidator") if name in body]
    if validators:
        django_lines.add(f"from django.core.validators import {', '.join(validators)}")
    for schema in models.values():
        base = model_meta(schema).get("base")
        if base:
            django_lines.add(f"from {base['module']} import {base['name']}")

    header = "\n".join(sorted(django_lines))
    local = "\n".join(
        f"from {other}.models import {', '.join(sorted(names))}"
        for other, names in sorted(imports.items())
    )
    if local:
        header += "\n\n" + local
    return header + "\n\n\n" + body + "\n"


def render_serializer(serializer, model, fields, read_only):
    return "\n".join(
        [
            f"class {serializer}(serializers.ModelSerializer):",
            "    class Meta:",
            f"        model = {model}",
            f"        fields = {fields!r}",
            f"        read_only_fields = {read_only!r}",
        ]
    )


def serializable_models(app, context):
    return {
        name: schema
        for name, schema in app_models(app, context).items()
        if model_meta(schema).get("serializer") is not False
    }


def render_app_serializers(app, context):
    blocks = []
    names = []
    for name, schema in serializable_models(app, context).items():
        columns = column_names(schema)
        props = schema["properties"]
        fields = ["id", *columns]
        read_only = ["id"] + [
            column
            for column in columns
            if column in TIMESTAMP_FIELDS or props.get(column, {}).get("readOnly")
        ]
        names.append(name)
        blocks.append(render_serializer(f"{name}Serializer", name, fields, read_only))
        public = context["schemas"].get(f"{name}Public")
        if public:
            public_fields = ["id"] + [prop for prop in public["properties"] if prop in columns]
            blocks.append(
                render_serializer(f"{name}PublicSerializer", name, public_fields, public_fields)
            )
    if not blocks:
        return None
    header = (
        "from rest_framework import serializers\n\n"
        f"from .models import {', '.join(names)}\n\n\n"
    )
    return header + "\n\n\n".join(blocks) + "\n"


def filter_kind(model_name, path, context):
    parts = path.split("__")
    current = model_name
    for index, part in enumerate(parts):
        prop = context["models"][current]["properties"].get(part)
        if not prop or "x-django-field" not in prop:
            raise ValueError(f"{model_name}: filter lookup {path!r} does not resolve ({part!r} is not a column of {current})")
        field = prop["x-django-field"]
        if index < len(parts) - 1:
            if field["type"] not in RELATION_TYPES:
                raise ValueError(f"{model_name}: filter lookup {path!r} crosses non-relation {part!r}")
            current = relation_target(field, context)
    if field["type"] == "BooleanField":
        return "BooleanFilter"
    if "$ref" in prop or field["type"] in ("CharField", "TextField"):
        return "CharFilter"
    return "NumberFilter"


def filterset_name(viewset):
    return viewset["name"].replace("ViewSet", "") + "Filter"


def render_filterset(viewset, context):
    lines = [f"class {filterset_name(viewset)}(filters.FilterSet):"]
    for param, path in viewset["filters"]:
        kind = filter_kind(viewset["model"], path, context)
        lines.append(f"    {param} = filters.{kind}(field_name={path!r})")
    lines.extend(["", "    class Meta:", f"        model = {viewset['model']}", "        fields = []"])
    return "\n".join(lines)


def render_action(action):
    name = action["name"]
    arguments = [
        f"detail={action['detail']}",
        f"methods={action['methods']!r}",
        f"url_path={action['url_path']!r}",
    ]
    lines = [
        "",
        f"    @action({', '.join(arguments)})",
        f"    def {name}(self, request, *args, **kwargs):",
        "        method = request.method.lower()",
        "        method = 'get' if method == 'head' else method",
        "        return getattr(self, f'handle_" + name + "_{method}')(request, *args, **kwargs)",
    ]
    for method in action["methods"]:
        lines.extend(
            ["", f"    def handle_{name}_{method}(self, request, *args, **kwargs):", "        return not_implemented()"]
        )
    return lines


def render_viewset(viewset):
    model = viewset["model"]
    scope = viewset["scope"]
    collection = viewset["collection"]
    detail = viewset["detail"]
    plain_create = bool(collection.get("post", {}).get("plain"))

    mixin_names = []
    if "get" in collection:
        mixin_names.append("ListModelMixin")
    if plain_create:
        mixin_names.append("CreateModelMixin")
    if "get" in detail:
        mixin_names.append("RetrieveModelMixin")
    if "put" in detail or "patch" in detail:
        mixin_names.append("UpdateModelMixin")
    if "delete" in detail:
        mixin_names.append("DestroyModelMixin")
    bases = ", ".join([f"mixins.{name}" for name in mixin_names] + ["viewsets.GenericViewSet"])

    methods = set(collection) | set(detail)
    for action in viewset["actions"].values():
        methods.update(action["methods"])
    allowed = sorted(methods) + ["head", "options"]

    lines = [
        f"class {viewset['name']}Base({bases}):",
        f"    serializer_class = {model}Serializer",
        "    permission_classes = [IsAuthenticated]",
        f"    http_method_names = {allowed!r}",
        "    lookup_value_regex = '[0-9]+'",
    ]
    if "get" in collection:
        lines.append("    pagination_class = StandardPagination")
    backends = []
    if viewset["filters"]:
        backends.append("filters.DjangoFilterBackend")
        lines.append(f"    filterset_class = {filterset_name(viewset)}")
    if viewset["search"]:
        backends.append("SearchFilter")
        lines.append(f"    search_fields = {viewset['search']!r}")
    if viewset["ordering"]:
        backends.append("OrderingFilter")
        lines.append(f"    ordering_fields = {viewset['ordering']!r}")
    if backends:
        lines.append(f"    filter_backends = [{', '.join(backends)}]")
    if viewset["parsers"]:
        lines.append(f"    parser_classes = [{', '.join(viewset['parsers'])}]")

    lines.extend(
        ["", "    def get_queryset(self):", f"        return {model}.objects.filter({scope}=self.request.user)"]
    )
    if plain_create:
        lines.extend(
            [
                "",
                "    def perform_create(self, serializer):",
                f"        save_or_conflict(serializer, {scope}=self.request.user)",
            ]
        )
    if "put" in detail or "patch" in detail:
        lines.extend(["", "    def perform_update(self, serializer):", "        save_or_conflict(serializer)"])
    if "post" in collection and not plain_create:
        lines.extend(
            [
                "",
                "    def create(self, request, *args, **kwargs):",
                "        return self.handle_create(request, *args, **kwargs)",
                "",
                "    def handle_create(self, request, *args, **kwargs):",
                "        return not_implemented()",
            ]
        )
    for action in viewset["actions"].values():
        lines.extend(render_action(action))
    return "\n".join(lines)


def render_view(view):
    permission = "AllowAny" if view["public"] else "IsAuthenticated"
    lines = [f"class {view['name']}Base(APIView):", f"    permission_classes = [{permission}]"]
    for method in view["methods"]:
        lines.extend(["", f"    def {method}(self, request, *args, **kwargs):", "        return not_implemented()"])
    return "\n".join(lines)


def app_view_classes(app, context):
    endpoints = context["endpoints"][app]
    viewsets = list(endpoints["viewsets"].values())
    views = [view for view in endpoints["views"].values() if not view["module"]]
    return viewsets, views


def render_app_views_base(app, context):
    viewsets, views = app_view_classes(app, context)
    if not viewsets and not views:
        return None
    blocks = [render_filterset(viewset, context) for viewset in viewsets if viewset["filters"]]
    blocks.extend(render_viewset(viewset) for viewset in viewsets)
    blocks.extend(render_view(view) for view in views)
    body = "\n\n\n".join(blocks)

    third_party = []
    if "filters." in body:
        third_party.append("from django_filters import rest_framework as filters")
    framework = [name for name in ("mixins", "viewsets") if f"{name}." in body]
    if framework:
        third_party.append(f"from rest_framework import {', '.join(framework)}")
    if "@action" in body:
        third_party.append("from rest_framework.decorators import action")
    backends = [name for name in ("OrderingFilter", "SearchFilter") if name in body]
    if backends:
        third_party.append(f"from rest_framework.filters import {', '.join(backends)}")
    parsers = [name for name in PARSER_NAMES if name in body]
    if parsers:
        third_party.append(f"from rest_framework.parsers import {', '.join(parsers)}")
    permissions = [name for name in ("AllowAny", "IsAuthenticated") if name in body]
    if permissions:
        third_party.append(f"from rest_framework.permissions import {', '.join(permissions)}")
    if "APIView" in body:
        third_party.append("from rest_framework.views import APIView")

    local = []
    support = [name for name in ("StandardPagination", "not_implemented", "save_or_conflict") if name in body]
    if support:
        local.append(f"from api_support import {', '.join(support)}")
    models = sorted({viewset["model"] for viewset in viewsets})
    if models:
        local.append(f"from .models import {', '.join(models)}")
        local.append(f"from .serializers import {', '.join(f'{model}Serializer' for model in models)}")

    header = "\n".join(third_party)
    if local:
        header += "\n\n" + "\n".join(local)
    return header + "\n\n\n" + body + "\n"


def render_app_views(app, context):
    viewsets, views = app_view_classes(app, context)
    names = [viewset["name"] for viewset in viewsets] + [view["name"] for view in views]
    if not names:
        return None
    header = f"from .views_base import {', '.join(f'{name}Base' for name in names)}\n\n\n"
    blocks = [f"class {name}({name}Base):\n    pass" for name in names]
    return header + "\n\n\n".join(blocks) + "\n"


def url_name(view_name):
    return snake(view_name.removesuffix("View"))


def render_app_urls(app, context):
    endpoints = context["endpoints"][app]
    viewsets = sorted(
        endpoints["viewsets"].values(),
        key=lambda viewset: (-len(viewset["route"].split("/")), viewset["name"]),
    )
    views = list(endpoints["views"].values())
    if not viewsets and not views:
        return None
    external = {}
    for view in views:
        if view["module"]:
            external.setdefault(view["module"], []).append(view["name"])

    third_party = []
    if views:
        third_party.append("from django.urls import path")
    if viewsets:
        third_party.append("from rest_framework.routers import SimpleRouter")
    for module, names in external.items():
        third_party.append(f"from {module} import {', '.join(sorted(names))}")
    third_party.sort()

    lines = ["\n".join(third_party)]
    if viewsets or any(not view["module"] for view in views):
        lines[0] += "\n\nfrom . import views"
    lines.extend(["", f"app_name = {app!r}"])
    if viewsets:
        lines.extend(["", "router = SimpleRouter(trailing_slash=False)"])
        for viewset in viewsets:
            basename = snake(viewset["model"])
            lines.append(
                f"router.register({viewset['route']!r}, views.{viewset['name']}, basename={basename!r})"
            )
    lines.extend(["", "urlpatterns = ["])
    for view in views:
        target = view["name"] if view["module"] else f"views.{view['name']}"
        lines.append(f"    path({view['route']!r}, {target}.as_view(), name={url_name(view['name'])!r}),")
    if viewsets:
        lines.append("    *router.urls,")
    lines.append("]")
    return "\n".join(lines) + "\n"


def render_root_urls(apps):
    lines = ["from django.urls import include, path", "", "", "urlpatterns = ["]
    lines.extend(f"    path('', include('{app}.urls'))," for app in apps)
    lines.append("]")
    return "\n".join(lines) + "\n"


def render_all(context):
    generated = {}
    scaffold = {}
    routed = []
    for app in context["app_order"]:
        if app_models(app, context):
            generated[Path(app) / "models.py"] = render_app_models(app, context)
            serializers = render_app_serializers(app, context)
            if serializers:
                generated[Path(app) / "serializers.py"] = serializers
        views_base = render_app_views_base(app, context)
        urls = render_app_urls(app, context)
        if urls:
            routed.append(app)
            generated[Path(app) / "urls.py"] = urls
        if views_base:
            generated[Path(app) / "views_base.py"] = views_base
            scaffold[Path(app) / "views.py"] = render_app_views(app, context)
    generated[Path("api_support.py")] = SUPPORT_MODULE
    generated[Path("api_urls.py")] = render_root_urls(routed)
    return generated, scaffold


def class_names(source):
    return re.findall(r"^class (\w+)\(", source, re.MULTILINE)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate per-app Django models, serializers, views and URLs from the OpenAPI spec."
    )
    parser.add_argument("spec", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    spec = yaml.safe_load(args.spec.read_text(encoding="utf-8"))
    context = build_context(spec)
    generated, scaffold = render_all(context)

    drift = False
    for relative, content in generated.items():
        target = args.out / relative
        if args.check:
            if not target.exists() or target.read_text(encoding="utf-8") != content:
                print(f"out of date: {target}", file=sys.stderr)
                drift = True
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            print(f"wrote {target}")

    for relative, content in scaffold.items():
        target = args.out / relative
        if target.exists():
            missing = sorted(set(class_names(content)) - set(class_names(target.read_text(encoding="utf-8"))))
            if missing:
                print(f"warning: {target} is missing {', '.join(missing)}", file=sys.stderr)
        elif args.check:
            print(f"missing: {target}", file=sys.stderr)
            drift = True
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            print(f"created {target}")

    if not args.check:
        print("app dependency order: " + " -> ".join(context["app_order"]))
    return 1 if drift else 0


if __name__ == "__main__":
    sys.exit(main())
