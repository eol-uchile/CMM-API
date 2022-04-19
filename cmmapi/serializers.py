from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from rest_framework import serializers
import logging
logger = logging.getLogger(__name__)

class CMMSerializer(serializers.Serializer):
    name = serializers.CharField(required=True, allow_blank=False)

    def validate_name(self, value):
        name = value
        if name == 'error':
            logger.error('CMMSerializer - Name Error')
            raise serializers.ValidationError(u"CMMSerializer - Name Error")
        return name
