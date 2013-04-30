import json

from django.template import Library

register = Library()


@register.filter('jsonify')
def jsonify(obj):
    return json.dumps(obj)
