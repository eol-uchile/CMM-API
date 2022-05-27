from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys import InvalidKeyError
from rest_framework import serializers
from .utils import validate_course, validate_block
import logging
logger = logging.getLogger(__name__)

class CMMCourseSerializer(serializers.Serializer):
    course_id = serializers.CharField(required=True, allow_blank=False)

    def validate_course_id(self, value):
        course_id = value
        if not validate_course(course_id):
            logger.error('CMMCourseSerializer - Course key not valid or dont exists: {}'.format(course_id))
            raise serializers.ValidationError(u"Course key not valid or dont exists: {}".format(course_id))
        return course_id

class CMMProblemSerializer(serializers.Serializer):
    block_id = serializers.CharField(required=True, allow_blank=False)
    
    def validate_block_id(self, value):
        block_id = value
        if not validate_block(block_id):
            logger.error('CMMProblemSerializer - Block key not valid or dont exists: {}'.format(block_id))
            raise serializers.ValidationError(u"Block key not valid or dont exists: {}".format(block_id))
        return block_id
