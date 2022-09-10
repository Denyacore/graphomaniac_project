from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow

from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

RECENT_POSTS: int = 10
TITLE_SYMBOL: int = 30
TIMOUT_CACHE: int = 20


@cache_page(TIMOUT_CACHE)
def index(request):
    template_index = 'posts/index.html'
    post_list = Post.objects.select_related('author')
    paginator = Paginator(post_list, RECENT_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj
    }
    return render(request, template_index, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author')
    paginator = Paginator(post_list, RECENT_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    template_group = 'posts/group_list.html'
    context = {
        'group': group,
        'page_obj': page_obj
    }
    return render(request, template_group, context)


def profile(request, username):
    template_profile = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related('author')
    paginator = Paginator(post_list, RECENT_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    if request.user.is_authenticated:
        follow = Follow.objects.filter(
            user=request.user.id,
            author=author.id
        ).exists()
    else:
        follow = False

    context = {
        'author': author,
        'page_obj': page_obj,
        'follow': follow

    }
    return render(request, template_profile, context)


def post_detail(request, post_id):
    template_post_detail = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    author = get_object_or_404(User, username=post.author)
    title = post.text[:TITLE_SYMBOL]
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'title': title,
        'form': form,
        'comments': comments,
        'author': author
    }
    return render(request, template_post_detail, context)


@login_required
def post_create(request):
    template_post_create = 'posts/post_create.html'
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', post.author)
    form = PostForm()
    return render(request, template_post_create, {'form': form})


@login_required
def post_edit(request, post_id):
    template_post_create = 'posts/post_create.html'
    post = get_object_or_404(Post, pk=post_id)
    is_edit = True
    if request.method == 'POST':
        form = PostForm(
            request.POST or None,
            instance=post,
            files=request.FILES or None,
        )
        if request.user == post.author:
            if form.is_valid():
                post = form.save(commit=True)
            return redirect('posts:post_detail', post_id)
        context = {'form': form, 'post': post}
        return render(request, template_post_create, context)
    form = PostForm(instance=post)
    context = {'form': form, 'is_edit': is_edit, 'post': post}
    return render(request, template_post_create, context)


@login_required
def add_comment(request, post_id):
    template_post_detail = 'posts:post_detail'
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect(template_post_detail, post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, RECENT_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj

    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user:
        Follow.objects.get_or_create(
            user=user, author=author
        )
    return redirect('posts:profile', username=author.username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    unfollow = Follow.objects.filter(
        user=request.user, author=author)
    unfollow.delete()
    return redirect('posts:profile', username)
