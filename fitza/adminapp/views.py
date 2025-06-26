from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView
from adminapp.serializers import AdminTokenObtainPairSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
# Create your views here.
from rest_framework import status

class AdminTokenObtainPairView(TokenObtainPairView):
    serializer_class=AdminTokenObtainPairSerializer

    def post(self,request,*args,**kwargs):
        serializer=self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response=Response(serializer.validated_data,status=status.HTTP_200_OK)

        response.set_cookie(
            key="refresh_token",
            value=serializer.validated_data["refresh"],
            httponly=True,
            secure=True,
            samesite=None,
            path="/",
             max_age=60 * 60 * 24 * 7
        )
        response.data.pop("refresh",None)

        return response
    
class AdminLogout(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request):
        response=Response({"message":"Logged out successfully.. "},status=status.HTTP_200_OK)
        response.delete_cookie("refresh_token")
        response.delete_cookie("access_token")
        return response

from common.models import CustomUser,Seller,SellerBankDetails
from adminapp.serializers import ViewUsersSerializer,ViewSellerSerializer,ViewSellerDetailsSerializer
from django.db.models import Q

class ViewUsers(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        users = CustomUser.objects.filter(seller_profile__isnull=True, admin_profile__isnull=True,user_type='user',is_superuser=False).order_by('-id')
        serializer=ViewUsersSerializer(users,many=True)
        return Response(serializer.data)







from django.shortcuts import get_object_or_404


class RemoveUsers(APIView):

    permission_classes=[IsAuthenticated]

    def post(self,request, user_id):

        if not request.user.is_staff:
            return Response({"error":"Unauthorized"},status=status.HTTP_403_FORBIDDEN)
        
        user=get_object_or_404(CustomUser, id=user_id)

        if user.is_superuser:
            return Response({"error":"Cannot remove superuser"},status=status.HTTP_400_BAD_REQUEST)
        
        if user.is_staff:
            return Response({"status":"Cannot Remove staffs"},status=status.HTTP_400_BAD_REQUEST)
        
        if user==request.user:
            return Response({"error":"Cannot remove your self"},status=status.HTTP_400_BAD_REQUEST)
        
        user.delete()
        return Response({"message":"User removed successfully"},status=status.HTTP_200_OK)
        

class ViewSellerDetails(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,id):
        seller=Seller.objects.filter(id=id)
        serializer=ViewSellerDetailsSerializer(seller,many=True)
        return Response(serializer.data)

class ViewSellers(APIView):
    permission_classes=[IsAuthenticated]

    def get(self,request):
        active_users=CustomUser.objects.filter(is_active=True).values_list('id', flat=True)
        sellers=Seller.objects.filter(account_verified=True,user_id__in=active_users)
        approve_sellers=Seller.objects.filter(account_verified=True,user_id__in=active_users).count()
        obj=CustomUser.objects.filter(is_active=False).values_list('id', flat=True)
        pending_sellers=Seller.objects.filter(account_verified=False,user_id__in=obj).count()
        serializer=ViewSellerSerializer(sellers,many=True)
        context={"data":serializer.data,"approve":approve_sellers,"pending":pending_sellers}
        return Response(context)


class SellerApprovals(APIView):
    permission_classes=[IsAuthenticated]

    def get(self,request):
        obj=CustomUser.objects.filter(is_active=False).values_list('id', flat=True)
        sellers=Seller.objects.filter(account_verified=False,user_id__in=obj)
        serializer=ViewSellerSerializer(sellers,many=True)
        return Response(serializer.data)

from django.db import transaction
class RemoveSeller(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,seller_id):
        if not request.user.is_staff:
            return Response({"error": "You are not authorized to perform this action."},status=status.HTTP_403_FORBIDDEN)
        try:
            with transaction.atomic():
                seller=get_object_or_404(Seller,id=seller_id)
                user=get_object_or_404(CustomUser,id=seller.user_id)
                obj=get_object_or_404(SellerBankDetails,seller_id=seller.id)
                obj.delete()
                seller.delete()
                user.delete()
            return Response({"message": "Seller removed successfully."},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":f" Failed to remove seller {str(e)}"},status=status.HTTP_400_BAD_REQUEST)

# from notifications.notifiers import SellerApprovalNotifier
# class ApproveSeller(APIView):
#     permission_classes=[IsAuthenticated]
#     def post(self,request,seller_id):
#         currentuser=request.user
#         if not request.user.is_staff:
#             return Response({"errors":"You are not authorized to perform this action."},status=status.HTTP_403_FORBIDDEN)
#         seller=Seller.objects.get(id=seller_id)
#         user=CustomUser.objects.get(id=seller.user_id)
#         user.is_active=True
#         user.save()
#         seller.account_verified=True
#         seller.save()
#         notifier=SellerApprovalNotifier(user=seller.user,sender=currentuser)
#         notifier.notify_seller_approval(seller_id=seller.id)

#         return Response({"message":"Approved Successfully..."},status=status.HTTP_200_OK)





from django.core.mail import send_mail
from django.conf import settings
from notifications.notifiers import SellerApprovalNotifier

class ApproveSeller(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, seller_id):
        currentuser = request.user
        if not request.user.is_staff:
            return Response(
                {"errors": "You are not authorized to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            seller = Seller.objects.get(id=seller_id)
            user = CustomUser.objects.get(id=seller.user_id)
            
            # Update user and seller status
            user.is_active = True
            user.save()
            seller.account_verified = True
            seller.save()
            
            # Send email notification
            subject = "Congratulations! Your Seller Account Has Been Approved"
            message = (
                f"Dear {user.first_name or 'Seller'},\n\n"
                "Congratulations! Your seller account has been approved on our FITZA e-commerce "
                "dress selling platform. You can now start listing and selling your products.\n\n"
                "Thank you for joining us!\n\n"
                "Best regards,\n"
                "The FITZA Team"
            )
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            # Send through your existing notifier system
            notifier = SellerApprovalNotifier(user=seller.user, sender=currentuser)
            notifier.notify_seller_approval(seller_id=seller.id)
            
            return Response(
                {"message": "Seller approved successfully and notification sent."},
                status=status.HTTP_200_OK
            )
            
        except Seller.DoesNotExist:
            return Response(
                {"errors": "Seller not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except CustomUser.DoesNotExist:
            return Response(
                {"errors": "User account not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"errors": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )









from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from adminapp.serializers import AddCategorySerializer

class AddCategory(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddCategorySerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({"message": "Category added successfully"}, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"message": f"Failed to add category: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

from adminapp.serializers import ViewCategorySerializer,UpdateNewCategorySerializer,DeleteCategorySerializer
from common.models import ProductCategory

class ViewCategory(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        try:
            categories=ProductCategory.objects.all().order_by('-id')
            serializer=ViewCategorySerializer(categories,many=True)
            return Response(serializer.data,status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message":f"An Error Occured while fetching Categories {e}"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class fetchUpdateCategory(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,cate_id):
        try:
            categories=ProductCategory.objects.filter(id=cate_id)
            serializer=ViewCategorySerializer(categories,many=True)
            return Response(serializer.data,status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message":f"An Error Occured while fetching Categories {e}"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class UpdateNewCategory(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, cate_id):
        serializer = UpdateNewCategorySerializer(
            data=request.data, context={"request": request, "cate_id": cate_id}
        )
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Category Updated Successfully"}, status=status.HTTP_200_OK)
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class DeleteCategory(APIView):
    permission_classes=[IsAuthenticated]

    def delete(self,request,cate_id):
        try:
            serializer=DeleteCategorySerializer(context={"request":request,"cate_id":cate_id})
            serializer.save()
            return Response({"message":"Category Deleted Successfully..."},status=status.HTTP_200_OK)
        except ProductCategory.DoesNotExist:
            return Response({"errors":"The Category does not exist."},status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"errors":str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)


from adminapp.serializers import AddColorSerializer,ViewColorsSerializer,DeleteColorSerializer

class AddColor(APIView):
    permission_classes={IsAuthenticated}
    def post(self,request):
        serializer=AddColorSerializer(data=request.data,context={"request":request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message":"Color Added Successfully..."},status=status.HTTP_201_CREATED)
        return Response({"errors":"Error Occured While Adding Color"},status=status.HTTP_400_BAD_REQUEST)

from common.models import Color
class ViewColors(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        obj=Color.objects.all().order_by('-id')
        serializer=ViewColorsSerializer(obj,many=True)
        return Response(serializer.data)

class DeleteColor(APIView):
    permission_classes=[IsAuthenticated]
    def delete(self,request,color_id):
        try:
            serializer=DeleteColorSerializer(context={"request":request,"color_id":color_id})
            serializer.save()
            return Response({"message":"Color Deleted Successfully..."},status=status.HTTP_200_OK)
        except Color.DoesNotExist:
            return Response({"errors":"Color Does not exist"},status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"errors":str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)


from adminapp.serializers import AddSizeSerializer,ViewSizeSerializer,SizeDeleteSerializer
class AddSize(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request):
        serializer=AddSizeSerializer(data=request.data,context={"request":request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message":"Size Added Successfully.."},status=status.HTTP_201_CREATED)
        if serializer.errors:
            return Response({"errors":str(serializer.errors)},status=status.HTTP_400_BAD_REQUEST)
        return Response({"errors":"Error Occured while adding size.."},status=status.HTTP_400_BAD_REQUEST)



from common.models import SizeOption,Brand

class ViewSize(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        size=SizeOption.objects.all().order_by('-id')
        serializer=ViewSizeSerializer(size,many=True)
        return Response(serializer.data)


class SizeDelete(APIView):
    permission_classes=[IsAuthenticated]
    def delete(self,request,size_id):
        try:
            serializer=SizeDeleteSerializer(context={"request":request,"size_id":size_id})
            serializer.save()
            return Response({"message":"Size Deleted Successfully..."},status=status.HTTP_200_OK)
        except SizeOption.DoesNotExist:
            return Response({"errors":"Size Does not exist"},status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"errors":str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
from adminapp.serializers import AddBrandSerializer,BrandSerializer,UpdateNewBrandSerializer,DeleteBrandSerializer

class AddBrand(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request):
        serializer=AddBrandSerializer(data=request.data,context={"request":request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message":"Brand Added Successfully.."},status=status.HTTP_201_CREATED)
        if serializer.errors:
            return Response({"errors":str(serializer.errors)},status=status.HTTP_400_BAD_REQUEST)
        return Response({"errors":"Error Occured while adding size.."},status=status.HTTP_400_BAD_REQUEST)


class ViewBrand(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        obj=Brand.objects.all().order_by('-id')
        serializer=BrandSerializer(obj,many=True)
        return Response(serializer.data)
    
class ViewUpdateBrand(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,brand_id):
        obj=Brand.objects.get(id=brand_id)
        serializer=BrandSerializer(obj)
        return Response(serializer.data)
    
class UpdateNewBrand(APIView):
    permission_classes=[IsAuthenticated]
    def put(self,request,brand_id1):
        print("BRRRRR",brand_id1)
        serializer=UpdateNewBrandSerializer(data=request.data,context={"request":request,"brand_id1":brand_id1})
        if serializer.is_valid():
            serializer.save()
            return Response({"message":"Brand Updated Successfully.."},status=status.HTTP_200_OK)
        return Response({"errors":"Error Occured.."},status=status.HTTP_400_BAD_REQUEST)

class DeleteBrand(APIView):
    permission_classes=[IsAuthenticated]
    def delete(self,request,brand_id):
        try:
            serializer=DeleteBrandSerializer(context={"request":request,"brand_id":brand_id})
            serializer.save()
            return Response({"message":"Brand deleted Successfully.."},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"errors":str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from adminapp.serializers import ViewPendingProductSerializer,IndividualProductsSerializer
from common.models import ProductItem

class ViewPendingProduct(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        obj=ProductItem.objects.filter(status='pending').order_by('-id')
        serializer=ViewPendingProductSerializer(obj,many=True)
        return Response(serializer.data)
    
    

class ViewAllProduct(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        obj=ProductItem.objects.filter(status="approved").order_by('-id')
        serializer=ViewPendingProductSerializer(obj,many=True)
        return Response(serializer.data)

from adminapp.serializers import ApproveProductSerializer,RejectProductSerializer
class ApproveProduct(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,id):
        obj=ProductItem.objects.get(id=id)
        obj.status="approved"
        obj.save()
        serializer=ApproveProductSerializer(data=request.data,context={"request":request,"id":id})
        if serializer.is_valid():
            serializer.save()
            return Response({"message":"Product Approved Successfully..."},status=status.HTTP_200_OK)
        return Response({"errors":"Error Occured While Approve product"},status=status.HTTP_400_BAD_REQUEST)



class RejectProduct(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,id):
        obj=ProductItem.objects.get(id=id)
        obj.status="rejected"
        obj.save()
        serializer=RejectProductSerializer(data=request.data,context={"request":request,"id":id})
        if serializer.is_valid():
            serializer.save()
            return Response({"message":"Product Rejected.."},status=status.HTTP_200_OK)
        return Response({"errors":"Error Occured While Reject product"},status=status.HTTP_400_BAD_REQUEST)


class ViewProduct(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,id):
        obj=ProductItem.objects.filter(id=id).order_by('-id')
        serializer=IndividualProductsSerializer(obj,many=True)
        return Response(serializer.data)
    

from userapp.models import RatingsReview  
from adminapp.serializers import RatingReviewSerializer  
class ViewRatingReview(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        obj=RatingsReview.objects.all()
        serializer=RatingReviewSerializer(obj,many=True)
        return Response(serializer.data)


from userapp.models import RatingsReview  


class ApproveReview(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,id):
        try:
            obj=RatingsReview.objects.get(id=id)
            obj.status="approved"
            obj.save()
            return Response({"message":"Approved..."},status=status.HTTP_200_OK)
        except RatingsReview.DoesNotExist:
            return Response({"error": "Review not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RejectReview(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,id):
        try:
            obj=RatingsReview.objects.get(id=id)
            obj.status="rejected"
            obj.save()
            return Response({"message":"Rejected..."},status=status.HTTP_200_OK)
        except RatingsReview.DoesNotExist:
            return Response({"error": "Review not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


from adminapp.serializers import AddBannerSerializer

class AddBanner(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request):
        serializer=AddBannerSerializer(data=request.data,context={"request":request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message":"Banner Added Successfully"},status=status.HTTP_201_CREATED)
        return Response({"errors":serializer.errors},status=status.HTTP_400_BAD_REQUEST)


from adminapp.serializers import GetBannersSerializer,UpdateBannerSerializer
from sellerapp.models import Banner
class GetBanners(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        obj=Banner.objects.all().order_by('-id')
        serializer=GetBannersSerializer(obj,many=True)
        return Response(serializer.data)


class DeleteBanner(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,id):
        try:
            banner=Banner.objects.get(id=id)
        except Banner.DoesNotExist:
            return Response({"error": "Banner with the provided ID does not exist."},status=status.HTTP_404_NOT_FOUND)
        banner.delete()
        return Response({"message":"Banner Deleted Successfully..."},status=status.HTTP_204_NO_CONTENT)



class EditBannerData(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,id):
        obj=Banner.objects.get(id=id)
        serializer=GetBannersSerializer(obj)
        return Response(serializer.data)
    
class UpdateBanner(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,id):
        serializer=UpdateBannerSerializer(data=request.data,context={"request":request,"id":id})
        if serializer.is_valid():
            serializer.save()
            return Response({"message":"Banner Updated Successfully"},status=status.HTTP_201_CREATED)
        return Response({"errors":serializer.errors},status=status.HTTP_400_BAD_REQUEST)


class ActivateBanner(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,id):
        try:
            banner=Banner.objects.get(id=id)
        except Banner.DoesNotExist:
            return Response({"error": "Banner with the provided ID does not exist."},status=status.HTTP_404_NOT_FOUND)
        banner.is_active=True
        banner.save()
        return Response({"message":"Banner Activated Successfully..."},status=status.HTTP_204_NO_CONTENT)


class DeactivateBanner(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,id):
        try:
            banner=Banner.objects.get(id=id)
        except Banner.DoesNotExist:
            return Response({"error": "Banner with the provided ID does not exist."},status=status.HTTP_404_NOT_FOUND)
        banner.is_active=False
        banner.save()
        return Response({"message":"Banner Deactivated..."},status=status.HTTP_204_NO_CONTENT)

from adminapp.serializers import AddCouponSerializer,GetCouponsSerializer,EditCouponSerializer
from common.models import Coupon
class AddCoupon(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request):
        serializer=AddCouponSerializer(data=request.data,context={"request":request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message":"Coupon Added Successfully..."},status=status.HTTP_201_CREATED)
        return Response({"errors":serializer.errors},status=status.HTTP_404_NOT_FOUND)

class GetCoupons(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        obj=Coupon.objects.all().order_by('-id')
        serializer=GetCouponsSerializer(obj,many=True)
        return Response(serializer.data)

class DeleteCoupon(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,id):
        user=request.user
        if not CustomUser.objects.filter(id=user.id).exists():
            return Response({"message":"UnAuthorized User..."},status=status.HTTP_404_NOT_FOUND)
        if not Coupon.objects.filter(id=id).exists():
            return Response({"message":"Coupon does not exists..."})
        coupondata=Coupon.objects.get(id=id)
        coupondata.delete()
        return Response({"message":"Coupon deleted successfully..."},status=status.HTTP_200_OK)


class GetEditCoupon(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,id):
        obj=Coupon.objects.filter(id=id)
        serializer=GetCouponsSerializer(obj,many=True)
        return Response(serializer.data)
    

class EditCoupon(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,id):
        serializer=EditCouponSerializer(data=request.data,context={"request":request,"id":id})
        if serializer.is_valid():
            serializer.save()
            return Response({"message":"Coupon Edited Successfully..."},status=status.HTTP_201_CREATED)
        return Response({"errors":serializer.errors},status=status.HTTP_404_NOT_FOUND)

from adminapp.serializers import AddDiscountCardSerializer,GetDiscountCardSerializer,EditDiscountCardSerializer

class AddDiscountCard(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request):
        serializer=AddDiscountCardSerializer(data=request.data,context={"request":request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message":"Discount Card Added Successfully..."},status=status.HTTP_201_CREATED)
        return Response({"errors":serializer.errors},status=status.HTTP_404_NOT_FOUND)


from sellerapp.models import DiscountCard  
class GetDiscountCards(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        obj=DiscountCard.objects.all().order_by('-id')
        serializer=GetDiscountCardSerializer(obj,many=True)
        return Response(serializer.data)


class ActiveDeactive(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id, newStatus):
        if not DiscountCard.objects.filter(id=id).exists():
            return Response({"message": "Discount Card does not exist."})

        obj = DiscountCard.objects.get(id=id)
        print("Status:", newStatus)

        # Determine the active status based on the input
        if newStatus.lower() == "false":
            active_status = False
        elif newStatus.lower() == "true":
            active_status = True
        else:
            return Response({"message": "Invalid status provided."}, status=status.HTTP_400_BAD_REQUEST)

        obj.is_active = active_status
        obj.save()

        return Response({"message": "Status changed successfully."}, status=status.HTTP_200_OK)


class DeleteDiscountCard(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,id):
        user=request.user
        if not CustomUser.objects.filter(id=user.id).exists():
            return Response({"message":"UnAuthorized User..."},status=status.HTTP_404_NOT_FOUND)
        if not DiscountCard.objects.filter(id=id).exists():
            return Response({"message":"DiscountCard does not exists..."})
        coupondata=DiscountCard.objects.get(id=id)
        coupondata.delete()
        return Response({"message":"DiscountCard deleted successfully..."},status=status.HTTP_200_OK)


class GetEditDiscountCard(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,id):
        obj=DiscountCard.objects.filter(id=id)
        serializer=GetDiscountCardSerializer(obj,many=True)
        return Response(serializer.data)

class EditDiscountData(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,editCardId):
        serializer=EditDiscountCardSerializer(data=request.data,context={"request":request,"id":editCardId})
        if serializer.is_valid():
            serializer.save()
            return Response({"message":"DiscountCard Edited Successfully..."},status=status.HTTP_201_CREATED)
        return Response({"errors":serializer.errors},status=status.HTTP_404_NOT_FOUND)


from adminapp.serializers import AddFreeShippingSerializer,GetFreeShipDataSerializer

class AddFreeShippingOffer(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request):
        serializer=AddFreeShippingSerializer(data=request.data,context={"request":request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message":"Free Shipping Offer Added Successfully..."},status=status.HTTP_201_CREATED)
        return Response({"errors":serializer.errors},status=status.HTTP_404_NOT_FOUND)


from sellerapp.models import FreeShippingOffer
class GetFreeshipOffers(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        obj=FreeShippingOffer.objects.all().order_by('-id')
        serializer=GetFreeShipDataSerializer(obj,many=True)
        return Response(serializer.data)



class ShipOfferActiveDeactive(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id, newStatus):
        if not FreeShippingOffer.objects.filter(id=id).exists():
            return Response({"message": "FreeShippingOffer Card does not exist."})

        obj = FreeShippingOffer.objects.get(id=id)
        print("Status:", newStatus)

        # Determine the active status based on the input
        if newStatus.lower() == "false":
            active_status = False
        elif newStatus.lower() == "true":
            active_status = True
        else:
            return Response({"message": "Invalid status provided."}, status=status.HTTP_400_BAD_REQUEST)

        obj.is_active = active_status
        obj.save()

        return Response({"message": "Status changed successfully."}, status=status.HTTP_200_OK)


class DeleteFreeShippingOffer(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,id):
        user=request.user
        if not CustomUser.objects.filter(id=user.id).exists():
            return Response({"message":"UnAuthorized User..."},status=status.HTTP_404_NOT_FOUND)
        if not FreeShippingOffer.objects.filter(id=id).exists():
            return Response({"message":"FreeShippingOffer does not exists..."})
        freeship=FreeShippingOffer.objects.get(id=id)
        freeship.delete()
        return Response({"message":"FreeShippingOffer deleted successfully..."},status=status.HTTP_200_OK)



class GetEditFreeShipOffer(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,id):
        obj=FreeShippingOffer.objects.filter(id=id)
        serializer=GetFreeShipDataSerializer(obj,many=True)
        return Response(serializer.data)  
    
from adminapp.serializers import EditShippingOfferSerializer,AddProductOfferSerializer

class EditShippingOfferData(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,editOfferId):
        serializer=EditShippingOfferSerializer(data=request.data,context={"request":request,"id":editOfferId})
        if serializer.is_valid():
            serializer.save()
            return Response({"message":"FreeShippingOffer Edited Successfully..."},status=status.HTTP_201_CREATED)
        return Response({"errors":serializer.errors},status=status.HTTP_404_NOT_FOUND)

from adminapp.serializers import ProductSelectSerializer
from common.models import Product
class GetSelectAllProducts(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        obj=Product.objects.all()
        serializer=ProductSelectSerializer(obj,many=True)
        return Response(serializer.data)


class AddProductOffer(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        print("Request Data:", request.data)  # Debug incoming data
        serializer = AddProductOfferSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            print("Saved successfully.")
            return Response({"message": "ProductOffer Added Successfully..."}, status=status.HTTP_201_CREATED)
        print("Serializer Errors:", serializer.errors)
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

from sellerapp.models import ProductOffer
from adminapp.serializers import GetProductsAllOffersSerializer,EditProductOfferSerializer

class GetProductsAllOffers(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        obj=ProductOffer.objects.all().order_by('-id')
        serializer=GetProductsAllOffersSerializer(obj,many=True)
        return Response(serializer.data)


class DeleteProductOffer(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,offerId):
        user=request.user
        if not CustomUser.objects.filter(id=user.id).exists():
            return Response({"message":"UnAuthorized User..."},status=status.HTTP_404_NOT_FOUND)
        if not ProductOffer.objects.filter(id=offerId).exists():
            return Response({"message":"ProductOffer does not exists..."})
        freeship=ProductOffer.objects.get(id=offerId)
        freeship.delete()
        return Response({"message":"ProductOffer deleted successfully..."},status=status.HTTP_200_OK)

class ProductOfferActiveDeactive(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id, newStatus):
        if not ProductOffer.objects.filter(id=id).exists():
            return Response({"message": "ProductOffer does not exist."})

        obj = ProductOffer.objects.get(id=id)
        print("Status:", newStatus)

        # Determine the active status based on the input
        if newStatus.lower() == "false":
            active_status = False
        elif newStatus.lower() == "true":
            active_status = True
        else:
            return Response({"message": "Invalid status provided."}, status=status.HTTP_400_BAD_REQUEST)

        obj.is_active = active_status
        obj.save()

        return Response({"message": "Status changed successfully."}, status=status.HTTP_200_OK)


class GetEditProductOffer(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,offerid):
        obj=ProductOffer.objects.filter(id=offerid)
        serializer=GetProductsAllOffersSerializer(obj,many=True)
        return Response(serializer.data)  

class EditProductOffers(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,editingOfferId):
        serializer=EditProductOfferSerializer(data=request.data,context={"request":request,"id":editingOfferId})
        if serializer.is_valid():
            serializer.save()
            return Response({"message":"Product Offer Edited Successfully..."},status=status.HTTP_201_CREATED)
        return Response({"errors":serializer.errors},status=status.HTTP_404_NOT_FOUND)


    

from adminapp.models import Complaint
from adminapp.serializers import ViewAllComplaintsSerializer   
class ViewAllComplaints(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        obj=Complaint.objects.all().order_by('id')
        serializer=ViewAllComplaintsSerializer(obj,many=True)
        return Response(serializer.data)

from adminapp.serializers import ResolveComplaintSerializer

class ResolveComplaint(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ResolveComplaintSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "message": "Complaint resolved successfully."}, status=status.HTTP_200_OK)
        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

from adminapp.serializers import AdminReplySerializer
class AdminReply(APIView):
    permission_classes=[IsAuthenticated]
    def post(self, request):
        serializer = AdminReplySerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "message": "replayed successfully."}, status=status.HTTP_200_OK)
        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

from userapp.models import Feedback
from adminapp.serializers import ViewSellerFeedbacksSerializer
class SellerFeedBacks(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,id):
        print("OOO",id)
        if id==0:
            platformstatus=True
        else:
            platformstatus=False
        print("NK",platformstatus)
        obj=Feedback.objects.filter(platform=platformstatus).order_by('-id')
        serializer=ViewSellerFeedbacksSerializer(obj,many=True)
        return Response(serializer.data)


from adminapp.serializers import ViewPendingOrdersSerializer
from userapp.models import OrderLine
from common.models import ShopOrder
class ViewPendingOrders(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        obj = ShopOrder.objects.all().order_by('-id')
        serializer=ViewPendingOrdersSerializer(obj,many=True)
        pdata = ShopOrder.objects.filter(order_status__status="pending")
        odata = ShopOrder.objects.filter(order_status__status="processing")
        cdata = ShopOrder.objects.filter(order_status__status="completed")
        print(len(obj))
        tempdata={
            "pending":len(pdata),
            "ongoing":len(odata),
            "completed":len(cdata),
        }
        print(tempdata)

        response_data={
            "orders":serializer.data,
            "statuscounts":tempdata,
        }
        return Response(response_data)


from common.models import OrderStatus
class UpdateOrderStatus(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, oid, uid):
        try:
            user_instance = CustomUser.objects.get(id=uid)
            order = ShopOrder.objects.get(id=oid, user=user_instance)
            processing_status, created = OrderStatus.objects.get_or_create(status="processing")
            order.order_status = processing_status
            order.save()

            

            return Response({
                "message": "Order status updated successfully.",
                "status_created": created  # Indicates if the status was newly created
            }, status=200)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found."}, status=404)
        except ShopOrder.DoesNotExist:
            return Response({"error": "Order not found."}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

from common.models import Payment
class VerifyPaymentAdmin(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pid, sid):
        try:
            shoporder_instance = ShopOrder.objects.get(id=sid)
            payment = Payment.objects.get(id=pid, order=shoporder_instance)
            payment.payout_status = "Completed"
            payment.save()

            return Response({"message": "Payment Verified successfully."},status=200)
        except ShopOrder.DoesNotExist:
            return Response({"error": "ShopOrder not found."}, status=404)
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found."}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        

from adminapp.serializers import FetchAllReturnRefundSerializer
from userapp.models import ReturnRefund
class FetchAllReturnRefund(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        obj=ReturnRefund.objects.all().order_by('-id')
        serializer=FetchAllReturnRefundSerializer(obj,many=True)
        return Response(serializer.data)
    

from adminapp.serializers import HandleMarkReturnedSerializer

class HandleMarkReturned(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,returnId):
        serializer=HandleMarkReturnedSerializer(data=request.data,context={"request":request,"returnId":returnId})
        if serializer.is_valid():
            serializer.save()
            return Response({"message":"Mark return added successfully.."},status=status.HTTP_200_OK)
        return Response({"errors":"Error occured..."},status=status.HTTP_400_BAD_REQUEST)

from adminapp.serializers import ViewAllNotificationsSerializer
from django.db.models import Q
from sellerapp.models import Notification
class ViewAllNotifications(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        notifications = Notification.objects.filter(group='all_admins') 
        priority = Notification.objects.filter(group='all_admins',priority='high') 
        sellers = Notification.objects.filter(group='all_admins',redirect_url='/admin/sellers/pending/') 
        products = Notification.objects.filter(group='all_admins',redirect_url='/admin/products/pending/') 
        returnrefunds = Notification.objects.filter(group='all_admins',redirect_url='/neworders/return') 
        unread=Notification.objects.filter(group='all_admins',is_read=False)
        statuscounts={"critical":len(priority),"seller":len(sellers),"products":len(products),"returnrefund":len(returnrefunds),"unread":len(unread)}
        print("Status:",statuscounts)
        serializer = ViewAllNotificationsSerializer(notifications, many=True)  # Serialize the queryset
        responsedata={"data":serializer.data,"counts":statuscounts}
        return Response(responsedata)


class MarksAdminRead(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,id):
        obj=Notification.objects.get(id=id)
        obj.is_read=True
        obj.save()
        return Response({"message":"Mark As Read...."},status=status.HTTP_200_OK)

class UnReadNotifications(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        obj=Notification.objects.filter(group='all_admins',is_read=False)
        serializer={"notifications":len(obj)}
        return Response(serializer)


from adminapp.serializers import AddSubCategorySerializer

class AddSubCategory(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = AddSubCategorySerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({"message": "Sub Category added successfully"}, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"message": f"Failed to add category: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


from adminapp.serializers import ViewSubCategorySerializer
from common.models import SubCategory
class ViewSubCategory(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        try:
            categories=SubCategory.objects.all().order_by('-id')
            serializer=ViewSubCategorySerializer(categories,many=True)
            return Response(serializer.data,status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message":f"An Error Occured while fetching Categories {e}"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from adminapp.serializers import DeleteSubCategorySerializer
class DeleteSubCategory(APIView):
    permission_classes=[IsAuthenticated]

    def delete(self,request,cate_id):
        try:
            serializer=DeleteSubCategorySerializer(context={"request":request,"cate_id":cate_id})
            serializer.save()
            return Response({"message":"SubCategory Deleted Successfully..."},status=status.HTTP_200_OK)
        except ProductCategory.DoesNotExist:
            return Response({"errors":"The SubCategory does not exist."},status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"errors":str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)


from adminapp.serializers import ViewSubCategorySerializer1

class fetchSubUpdateCategory(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,cate_id):
        try:
            categories=SubCategory.objects.filter(id=cate_id)
            serializer=ViewSubCategorySerializer1(categories,many=True)
            return Response(serializer.data,status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message":f"An Error Occured while fetching Categories {e}"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
from adminapp.serializers import UpdateNewSubCategorySerializer
class UpdateNewSubCategory(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, cate_id):
        serializer = UpdateNewSubCategorySerializer(
            data=request.data, context={"request": request, "cate_id": cate_id}
        )
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "SubCategory Updated Successfully"}, status=status.HTTP_200_OK)
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)



from adminapp.serializers import BillRevenueSerializer
from userapp.models import Bill

from collections import defaultdict
from django.db.models import Q

class ViewAdminRevenue(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        if not CustomUser.objects.filter(id=user.id).exists():
            return Response({"error": "You are not authorized to view this data."}, status=403)
        
        bills = Bill.objects.all()
        serializer = BillRevenueSerializer(bills, many=True)
        bills_data = serializer.data
        
        # Calculate overall stats
        total_revenue = sum(float(bill['total_amount']) for bill in bills_data)
        admin_earnings = sum(float(bill['payment']['platform_fee']) for bill in bills_data)
        active_sellers = Seller.objects.filter(user__is_active=True).count()
        
        # Calculate refund amount
        refund_amount = 0
        for bill in bills_data:
            returns = bill.get('order', {}).get('returns', [])
            if returns:
                refund_amount += sum(
                    float(ret['approved_refund_amount']) 
                    for ret in returns 
                    if ret.get('status') == "completed"
                )
        
        # Calculate seller-wise statistics
        seller_stats = {}
        
        for bill in bills_data:
            order_lines = bill.get('order', {}).get('order_lines', [])
            for line in order_lines:
                seller = line.get('seller')
                if seller:
                    seller_id = seller['id']
                    if seller_id not in seller_stats:
                        seller_stats[seller_id] = {
                            'name': f"{seller.get('first_name', '')} {seller.get('last_name', '')}".strip(),
                            'total_orders': 0,
                            'total_revenue': 0,
                            'total_refunds': 0,
                            'total_commission': 0
                        }
                    
                    # Update seller stats
                    seller_stats[seller_id]['total_orders'] += 1
                    seller_stats[seller_id]['total_revenue'] += float(bill['total_amount'])
                    seller_stats[seller_id]['total_commission'] += float(bill['payment']['platform_fee'])
                    
                    # Calculate refunds for this seller in this order
                    returns = bill.get('order', {}).get('returns', [])
                    if returns:
                        seller_refund = sum(
                            float(ret['approved_refund_amount']) 
                            for ret in returns 
                            if ret.get('status') == "completed"
                        )
                        seller_stats[seller_id]['total_refunds'] += seller_refund
        
        # Convert seller_stats to a list
        seller_details = [
            {
                'seller_id': seller_id,
                'seller_name': stats['name'],
                'total_orders': stats['total_orders'],
                'gross_revenue': stats['total_revenue'],
                'net_revenue': stats['total_revenue'] - stats['total_commission'],  # revenue after platform fee
                'total_refunds': stats['total_refunds'],
                'total_commission': stats['total_commission'],
                'final_revenue': (stats['total_revenue'] - stats['total_refunds']) - stats['total_commission']  # (gross - refunds) - commission
            }
            for seller_id, stats in seller_stats.items()
        ]
        
        response_data = {
            "overview": {
                "total_revenue": total_revenue,
                "admin_earnings": admin_earnings,
                "refund_amount": refund_amount,
                "active_sellers": active_sellers
            },
            "seller_stats": seller_details,
            "transactions": serializer.data,
        }
        
        return Response(response_data)
    
from adminapp.serializers import SalesTrendsSerializer 
from common.models import Brand

class FetchAdminDashboard(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        user=request.user
        if not CustomUser.objects.filter(id=user.id).exists():
            return Response({"error": "You are not authorized to view this data."}, status=403)
        total_users=CustomUser.objects.filter(user_type="user",is_active=True).count()
        total_sellers=Seller.objects.filter(account_verified=True,user__user_type="seller",user__is_active=True).count()
        order_excluded_status = ["completed", "canceled"]
        total_orders=ShopOrder.objects.exclude(order_status__status__in=order_excluded_status).count()
        total_products=Product.objects.filter(items__status="approved").count()
        pending_products=Product.objects.filter(items__status="pending").count()
        product_categories=ProductCategory.objects.all().count()
        product_brands=Brand.objects.all().count()
        bills = Bill.objects.all()
        serializer = BillRevenueSerializer(bills, many=True)
        bills_data = serializer.data
        total_revenue = sum(float(bill['total_amount']) for bill in bills_data)
        total_ratingreview=RatingsReview.objects.all().count()
        total_sales=Bill.objects.filter(payment_status="paid").count()
        serializer=SalesTrendsSerializer(bills,many=True)
        context={
                "totalusers":total_users,
                "totalsellers":total_sellers,
                "totalorders":total_orders,
                "totalproducts":total_products,
                "pending_products":pending_products,
                "product_categories":product_categories,
                "product_brands":product_brands,
                "totalrevenue":total_revenue,
                "totalratingreview":total_ratingreview,
                "total_sales":total_sales,
                "data":serializer.data
                }
        return Response({"data":context,"message":"Completed"})
    


# class PendingActions(APIView):
#     permission_classes=[IsAuthenticated]
#     def get(self,request):
#         user=request.user
#         if not CustomUser.objects.filter(id=user.id).exists():
#             return Response({"error": "You are not authorized to view this data."}, status=403)

#         obj=CustomUser.objects.filter(is_active=False).values_list('id', flat=True)
#         sellers_count=Seller.objects.filter(account_verified=False,user_id__in=obj).count()
#         products_count=ProductItem.objects.filter(status='pending').count()
#         review_ratings=RatingsReview.objects.filter(status="pending").count()
#         complaints=Complaint.objects.filter(resolved=False).count()
#         return_refund=ReturnRefund.objects.filter(status="pending").count()
#         bills=Bill.objects.all()
#         serializer=TopSellersSerializer(bills,many=True)
#         context={"sellerscount":sellers_count,"productscount":products_count,"reviewratings":review_ratings,"complaints":complaints,"returnrefund":return_refund,"topsellers":serializer.data}
#         return Response({"data":context})





from common.models import Seller

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count
# from .models import Seller, OrderLine, ShopOrder, Bill
from adminapp.serializers import TopSellerSerializer

class PendingActions(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        if not CustomUser.objects.filter(id=user.id).exists():
            return Response({"error": "You are not authorized to view this data."}, status=403)

        # Get top 5 sellers by revenue

        obj=CustomUser.objects.filter(is_active=False).values_list('id', flat=True)
        sellers_count=Seller.objects.filter(account_verified=False,user_id__in=obj).count()
        products_count=ProductItem.objects.filter(status='pending').count()
        review_ratings=RatingsReview.objects.filter(status="pending").count()
        complaints=Complaint.objects.filter(resolved=False).count()
        return_refund=ReturnRefund.objects.filter(status="pending").count()


        top_sellers = (
            OrderLine.objects
            .select_related('seller__seller_profile', 'order__bill')
            .filter(order__bill__payment_status='paid')  # Only count paid orders
            .values('seller')
            .annotate(
                total_revenue=Sum('order__bill__total_amount'),
                total_orders=Count('order', distinct=True)
            )
            .order_by('-total_revenue')[:5]  # Get top 5 by revenue
        )

        # Get seller details for each top seller
        seller_details = []
        for seller_data in top_sellers:
            seller_id = seller_data['seller']
            try:
                seller = Seller.objects.get(user_id=seller_id)
                seller_details.append({
                    'seller': seller,
                    'total_revenue': seller_data['total_revenue'],
                    'total_orders': seller_data['total_orders']
                })
            except Seller.DoesNotExist:
                continue

        # Serialize the data
        serializer = TopSellerSerializer(seller_details, many=True)
        context={"sellerscount":sellers_count,"productscount":products_count,"reviewratings":review_ratings,"complaints":complaints,"returnrefund":return_refund,"topsellers":serializer.data}
        return Response(context)