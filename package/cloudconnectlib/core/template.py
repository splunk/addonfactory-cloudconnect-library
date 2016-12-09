from jinja2 import Template


def compile_template(template):
    _template = Template(template)

    def render_internal(context):
        return _template.render(context)

    return render_internal
