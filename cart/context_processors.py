from .models import Cart


def cart(request):
    """
    معالج سياق لسلة التسوق - يضيف سلة التسوق الحالية إلى سياق القالب
    Cart context processor - adds current cart to template context
    """
    if request.user.is_authenticated:
        # للمستخدمين المسجلين، استخدم معرف المستخدم
        # For logged-in users, use the user ID
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            cart = None
    else:
        # للزوار، استخدم مفتاح الجلسة
        # For visitors, use the session key
        session_key = request.session.session_key
        if not session_key:
            cart = None
        else:
            try:
                cart = Cart.objects.get(session_key=session_key)
            except Cart.DoesNotExist:
                cart = None

    return {'cart': cart}