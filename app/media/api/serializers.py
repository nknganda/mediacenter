from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.core.paginator import Paginator
from django_countries.serializer_fields import CountryField
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination

from api.models import *


class AccountSerializer(serializers.ModelSerializer):
    country = CountryField()
    profile_details = serializers.JSONField(read_only=True)

    class Meta:
        model = Account
        fields = ('first_name', 'last_name', 'username', 'country', 'profile_details', 'email')


class FullAccountSerializer(AccountSerializer):
    """Requires full account view permissions (i.e. admin or current user privilege levels) UNLESS it is from a CREATE request."""
    account_settings = serializers.JSONField(read_only=False)

    class Meta:
        model = Account
        fields = ('username', 'first_name', 'last_name', 'email', 'password', 'country', 'account_settings')


class PrivateAccountProfileDetailsSerializer(serializers.ModelSerializer):
    account_settings = serializers.JSONField(read_only=False)
    profile_details = serializers.JSONField(read_only=False)

    class Meta:
        model = Account
        fields = ('id', 'account_settings', 'profile_details')


class LogSerializer(serializers.Serializer):
    created = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()
    message = serializers.CharField(max_length=400, allow_blank=True)


class ActivityLogSerializer(serializers.Serializer):
    title = serializers.CharField()
    authors = serializers.ModelField(Account)
    logs = serializers.ModelField(Log)


class BlogPostSerializer(serializers.Serializer):
    title = serializers.CharField()
    slug = models.SlugField()
    # TODO create authors field validator
    authors = serializers.ListField(
        child=serializers.CharField()
    )
    body = serializers.CharField()


# class MediaSrcHyperlinkedField(serializers.HyperlinkedIdentityField):
#     def to_representation(self, data):
#         pass

#     def to_internal_value(self, data):
#         return

#     def get_url(self, obj, view_name, request, format):
#         return 'https:/i.imgur.com/5EMmiqE.png'
#         # TODO do I need the album primary key here?
#         # url_kwargs = {
#         #     'album_pk': obj.pk,
#         #     'media_pk': obj.pk
#         # }
#         # return reverse()

#     def get_object():
#         pass


class MediaListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        # Batch upload is being performed
        media_list = [Media(**item) for item in validated_data]
        try:
            return Media.objects.create
        except (TypeError) as e:
            return Media.objects.bulk_create(media_list)

    def update(self, instance, validated_data):
        # is this where we check if the filetype is valid etc.?

        # multiple media updates are happening at once
        pass


class MediaAllowedFileTypeChecker(object):
    ALLOWED_FILETYPES = settings.ACCEPT_FILETYPES

    def __contains__(self, val):
        for kind, types in settings.ACCEPT_MIMES.values():
            if val in types:
                return kind
        raise ValidationError("Media type could not be determined.")


# class MediaSrcField(FileField):
#     ALLOWED_TYPES = MediaAllowedFileTypeChecker()

#     def get_file_extension(self, filename, decoded_file):
#         #
#         # WARNING: this could be DDOSed!
#         #
#         from django.core.files.storage import default_storage
#         from django.core.files.base import ContentFile
#         from os.path import join
#         import magic
#         tmpfile = 'tmp/{}'.format(upload)
#         default_storage.save(tmpfile, ContentFile(decoded_file).read())
#         path_to_tmpfile = join(settings.MEDIA_ROOT, tmpfile)

#         file_mime = magic.from_file(path_to_tmpfile, mime=True)

#         return file_mime

#     def to_internal_value(self, data):
#         file_object = super(MediaSrcField, self).to_internal_value(data)
#         # TODO add virus protection

#         try:
#             file_object['ext'] = file_object['name'].split('.')[1 ]
#         except IndexError:
#             # There is no explicit file extension
#             file_object['ext'] = ''

#         if 'mime' not in file_object:
#             # Try to figure out a file format from the associated mimetypes
#             file_object['mime'] = self.infer_format(data.file)

#         return file_object


# class MediaHyperlinkedSerializer(serializers.HyperlinkedModelSerializer):
#     src = MediaSrcHyperlinkedField(
#         read_only=False,
#         many=True,
#         required=False,
#         view_name='media-image-src'
#     )

#     tags = serializers.PrimaryKeyRelatedField(
#         queryset=MediaTag.objects.all(),
#         many=True,
#         required=False
#     )

#     class Meta:
#         model = Media
#         list_serializer_class = MediaListSerializer
#         fields = ('album', 'title', 'description', 'tags', 'media_type', 'src')


class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = ('id', 'title', 'description', 'tags', 'media_type')

    def determine_media_type(self, mime):
        for kind, types in settings.ACCEPT_MIMES.values():
            if mime in types:
                return kind
        raise ValidationError("Media type could not be determined.")

    # def validate(self, data):
    #     if data['media_type'] not in mediaChoices:
    #         data['media_type'] = self.determine_media_type(data['src']['mime'])

        # if data['src']['size'] > settings.MAX_FILE_SIZE[data['media_type']]:
        #     raise ValidationError('File cannot be stored due to large size')

        # acceptable_mimes = settings.ACCEPT_MIMES[data["media_type"]]
        # if data['src']['mime'] not in acceptable_mimes:
        #     raise ValidationError('MIME type not valid for media_type')


class AlbumMediaBrowserPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 24
    # essentially we limit this because this will be 24 "guaranteed" CDN requests


# class MediaBrowserSerializer(serializers.HyperlinkedModelSerializer):
#     media_set = SerializerMethodField()


#    class Meta:
#         model = Album
#         # TODO reevaluate this later
#         #'thumbnail', 
#         fields = ('media_set')

    # def get_media_set(self, obj):
    #     MediaSerializer(
    #         many=True,
    #         read_only=True
    #     )

    #     return serializer.data

class AlbumInfoSerializer(serializers.ModelSerializer):
    owner = AccountSerializer(
        read_only=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=AlbumTag.objects.all(),
        many=True,
        required=False
    )
    class Meta:
        model = Album
        fields = ('id', 'title', 'description', 'owner', 'tags')


class AlbumCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=AlbumTag.objects.all(),
        many=True,
        required=False
    )
    class Meta:
        model = Album
        fields = ('id', 'title', 'description', 'owner', 'tags')

