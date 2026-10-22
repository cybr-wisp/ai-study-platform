import argparse
import sys
from pathlib import Path

import yaml

SCHEMA_PREFIX = "#/components/schemas/"
RELATION_TYPES = {"ForeignKey", "OneToOneField", "ManyToManyField"}
ACRONYMS = {"pdf", "pptx", "docx", "txt", "md", "ai"}
TIMESTAMP_FIELDS = ("created_at", "updated_at")
AUTH_TOKEN = "AUTH_USER_MODEL"
MAX_INDEX_NAME = 30


def ref_name(ref):
    return ref[len(SCHEMA_PREFIX):]


def enum_label(value):
    text = value.replace("_", " ")
    return text.upper() if value in ACRONYMS else text.capitalize()


def model_meta(schema):
    return schema["x-django-model"]


def auth_model_name(context):
    return context["auth_user_model"].split(".")[1]


def auth_app(context):
    return context["auth_user_model"].split(".")[0]


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


def render_app_serializers(app, context):
    blocks = []
    names = []
    for name, schema in app_models(app, context).items():
        if model_meta(schema).get("serializer") is False:
            continue
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


def render_all(context):
    outputs = {}
    for app in context["app_order"]:
        if not app_models(app, context):
            continue
        outputs[Path(app) / "models.py"] = render_app_models(app, context)
        serializers = render_app_serializers(app, context)
        if serializers:
            outputs[Path(app) / "serializers.py"] = serializers
    return outputs


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate per-app Django models.py and serializers.py from the OpenAPI spec."
    )
    parser.add_argument("spec", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    spec = yaml.safe_load(args.spec.read_text(encoding="utf-8"))
    context = build_context(spec)
    outputs = render_all(context)

    drift = False
    for relative, content in outputs.items():
        target = args.out / relative
        if args.check:
            if not target.exists() or target.read_text(encoding="utf-8") != content:
                print(f"out of date: {target}", file=sys.stderr)
                drift = True
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            print(f"wrote {target}")
    if not args.check:
        print("app dependency order: " + " -> ".join(context["app_order"]))
    return 1 if drift else 0


if __name__ == "__main__":
    sys.exit(main())
