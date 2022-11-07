import django.contrib.auth.forms
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator

from .models import Post, Tag

from .forms import TagForm, PostForm
from .utils import *


class PostDetail(ObjectDetailMixin, View):
    model = Post
    template = 'blog/post_detail.html'


class TagDetail(ObjectDetailMixin, View):
    model = Tag
    template = 'blog/tag_detail.html'


class TagCreate(LoginRequiredMixin, ObjectCreateMixin, View):
    model_form = TagForm
    template = 'blog/tag_create.html'
    go_to_mainpage = True
    redirect_url = 'tags_list_url'
    raise_exception = True


class TagUpdate(LoginRequiredMixin, ObjectUpdateMixin, View):
    model = Tag
    model_form = TagForm
    template = 'blog/tag_update.html'
    raise_exception = True


class PostUpdate(LoginRequiredMixin, ObjectUpdateMixin, View):
    model = Post
    model_form = PostForm
    template = 'blog/post_update.html'
    raise_exception = True


class PostCreate(LoginRequiredMixin, ObjectCreateMixin, View):
    model_form = PostForm
    template = 'blog/post_create.html'
    raise_exception = True


class PostDelete(LoginRequiredMixin, ObjectDeleteMixin, View):
    model = Post
    template = 'blog/post_delete.html'
    redirect_url = 'posts_list_url'
    raise_exception = True


class TagDelete(LoginRequiredMixin, ObjectDeleteMixin, View):

    model = Tag
    template = 'blog/tag_delete.html'
    redirect_url = 'tags_list_url'
    raise_exception = True


class PostList(View):
    def get(self, request, posts=None):
        searched_post = Search.search(request)
        if searched_post:
            return searched_post
        if not posts:
            posts = Post.objects.all()
        paginator = Paginator(posts, 1)
        page_number = request.GET.get('page', 1)
        page = paginator.get_page(page_number)
        return render(request, 'blog/index.html', context={'page': page, 'is_paginated': page.has_other_pages()})


class TagList(View):
    def get(self, request):
        searched_post = Search.search(request)
        if searched_post:
            return searched_post
        tags = Tag.objects.all()
        return render(request, 'blog/tags.html', context={'tags': tags})

