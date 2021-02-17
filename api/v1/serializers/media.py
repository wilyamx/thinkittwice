from rest_framework import serializers
from django.conf import settings

from PoleLuxe.models import User
from PoleLuxe.models.media import (
    Media,
    MediaComment,
    MediaResource,
)

from api.v1.helpers.company_manager import default_company_manager_helper
from api.v1.mixins import serializers as serializer_mixins
from api.v1.serializers.fields import FileOrPathField


class MediaResourceSerializer(serializers.ModelSerializer):
    media_id = serializers.PrimaryKeyRelatedField(
        queryset=Media.objects.all(),
        source='media'
    )
    thumbnail = FileOrPathField(
        required=False,
        max_length=None,
        allow_empty_file=True
    )
    resource = FileOrPathField()

    class Meta:
        model = MediaResource
        fields = [
            'id',
            'media_id',
            'resource',
            'thumbnail',
            'content_type',
            'caption',
        ]

        read_only_fields = ['type']


class MediaUserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'name', 'avatar_url']

    def get_avatar_url(self, obj):
        return settings.AWS_CLOUDFRONT_DOMAIN + str(obj.avatar_url)


class MediaSerializer(serializer_mixins.LikeableModelSerializer):
    comments_count = serializers.SerializerMethodField()
    user = MediaUserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True, required=False)
    commented = serializers.SerializerMethodField(method_name='is_commented')

    resources = MediaResourceSerializer(many=True, read_only=True)

    class Meta:
        model = Media
        fields = [
            'id',
            'title',
            'content',
            'user',
            'type',
            'resources',
            'likes_count',
            'comments_count',
            'liked',
            'commented',
            'created_at',
            'product_groups',
            'user_id',
            'is_active',
            'publish_date',
        ]

    def get_comments_count(self, obj):
        return obj.comments.count()

    def is_commented(self, obj):
        """
        Current user commented the media post.

        :param Media obj

        :return bool
        """
        return obj.comments.filter(
            id=self.context.get('user_id')
        ).count() > 0

    def update(self, instance, validated_data):
        # the mobile will do the encoding for emoji device support
        # validated_data['content'] as string
        # validated_data['title'] as string

        return super(MediaSerializer, self).update(
            instance,
            validated_data
        )

    def validate_user_id(self, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError('User does not exist.')

        if not user.active:
            raise serializers.ValidationError('User is not active.')

        return user_id

    def to_representation(self, obj):
        data = super(MediaSerializer, self).to_representation(obj)

        # the mobile will do the encoding for emoji device support
        # data['title'] as string
        # data['content'] as string

        return data


class MediaForFeedSerializer(serializer_mixins.FeedContentSerializer):
    user = MediaUserSerializer(read_only=True)
    resources = MediaResourceSerializer(many=True, read_only=True)

    class Meta:
        model = Media
        fields = [
            'id',
            'title',
            'content',
            'user',
            'type',
            'resources',
            'like_count',
            'comment_count',
            'liked',
            'commented',
            'created_at',
        ]

    def to_representation(self, obj):
        data = super(MediaForFeedSerializer, self).to_representation(obj)

        # the mobile will do the encoding for emoji device support
        # data['title'] as string
        # data['content'] as string

        return data


class MediaCommentSerializer(
    serializer_mixins.LikeableModelSerializer,
):
    class UserSerializer(serializers.ModelSerializer):
        class Meta:
            model = User
            fields = ['id', 'name', 'avatar_url']

    content = serializers.CharField(source='comment')
    user = UserSerializer(read_only=True)

    class Meta:
        model = MediaComment
        fields = [
            'content',
            'id',
            'user',
            'media',
            'likes_count',
            'liked',
            'created_at',
        ]

    def create(self, validated_data):
        commenter = User.objects.get(
            pk=self.context.get('user_id')
        )

        validated_data['user'] = commenter
        return super(MediaCommentSerializer, self).create(validated_data)

    def to_representation(self, obj):
        data = super(MediaCommentSerializer, self).to_representation(obj)

        # the mobile will do the encoding for emoji device support
        # data['content'] as string

        return data


class MediaCommentCountSerializer(MediaCommentSerializer):
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = MediaComment
        fields = [
            'content',
            'id',
            'user',
            'media',
            'likes_count',
            'liked',
            'comment_count',
            'created_at',
        ]

    def get_comment_count(self, obj):
        return MediaComment.objects.filter(
            media=obj.media
        ).count()


class MediaResourceWriteSerializer(serializers.ModelSerializer):
    thumbnail = FileOrPathField(
        required=False,
        max_length=None,
        allow_empty_file=True
    )
    resource = FileOrPathField()

    class Meta:
        model = MediaResource
        fields = [
            'id',
            'resource',
            'thumbnail',
            'caption',
        ]


class MediaWriteSerializer(MediaSerializer):
    """
    serializer used for create action only
    the mediaserializer is not usable because media_id is required field in that serializer
    """

    def create(self, validated_data):
        resources = validated_data.pop('resources', [])
        instance = super(MediaWriteSerializer, self).create(validated_data)

        for r in resources:
            r['media_id'] = instance.id
            serializer = MediaResourceSerializer(data=r)
            serializer.is_valid()
            serializer.save()

        return instance

    def update(self, instance, validated_data):
        resources = validated_data.pop('resources', None)
        instance = super(MediaWriteSerializer, self).update(instance, validated_data)

        if resources is not None:
            # delete
            existing_resources_ids = set(instance.resources.values_list('id', flat=True))
            param_resources_ids = set([i['id'] for i in resources if 'id' in i])
            to_delete = list(existing_resources_ids - param_resources_ids)
            MediaResource.objects.filter(id__in=to_delete).delete()

            for resource in resources:
                if 'id' in resource:
                    # update if has id
                    res = MediaResource.objects.get(id=resource['id'])
                    serializer = MediaResourceSerializer(data=res)
                else:
                    # add if no id
                    resource['media_id'] = instance.id
                    serializer = MediaResourceSerializer(data=resource)
                serializer.is_valid()
                serializer.save()

        return instance

    resources = MediaResourceWriteSerializer(many=True, required=False)
