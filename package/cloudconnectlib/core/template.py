from jinja2 import Template


class CloudConnectTemplate(object):
    def __init__(self, template_str):
        self._template = Template(template_str)

    def render(self, context):
        return self._template.render(context)
