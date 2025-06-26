from django.urls import path

from adminapp.views import AdminTokenObtainPairView,AdminLogout,ViewUsers,ViewSellers,RemoveUsers,ViewSellerDetails,RemoveSeller,MarksAdminRead,UnReadNotifications
from adminapp.views import SellerApprovals,ApproveSeller,AddCategory,ViewCategory,fetchUpdateCategory,UpdateNewCategory,DeleteCategory,AddColor,ViewColors,DeleteColor,AddSize
from adminapp.views import ViewSize,SizeDelete,AddBrand,ViewBrand,ViewUpdateBrand,UpdateNewBrand,DeleteBrand,ViewPendingProduct,ApproveProduct,ViewAllProduct,RejectProduct,ViewProduct,ViewRatingReview,UpdateNewSubCategory
from adminapp.views import ApproveReview,RejectReview,AddBanner,GetBanners,DeleteBanner,EditBannerData,UpdateBanner,ActivateBanner,DeactivateBanner,AddCoupon,GetCoupons,DeleteCoupon,GetEditCoupon,EditCoupon,fetchSubUpdateCategory
from adminapp.views import AddDiscountCard,GetDiscountCards,ActiveDeactive,DeleteDiscountCard,GetEditDiscountCard,EditDiscountData,AddFreeShippingOffer,GetFreeshipOffers,ShipOfferActiveDeactive,DeleteFreeShippingOffer,GetEditFreeShipOffer
from adminapp.views import EditShippingOfferData,GetSelectAllProducts,AddProductOffer,GetProductsAllOffers,DeleteProductOffer,ProductOfferActiveDeactive,GetEditProductOffer,EditProductOffers,ViewAllComplaints,ResolveComplaint,ViewAdminRevenue,PendingActions
from adminapp.views import ResolveComplaint,AdminReply,SellerFeedBacks,ViewPendingOrders,UpdateOrderStatus,VerifyPaymentAdmin,FetchAllReturnRefund,HandleMarkReturned,ViewAllNotifications,AddSubCategory,ViewSubCategory,DeleteSubCategory,FetchAdminDashboard

urlpatterns = [
    path('login/',AdminTokenObtainPairView.as_view(), name='admin_token_obtain_pair'),
    path('adminlogout/',AdminLogout.as_view(),name='adminlogout'),
    path('view_users/',ViewUsers.as_view(),name='view_users'),
    path('view_sellers/',ViewSellers.as_view(),name='view_sellers'),
    path('view_seller_approvals/',SellerApprovals.as_view(),name='view_seller_approvals'),
    path('remove_users/<int:user_id>/',RemoveUsers.as_view(),name="remove_users"),
    path('view_sellers_details/<int:id>/',ViewSellerDetails.as_view(),name="view_sellers_details"),
    path('remove_seller/<int:seller_id>/',RemoveSeller.as_view(),name="remove_seller"),
    path('approve_seller/<int:seller_id>/',ApproveSeller.as_view(),name="approve_seller"),
    path('add_category/',AddCategory.as_view(),name="add_category"),
    path('add_sub_category/',AddSubCategory.as_view(),name="add_sub_category"),
    path('view_category/',ViewCategory.as_view(),name="view_category"),
    path('view_sub_category/',ViewSubCategory.as_view(),name="view_sub_category"),
    path('fetch_update_category/<int:cate_id>/',fetchUpdateCategory.as_view(),name="fetch_update_category"),
    path('fetch_subupdate_category/<int:cate_id>/',fetchSubUpdateCategory.as_view(),name="fetch_subupdate_category"),
    path('update_new_category/<int:cate_id>/',UpdateNewCategory.as_view(),name="update_new_category"),
    path('update_newsub_category/<int:cate_id>/',UpdateNewSubCategory.as_view(),name="update_newsub_category"),
    path('delete_category/<int:cate_id>/',DeleteCategory.as_view(),name="delete_category"),
    path('delete_sub_category/<int:cate_id>/',DeleteSubCategory.as_view(),name="delete_sub_category"),
    path('add_color/',AddColor.as_view(),name="add_color"),
    path('view_colors/',ViewColors.as_view(),name="view_colors"),
    path('delete_color/<int:color_id>/',DeleteColor.as_view(),name="delete_color"),
    path('add_size/',AddSize.as_view(),name="add_size"),
    path('view_size/',ViewSize.as_view(),name="view_size"),
    path('delete_size/<int:size_id>/',SizeDelete.as_view(),name="delete_size"),
    path('add_brand/',AddBrand.as_view(),name="add_brand"),
    path('view_brand/',ViewBrand.as_view(),name="view_brand"),
    path('view_update_brand/<int:brand_id>/',ViewUpdateBrand.as_view(),name='view_update_brand'),
    path('update_brand/<int:brand_id1>/',UpdateNewBrand.as_view(),name='update_brand'),
    path('delete_brand/<int:brand_id>/',DeleteBrand.as_view(),name="delete_brand"),
    path('view_pending_product/',ViewPendingProduct.as_view(),name='view_pending_product'),
    path('view_all_product/',ViewAllProduct.as_view(),name='view_all_product'),
    path('approve_product/<int:id>/',ApproveProduct.as_view(),name="approve_product"),
    path('reject_product/<int:id>/',RejectProduct.as_view(),name="reject_product"),
    path('view_product/<int:id>/',ViewProduct.as_view(),name="view_product"),
    path('view_review_ratings/',ViewRatingReview.as_view(),name="view_review_ratings"),
    path('approve_review/<int:id>/',ApproveReview.as_view(),name="approve_review"),
    path('reject_review/<int:id>/',RejectReview.as_view(),name="reject_review"),
    path('add_banner/',AddBanner.as_view(),name="add_banner"),
    path('get_banners/',GetBanners.as_view(),name="get_banners"),
    path('delete_banner/<int:id>/',DeleteBanner.as_view(),name="delete_banner"),
    path('edit_banner_data/<int:id>/',EditBannerData.as_view(),name="edit_banner_data"),
    path('update_banner/<int:id>/',UpdateBanner.as_view(),name="update_banner"),
    path('activate_banner/<int:id>/',ActivateBanner.as_view(),name="activate_banner"),
    path('deactivate_banner/<int:id>/',DeactivateBanner.as_view(),name="deactivate_banner"),
    path('add_coupon/',AddCoupon.as_view(),name="add_coupon"),
    path('get_coupons/',GetCoupons.as_view(),name="get_coupons"),
    path('delete_coupon/<int:id>/',DeleteCoupon.as_view(),name="delete_coupon"),
    path('get_edit_coupon/<int:id>/',GetEditCoupon.as_view(),name="get_edit_coupon"),
    path('edit_coupon_data/<int:id>/',EditCoupon.as_view(),name="edit_coupon_data"),

    path("add_discount_card/",AddDiscountCard.as_view(),name="add_discount_card"),
    path("get_discount_cards/",GetDiscountCards.as_view(),name="get_discount_cards"),
    path('active_deactive/<int:id>/<str:newStatus>/', ActiveDeactive.as_view(), name='active_deactive'),
    path('delete_discount_card/<int:id>/',DeleteDiscountCard.as_view(),name="delete_discount_card"),
    path('get_edit_discount_card/<int:id>/',GetEditDiscountCard.as_view(),name="get_edit_discount_card"),
    path('edit_discount_card/<int:editCardId>/',EditDiscountData.as_view(),name="edit_discount_card"),


    path("add_freeshipping_offer/",AddFreeShippingOffer.as_view(),name="add_freeshipping_offer"),

    path("get_freeshipping_offer/",GetFreeshipOffers.as_view(),name="get_freeshipping_offer"),
    path('shipoffer_active_deactive/<int:id>/<str:newStatus>/', ShipOfferActiveDeactive.as_view(), name='shipoffer_active_deactive'),
    path('delete_freeshipping_offer/<int:id>/',DeleteFreeShippingOffer.as_view(),name="delete_freeshipping_offer"),
    path('get_edit_freeshipoffer/<int:id>/',GetEditFreeShipOffer.as_view(),name="get_edit_freeshipoffer"),
    path('edit_shipping_offer/<int:editOfferId>/',EditShippingOfferData.as_view(),name="edit_shipping_offer"),
    path('get_select_all_products/',GetSelectAllProducts.as_view(),name="get_select_all_products"),

    path("add_product_offer/",AddProductOffer.as_view(),name="add_product_offer"),

    path("get_Productsall_offers/",GetProductsAllOffers.as_view(),name="get_Productsall_offers"),
    
    path('delete_product_offer/<int:offerId>/',DeleteProductOffer.as_view(),name="delete_product_offer"),

    path('offer_active_deactive/<int:id>/<str:newStatus>/', ProductOfferActiveDeactive.as_view(), name='offer_active_deactive'),
    path('get_editproduct_offer/<int:offerid>/',GetEditProductOffer.as_view(),name="get_editproduct_offer"),
    
    path('edit_product_offer/<int:editingOfferId>/',EditProductOffers.as_view(),name="edit_product_offer"),
    path('view_all_complaints/',ViewAllComplaints.as_view(),name="view_all_complaints"),

    path('resolve_complaint/',ResolveComplaint.as_view(),name="resolve_complaint"),
    path('admin_reply/',AdminReply.as_view(),name="admin_reply"),
    path('seller_feedbacks/<int:id>/',SellerFeedBacks.as_view(),name="seller_feedbacks"),
    path('view_pending_orders/',ViewPendingOrders.as_view(),name="view_pending_orders"),
    path('update_order_status/<int:oid>/<int:uid>/',UpdateOrderStatus.as_view(),name="update_order_status"),
    path('verify_payment/<int:pid>/<int:sid>/',VerifyPaymentAdmin.as_view(),name="verify_payment"),
    path('fetch_all_returnrefund/',FetchAllReturnRefund.as_view(),name="fetch_all_returnrefund"),
    path('hanle_mark_returned/<int:returnId>/',HandleMarkReturned.as_view(),name="hanle_mark_returned"),
    path('view_all_notifications/',ViewAllNotifications.as_view(),name="view_all_notifications"),
    path('marks_admin_read/<int:id>/',MarksAdminRead.as_view(),name="marks_admin_read"),
    path('unread_notifications/',UnReadNotifications.as_view(),name="unread_notifications"),
    path('view_admin_revenue/',ViewAdminRevenue.as_view(),name="view_admin_revenue"),
    path('fetch_admin_dashboard/',FetchAdminDashboard.as_view(),name="fetch_admin_dashboard"),
    path('admin_pendings_actions/',PendingActions.as_view(),name="admin_pendings_actions")



]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)