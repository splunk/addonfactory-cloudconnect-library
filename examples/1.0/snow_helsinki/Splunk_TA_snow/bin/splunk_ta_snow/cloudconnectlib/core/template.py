from jinja2 import Template, Environment, meta
import re

PATTERN = re.compile(r"^\{\{\s*(\w+)\s*\}\}$")


def compile_template(template):
    _origin_template = template
    _template = Template(template)

    def render_internal(context):
        match = re.match(PATTERN, _origin_template)
        if match:
            context_var = context.get(match.groups()[0])
            if context_var and isinstance(context_var, (dict, list,tuple)):
                return context_var
        return _template.render(context)

    return render_internal
