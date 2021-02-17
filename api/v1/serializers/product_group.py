# -*- coding: utf-8 -*-

from rest_framework import serializers

from PoleLuxe.models.productgroup import ProductGroup

from api.v1.serializers.user_group import ProductUserGroupSerializer


class ProductGroupSerializer(serializers.ModelSerializer):
    user_group_list = serializers.SerializerMethodField()
    user_group = serializers.ListField(write_only=True)

    class Meta:
        model = ProductGroup
        fields = [
            'id',
            'name',
            'user_group',
            'user_group_list',
            'created_at',
            'updated_at',
            'is_active',
            'company'
        ]

    def create(self, validated_data):
        # I don't understand why `is_active` becomes `False` when not provided
        # in the request considering it is set by default to `True` in the
        # model definition.
        if 'is_active' not in self.initial_data:
            validated_data.pop('is_active', None)
        obj = super(ProductGroupSerializer, self).create(validated_data)

        if 'request' in self.context and \
            hasattr(self.context['request'], 'authenticated_user') and \
            self.context['request'].authenticated_user.company_id and \
            obj.company is None:
            obj.company = self.context['request'].authenticated_user.company_id

        return obj

    def update(self, instance, validated_data):

        # if already has company and company with null is passed, ignore company field
        if instance.company and 'company' in validated_data and validated_data['company'] is None:
            validated_data.pop('company')

        return super(ProductGroupSerializer, self).update(instance, validated_data)

    def get_user_group_list(self, obj):
        if hasattr(obj, 'user_group'):
            return ProductUserGroupSerializer(
                obj.user_group.all(), many=True
            ).data
        else:
            return []

