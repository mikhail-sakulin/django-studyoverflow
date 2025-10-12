from django.contrib import admin
from posts.models import LowercaseTag, Post, TaggedPost


admin.site.register(Post)
admin.site.register(LowercaseTag)
admin.site.register(TaggedPost)
