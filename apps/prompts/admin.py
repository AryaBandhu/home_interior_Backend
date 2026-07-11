from django.contrib import admin
from .models import RoomType, RoomSize, DesignStyle, ColorTheme


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    list_filter = ['is_active']


@admin.register(RoomSize)
class RoomSizeAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    list_filter = ['is_active']


@admin.register(DesignStyle)
class DesignStyleAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    list_filter = ['is_active']


@admin.register(ColorTheme)
class ColorThemeAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    list_filter = ['is_active']
