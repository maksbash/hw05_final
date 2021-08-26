from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from yatube.settings import MAX_POST_ON_PAGE


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, MAX_POST_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, MAX_POST_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    title = f'Записи сообщества {group.title}'
    context = {
        'title': title,
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user_author = get_object_or_404(User, username=username)
    following = False

    if request.user.id is not None and not request.user.id == user_author.id:
        user_request = User.objects.get(id=request.user.id)
        follow = Follow.objects.filter(
            user=user_request.id, author=user_author.id)
        if follow.count() > 0:
            following = True

    post_list = user_author.posts.all()
    paginator = Paginator(post_list, MAX_POST_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    author = user_author.get_full_name()
    title = f'Профайл пользователя {author}'
    count_of_posts = post_list.count()
    context = {
        'title': title,
        'count_of_posts': count_of_posts,
        'author': user_author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comment_form = CommentForm(request.POST or None)
    comments = post.comments.all()
    count_of_posts = post.author.posts.all().count()
    title = f'Пост {post.text[:30]}'
    context = {
        'title': title,
        'count_of_posts': count_of_posts,
        'post': post,
        'comment_form': comment_form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    groups = Group.objects.all()
    form = PostForm(request.POST or None, files=request.FILES or None)

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user.username)

    return render(
        request,
        template,
        {'form': form, 'is_edit': False, 'groups': groups})


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)
    groups = Group.objects.all()
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:post_detail', post_id=post_id)

    return render(
        request,
        template,
        {'form': form,
            'username': request.user,
            'groups': groups,
            'is_edit': True})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    user = get_object_or_404(User, username=request.user.username)
    follows = user.follower.all()
    post_list = []
    for follow in follows:
        post_list.extend(follow.author.posts.all())
        print(follow.author.username)
        print(len(post_list))
        print(post_list)
    paginator = Paginator(post_list, MAX_POST_ON_PAGE)
    print(request.GET.get('page'))
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = get_object_or_404(User, username=request.user.username)
    author = get_object_or_404(User, username=username)
    if not user.id == author.id:
        follow = Follow()
        follow.user = user
        follow.author = author
        follow.save()
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    user = get_object_or_404(User, username=request.user.username)
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=user, author=author)
    follow.delete()
    return redirect('posts:profile', username=username)
