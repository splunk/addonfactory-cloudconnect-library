from jinja2 import Template, Environment, meta
import re

PATTERN = re.compile(r"^\{\{\s*(\w+)\s*\}\}$")


def compile_template(template):
    _origin_template = template
    _template = Template(template)

    def translate_internal(context):
        match = re.match(PATTERN, _origin_template)
        if match:
            context_var = context.get(match.groups()[0])
            return context_var if context_var else ""
        return _template.render(context)

    return translate_internal
