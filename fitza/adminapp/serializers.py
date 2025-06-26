from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import serializers
from common.models import CustomUser,Seller,SellerBankDetails

class AdminTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self,attrs):
        data=super().validate(attrs)
        user=self.user
        if not user:
            raise AuthenticationFailed("User not registered or invalid credentials")
        if not user.is_active:
            raise AuthenticationFailed("This account is disabled. Please contact support.")
        if not user.is_staff:
            raise AuthenticationFailed("Access denied. Only admins can log in here.")
        if not user.user_type=="admin":
            raise AuthenticationFailed("Only admins can log in here..")
   
        data["user_id"]=user.id
        data["username"]=user.username
        data["email"]=user.email
        data["photo"] = str(user.userphoto) if hasattr(user, "userphoto") else None
        data["is_admin"]=user.is_staff

        return data



class UserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model=CustomUser
        fields=['first_name','last_name','is_active']


class ViewSellerSerializer(serializers.ModelSerializer):
    user=UserDetailsSerializer(read_only=True)
    class Meta:
        model=Seller
        fields='__all__'


from cryptography.fernet import Fernet
from django.conf import settings
from rest_framework import serializers

class BankDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerBankDetails
        fields = ['account_holder_name', 'bank_name', 'account_number', 'ifsc_code', 'branch_address']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        try:
            # Access the encrypted account_number from the instance
            encrypted_account_number = instance.account_number
            cipher = Fernet(settings.BANK_ENCRYPTION_KEY)
            # Decrypt the account number
            representation['account_number'] = cipher.decrypt(encrypted_account_number).decode()
        except Exception as e:
            # Log the error and mask the sensitive data
            representation['account_number'] = None
        return representation




class ViewUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model=CustomUser
        fields='__all__'

class ViewSellerDetailsSerializer(serializers.ModelSerializer):
    bank_details=BankDetailsSerializer(read_only=True)
    user=ViewUsersSerializer(read_only=True)
    class Meta:
        model=Seller
        fields='__all__'

from common.models import ProductCategory
class AddCategorySerializer(serializers.Serializer):
    category=serializers.CharField(max_length=255)
    description=serializers.CharField(required=False, allow_blank=True)
    image=serializers.FileField(required=False, allow_null=True)
    def validate(self,data):
        user=self.context["request"].user
        if not CustomUser.objects.filter(id=user.id).exists():
            raise serializers.ValidationError("You don't have permission to add a category.")
        if ProductCategory.objects.filter(category_description=data["description"]).exists():
            raise serializers.ValidationError("Sub Category already exists.")
        return data
    def save(self):
        try:
            category=ProductCategory.objects.create(
                category_name=self.validated_data["category"],
                category_image=self.validated_data["image"],
                category_description=self.validated_data["description"],
            )
            return category
        except Exception as e:
            raise serializers.ValidationError(f"Failed to create category: {e}")


    

class ViewCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model=ProductCategory
        fields='__all__'



class UpdateNewCategorySerializer(serializers.Serializer):
    category = serializers.CharField()
    description = serializers.CharField()
    image = serializers.FileField()

    def validate(self, data):
        cate_id = self.context["cate_id"]
        if not ProductCategory.objects.filter(id=cate_id).exists():
            raise serializers.ValidationError({"category": "The category does not exist."})
        return data

    def save(self):
        cate_id = self.context["cate_id"]
        obj = ProductCategory.objects.get(id=cate_id)
        obj.category_name = self.validated_data["category"]
        obj.category_description = self.validated_data["description"]
        obj.category_image = self.validated_data["image"]
        obj.save()


class DeleteCategorySerializer(serializers.Serializer):
    def validate(self):
        cate_id = self.context["cate_id"]
        if not ProductCategory.objects.filter(id=cate_id).exists():
            raise serializers.ValidationError({"category": "The category does not exist."})
        return {}
    
    def save(self):
        cate_id = self.context["cate_id"]
        category = ProductCategory.objects.get(id=cate_id)
        category.delete()

from common.models import Color,SizeOption,Brand
class AddColorSerializer(serializers.Serializer):
    color=serializers.CharField()
    def validate(self,data):
        user=self.context["request"].user
        if not CustomUser.objects.filter(id=user.id).exists():
            raise serializers.ValidationError("You can't able to add color")
        if Color.objects.filter(color_name=data["color"]).exists():
            raise serializers.ValidationError("Color already exists...")
        return data
    def save(self):
        obj=Color.objects.create(color_name=self.validated_data["color"])
        return obj

    
class ViewColorsSerializer(serializers.ModelSerializer):
    class Meta:
        model=Color
        fields='__all__'

class DeleteColorSerializer(serializers.Serializer):
    def validate(self):
        color_id=self.context["color_id"]
        if not Color.objects.filter(id=color_id).exists():
            raise serializers.ValidationError("Color Does not exist")
    def save(self):
        color_id=self.context["color_id"]
        obj=Color.objects.get(id=color_id)
        obj.delete()


class AddSizeSerializer(serializers.Serializer):
    size=serializers.CharField()
    order=serializers.CharField()
    def validate(self,data):
        if SizeOption.objects.filter(size_name=data["size"]).exists():
            raise serializers.ValidationError("Size name already exists...")
        if SizeOption.objects.filter(sort_order=data["order"]).exists():
            raise serializers.ValidationError("Sort Order Value already used")
        return data
    def save(self):
        obj=SizeOption.objects.create(size_name=self.validated_data["size"],sort_order=self.validated_data["order"] )
        return obj

class ViewSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model=SizeOption
        fields='__all__'

class SizeDeleteSerializer(serializers.Serializer):
    def validate(self):
        size_id=self.context["size_id"]
        if not SizeOption.objects.filter(id=size_id).exists():
            raise serializers.ValidationError("Size Does not exist")
    def save(self):
        size_id=self.context["size_id"]
        obj=SizeOption.objects.get(id=size_id)
        obj.delete()


class AddBrandSerializer(serializers.Serializer):
    brand=serializers.CharField()
    description=serializers.CharField()
    def validate(self,data):
        user=self.context["request"].user
        if not CustomUser.objects.filter(id=user.id).exists():
            raise serializers.ValidationError("You can't able to add color")
        if Brand.objects.filter(brand_name=self.initial_data["brand"]).exists():
            raise serializers.ValidationError("Brandname already added...")
        return data
    
    def save(self):
        obj=Brand.objects.create(brand_name=self.validated_data["brand"],brand_description=self.validated_data["description"])
        return obj
    
        
class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model=Brand
        fields='__all__'


class UpdateNewBrandSerializer(serializers.Serializer):
    brand=serializers.CharField()
    description=serializers.CharField()
    def validate(self,data):
        user=self.context["request"].user
        brand_id1=self.context["brand_id1"]
        if not CustomUser.objects.filter(id=user.id).exists():
            raise serializers.ValidationError("Un authorised user")
        if not Brand.objects.filter(id=brand_id1).exists():
            raise serializers.ValidationError("You can't update..")
        return data
    
    def save(self):
        brand_id1=self.context["brand_id1"]
        obj=Brand.objects.get(id=brand_id1)
        obj.brand_name=self.validated_data["brand"]
        obj.brand_description=self.validated_data["description"]
        obj.save()
        return obj
            
    
class DeleteBrandSerializer(serializers.Serializer):
    def validate(self,attrs):
        user=self.context["request"].user
        brand_id=self.context["brand_id"]
        if not CustomUser.objects.filter(id=user.id).exists():
            raise serializers.ValidationError("UnAuthprized User")
        if not Brand.objects.filter(id=brand_id).exists():
            raise serializers.ValidationError("Brand already deleted")
        return attrs

    def save(self):
        brand_id=self.context["brand_id"]   
        obj=Brand.objects.get(id=brand_id).delete()
        return obj


from sellerapp.models import ProductImage
from common.models import ProductItem
from common.models import Product

# Serializer for ProductImage
class ViewProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['main_image', 'sub_image_1', 'sub_image_2', 'sub_image_3']

# Serializer for Product
class ViewProductsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'




# Serializer for ProductItem

class ViewPendingProductSerializer(serializers.ModelSerializer):
    product = ViewProductsSerializer(read_only=True)  # Product relationship
    images = ViewProductImageSerializer(many=True, read_only=True)  # Automatically maps to `images` related_name

    class Meta:
        model = ProductItem
        fields = [
            'id', 'product', 'color', 'size', 'original_price', 'sale_price', 
            'product_code', 'quantity_in_stock', 'status', 'rejection_reason', 'images'
        ]

from common.models import Seller

class ShopSellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seller
        fields = '__all__'

class IndividualProductsSerializer(serializers.ModelSerializer):
    product = ViewProductsSerializer(read_only=True) 
    images = ViewProductImageSerializer(many=True, read_only=True) 
    brand=serializers.SerializerMethodField()
    size=ViewSizeSerializer(read_only=True)
    color=ViewColorsSerializer(read_only=True)
    category=serializers.SerializerMethodField() 
    shop=serializers.SerializerMethodField() 

    class Meta:
        model = ProductItem
        fields = [
            'id', 'product','color','shop', 'size', 'original_price', 'sale_price', 'product_code',
            'quantity_in_stock', 'rejection_reason', 'images', 'brand', 'category'
        ]


    def get_brand(self, obj):
        if obj.product and obj.product.brand:
            return BrandSerializer(obj.product.brand).data
        return None

    def get_category(self, obj):
        if obj.product and obj.product.category:
            return ViewCategorySerializer(obj.product.category).data
        return None

    def get_shop(self, obj):
        if obj.product and obj.product.shop:
            return ShopSellerSerializer(obj.product.shop).data
        return None

from notifications.notifiers import ProductNotifier
class ApproveProductSerializer(serializers.Serializer):
    saleprice=serializers.CharField()
    code=serializers.CharField()
    def validate(self,data):
        user=self.context["request"].user
        if not user.is_staff:
            raise serializers.ValidationError("You are not authorized to perform this action.")
        return data
    def save(self):
        adminuser=self.context["request"].user
        id=self.context["id"]
        obj1=ProductItem.objects.get(id=id)
        obj1.sale_price=self.validated_data["saleprice"]
        obj1.product_code=self.validated_data["code"]
        obj1.save()
        seller_user = obj1.product.shop.user # Assuming ProductItem has a seller field
        notifier = ProductNotifier(user=seller_user,sender=adminuser)
        notifier.product_approved(product_name=obj1.product.product_name)






class RejectProductSerializer(serializers.Serializer):
    reason=serializers.CharField()
    def validate(self,data):
        user=self.context["request"].user
        if not user.is_staff:
            raise serializers.ValidationError("You are not authorized to perform this action.")
        return data
    def save(self):
        id=self.context["id"]
        obj1=ProductItem.objects.get(id=id)
        obj1.rejection_reason=self.validated_data["reason"]
        obj1.save()
        seller_user = obj1.product.shop.user # Assuming ProductItem has a seller field
        notifier = ProductNotifier(user=seller_user)
        notifier.product_rejected(product_name=obj1.product.product_name,reason=self.validated_data["reason"])

from userapp.models import RatingsReview

class ViewUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id','first_name']

class ProductNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['product_name']

class RatingReviewSerializer(serializers.ModelSerializer):
    user = ViewUserSerializer(read_only=True)
    shop_name = serializers.SerializerMethodField()
    product = ProductNameSerializer(read_only=True)

    class Meta:
        model = RatingsReview
        fields = '__all__'

    def get_shop_name(self, obj):
        # Check if the product exists and has a related shop (Seller)ll
        if obj.product and obj.product.shop:
            return obj.product.shop.shop_name
        return None
    
from sellerapp.models import Banner
class AddBannerSerializer(serializers.Serializer):
    image=serializers.FileField()
    title=serializers.CharField()
    description=serializers.CharField()
    offer=serializers.CharField()
    startdate=serializers.CharField()
    endDate=serializers.CharField()
    def validate(self,data):
        user=self.context["request"].user
        if not CustomUser.objects.filter(id=user.id).exists():
            raise serializers.ValidationError("UnAuthprized User")
        if Banner.objects.count() >= 3:
            raise serializers.ValidationError("You can only add up to 3 banners.")
        return data
       

    def save(self):
        obj=Banner.objects.create(
            title=self.validated_data["title"],
            description=self.validated_data["description"],
            offer_details=self.validated_data["offer"],
            image=self.validated_data["image"],
            start_date=self.validated_data["startdate"],
            end_date=self.validated_data["endDate"],
            is_active=False,
        )
        return obj

from sellerapp.models import Banner
class GetBannersSerializer(serializers.ModelSerializer):
    class Meta:
        model=Banner
        fields='__all__'


class UpdateBannerSerializer(serializers.Serializer):
    image=serializers.FileField()
    title=serializers.CharField()
    description=serializers.CharField()
    offer=serializers.CharField()
    startdate=serializers.CharField()
    endDate=serializers.CharField()
    def validate(self,data):
        user=self.context["request"].user
        id=self.context["id"]
        if not CustomUser.objects.filter(id=user.id).exists():
            raise serializers.ValidationError("UnAuthprized User")
        if not Banner.objects.filter(id=id).exists():
            raise serializers.ValidationError("Banner Does not exists..")
        return data
    

    def save(self):
        obj=Banner.objects.get(id=self.context["id"])
        obj.title=self.validated_data["title"]
        obj.description=self.validated_data["description"]
        obj.offer_details=self.validated_data["offer"]
        obj.image=self.validated_data["image"]
        obj.start_date=self.validated_data["startdate"]
        obj.end_date=self.validated_data["endDate"]
        obj.is_active=False
        obj.save()
        return obj
from notifications.notifiers import MarketingNotifier
from common.models import Coupon
class AddCouponSerializer(serializers.Serializer):
    code=serializers.CharField()
    discountType=serializers.CharField()
    discountValue=serializers.IntegerField()
    minimumOrderAmount=serializers.IntegerField()
    startDate=serializers.CharField()
    endDate=serializers.CharField()
    usageLimit=serializers.CharField()
    def validate(self, data):
        user=self.context["request"].user
        if not CustomUser.objects.filter(id=user.id).exists():
            raise serializers.ValidationError("UnAuthorized User...")
        return data
    def save(self):
        coupon, created = Coupon.objects.get_or_create(
            code=self.validated_data["code"],
            discount_type=self.validated_data["discountType"],
            discount_value=self.validated_data["discountValue"],
            minimum_order_amount=self.validated_data["minimumOrderAmount"],
            start_date=self.validated_data["startDate"],
            end_date=self.validated_data["endDate"],
            usage_limit=self.validated_data["usageLimit"],
        )
        if created:
                notifier = MarketingNotifier(group='all_users')  # Notify all users (you can customize the target)
                notifier.new_coupon(
                    coupon_code=coupon.code,
                    discount_type=coupon.discount_type,
                    discount_value=coupon.discount_value,
                    expires_on=coupon.end_date
                )
        

class GetCouponsSerializer(serializers.ModelSerializer):
    class Meta:
        model=Coupon
        fields='__all__'


class EditCouponSerializer(serializers.Serializer):
    code=serializers.CharField()
    discountType=serializers.CharField()
    discountValue=serializers.IntegerField()
    minimumOrderAmount=serializers.IntegerField()
    startDate=serializers.CharField()
    endDate=serializers.CharField()
    usageLimit=serializers.CharField()
    def validate(self, data):
        user=self.context["request"].user
        if not CustomUser.objects.filter(id=user.id).exists():
            raise serializers.ValidationError("UnAuthorized User...")
        return data
    def save(self):
        id=self.context["id"]
        obj=Coupon.objects.get(id=id)
        obj.code=self.validated_data["code"]
        obj.discount_type=self.validated_data["discountType"]
        obj.discount_value=self.validated_data["discountValue"]
        obj.minimum_order_amount=self.validated_data["minimumOrderAmount"]
        obj.start_date=self.validated_data["startDate"]
        obj.end_date=self.validated_data["endDate"]
        obj.usage_limit=self.validated_data["usageLimit"]
        obj.save()


from sellerapp.models import DiscountCard   

class AddDiscountCardSerializer(serializers.Serializer):
    cardName=serializers.CharField()
    discountPercentage=serializers.IntegerField()
    startDate=serializers.CharField()
    endDate=serializers.CharField()
    isActive=serializers.BooleanField()

    def validate(self, data):
        user=self.context["request"].user
        if not CustomUser.objects.filter(id=user.id).exists():
            raise serializers.ValidationError("UnAuthorized User...")
        return data
    def save(self):
        discount_card, created = DiscountCard.objects.get_or_create(
        card_name=self.validated_data["cardName"],
        discount_percentage=self.validated_data["discountPercentage"],
        start_date=self.validated_data["startDate"],
        end_date=self.validated_data["endDate"], 
        is_active=self.validated_data["isActive"],
        )
        if created:
            notifier = MarketingNotifier(group='all_users') 
            notifier.discount_card(
                card_name=discount_card.card_name,
                discount_percentage=discount_card.discount_percentage,
                expires_on=self.validated_data["endDate"]
            )





from sellerapp.models import DiscountCard  
class GetDiscountCardSerializer(serializers.ModelSerializer):
    class Meta:
        model=DiscountCard
        fields='__all__'


class EditDiscountCardSerializer(serializers.Serializer):
    cardName=serializers.CharField()
    discountPercentage=serializers.IntegerField()
    startDate=serializers.CharField()
    endDate=serializers.CharField()
    def validate(self, data):
        user=self.context["request"].user
        if not CustomUser.objects.filter(id=user.id).exists():
            raise serializers.ValidationError("UnAuthorized User...")
        return data
    def save(self):
        id=self.context["id"]
        obj=DiscountCard.objects.get(id=id)
        obj.card_name=self.validated_data["cardName"]
        obj.discount_percentage=self.validated_data["discountPercentage"]
        obj.start_date=self.validated_data["startDate"]
        obj.end_date=self.validated_data["endDate"]
        obj.save()


from sellerapp.models import FreeShippingOffer


from datetime import datetime
from rest_framework import serializers

class AddFreeShippingSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    minOrderAmount = serializers.IntegerField()
    description = serializers.CharField()
    startDate = serializers.CharField()
    endDate = serializers.CharField()
    isActive = serializers.BooleanField()

    def validate(self, data):
        user = self.context["request"].user
        if not CustomUser.objects.filter(id=user.id).exists():
            raise serializers.ValidationError("Unauthorized User...")

        # Validate and parse the date strings
        try:
            data["startDate"] = datetime.strptime(data["startDate"], "%Y-%m-%d")
            data["endDate"] = datetime.strptime(data["endDate"], "%Y-%m-%d")
        except ValueError:
            raise serializers.ValidationError("Invalid date format. Use 'YYYY-MM-DD'.")

        # Ensure endDate is not before startDate
        if data["endDate"] < data["startDate"]:
            raise serializers.ValidationError("End date must be after start date.")

        return data

    def save(self):
        free_shipping_offer, created = FreeShippingOffer.objects.get_or_create(
            min_order_amount=self.validated_data["minOrderAmount"],
            description=self.validated_data["description"],
            start_date=self.validated_data["startDate"],  # Already parsed to datetime
            end_date=self.validated_data["endDate"],  # Already parsed to datetime
            is_active=self.validated_data["isActive"],
        )
        if created:
            notifier = MarketingNotifier(group='all_users')
            notifier.free_shipping_offer(
                min_order_amount=free_shipping_offer.min_order_amount,
                expires_on=self.validated_data["endDate"]  # Already datetime
            )



class GetFreeShipDataSerializer(serializers.ModelSerializer):
    class Meta:
        model=FreeShippingOffer
        fields='__all__'
    

from datetime import datetime
from rest_framework import serializers

class EditShippingOfferSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    minOrderAmount = serializers.IntegerField()
    description = serializers.CharField()
    startDate = serializers.CharField()
    endDate = serializers.CharField()

    def validate(self, data):
        user = self.context["request"].user
        if not CustomUser.objects.filter(id=user.id).exists():
            raise serializers.ValidationError("Unauthorized User...")
        
        # Validate and parse the date strings
        try:
            data["startDate"] = datetime.strptime(data["startDate"], "%Y-%m-%d")
            data["endDate"] = datetime.strptime(data["endDate"], "%Y-%m-%d")
        except ValueError:
            raise serializers.ValidationError("Invalid date format. Use 'YYYY-MM-DD'.")
        
        # Ensure endDate is not before startDate
        if data["endDate"] < data["startDate"]:
            raise serializers.ValidationError("End date must be after start date.")
        
        return data

    def save(self):
        id = self.validated_data["id"]
        obj = FreeShippingOffer.objects.get(id=id)
        obj.min_order_amount = self.validated_data["minOrderAmount"]
        obj.description = self.validated_data["description"]
        obj.start_date = self.validated_data["startDate"]  # Already a datetime object
        obj.end_date = self.validated_data["endDate"]  # Already a datetime object
        obj.save()



class ProductSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model=Product
        fields=['id','product_name']

from sellerapp.models import ProductOffer
from common.models import Product

class AddProductOfferSerializer(serializers.Serializer):
    id=serializers.IntegerField()
    pid=serializers.IntegerField()
    productName=serializers.CharField()
    offerTitle=serializers.CharField()
    offerDescription=serializers.CharField()
    discountPercentage=serializers.IntegerField()
    startDate = serializers.DateField()
    endDate = serializers.DateField()
    isActive=serializers.BooleanField()

    def validate(self, data):
        user=self.context["request"].user
        if not CustomUser.objects.filter(id=user.id).exists():
            raise serializers.ValidationError("UnAuthorized User...")
        return data
    def save(self):
        try:
            product = Product.objects.get(id=self.validated_data["pid"], product_name=self.validated_data["productName"])
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found.")

        product_offer, created = ProductOffer.objects.get_or_create(
        product=product,
        offer_title=self.validated_data["offerTitle"],
        offer_description=self.validated_data["offerDescription"],
        discount_percentage=self.validated_data["discountPercentage"],
        start_date=self.validated_data["startDate"],
        end_date=self.validated_data["endDate"],
        is_active=self.validated_data["isActive"],
        )
        if created:
            notifier = MarketingNotifier(group='all_users')
            notifier.product_offer(
                product_name=product.product_name,
                offer_title=product_offer.offer_title,
                discount_percentage=product_offer.discount_percentage,
                expires_on=self.validated_data["endDate"]
            )




class ProductNameSerializer(serializers.ModelSerializer):
    class Meta:
        model=Product
        fields=['id','product_name']


from sellerapp.models import ProductOffer
class GetProductsAllOffersSerializer(serializers.ModelSerializer):
    product = ProductNameSerializer()

    class Meta:
        model=ProductOffer
        fields=['id','offer_title','offer_description','discount_percentage','start_date','end_date','is_active','product']


from rest_framework import serializers
from django.shortcuts import get_object_or_404
from datetime import datetime
# from .models import Product, ProductOffer, CustomUser  # Adjust imports as needed

class EditProductOfferSerializer(serializers.Serializer):
    pid = serializers.IntegerField()
    productname = serializers.CharField(max_length=255)
    offer_title = serializers.CharField(max_length=255)
    offer_description = serializers.CharField(max_length=1000)
    discount_percentage = serializers.FloatField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()

    def validate(self, data):
        user = self.context["request"].user
        if not CustomUser.objects.filter(id=user.id).exists():
            raise serializers.ValidationError("Unauthorized User...")

        # Validate that start_date is before end_date
        if data["start_date"] >= data["end_date"]:
            raise serializers.ValidationError("Start date must be before end date.")
        
        # Validate discount percentage range
        if not (0 <= data["discount_percentage"] <= 100):
            raise serializers.ValidationError("Discount percentage must be between 0 and 100.")

        return data

    def save(self):
        id = self.context["id"]
        validated_data = self.validated_data

        # Fetch product and offer safely
        product = get_object_or_404(Product, id=validated_data["pid"], product_name=validated_data["productname"])
        product_offer = get_object_or_404(ProductOffer, id=id)

        # Update offer details
        product_offer.product = product
        product_offer.offer_title = validated_data["offer_title"]
        product_offer.offer_description = validated_data["offer_description"]
        product_offer.discount_percentage = validated_data["discount_percentage"]
        product_offer.start_date = validated_data["start_date"]
        product_offer.end_date = validated_data["end_date"]
        product_offer.save()




from adminapp.models import Complaint,ComplaintMessage

class UserNameSerializer(serializers.ModelSerializer):
    class Meta:
        model=CustomUser
        fields=['first_name','user_type']

class ComplaintMessageSerializer(serializers.ModelSerializer):
    sender=UserNameSerializer(read_only=True)

    class Meta:
        model=ComplaintMessage
        fields=['complaint','sender','message','timestamp']

class ViewAllComplaintsSerializer(serializers.ModelSerializer):
    messages=ComplaintMessageSerializer(read_only=True,many=True)

    class Meta:
        model=Complaint
        fields=['id','seller','title','description','response','created_at','updated_at','resolved','messages']


from notifications.notifiers import ComplaintNotifier
class ResolveComplaintSerializer(serializers.Serializer):
    id = serializers.CharField()
    status = serializers.BooleanField()

    def validate(self, data):
        user = self.context["request"].user
        if not Complaint.objects.filter(id=data["id"]).exists():
            raise serializers.ValidationError({"id": "Complaint ID does not exist."})
        return data

    def save(self):
        user = self.context["request"].user
        complaint = Complaint.objects.get(id=self.validated_data["id"])
        complaint.resolved = self.validated_data["status"]
        complaint.save()
        notifier = ComplaintNotifier(user=complaint.seller, sender=user)
        notifier.notify_seller_admin_reply(complaint_id=complaint.id,reply_message="Your Complaint has been resolved. Please check the updated status.")

class AdminReplySerializer(serializers.Serializer):
    cid = serializers.IntegerField()
    newMessage = serializers.CharField()

    def validate(self, data):
        user = self.context["request"].user
        if not CustomUser.objects.filter(id=user.id).exists():
            raise serializers.ValidationError("Unauthorized User...")
        
        complaint_id=data.get("cid")
        complaint=Complaint.objects.filter(id=complaint_id).first()
        if not complaint:
            raise serializers.ValidationError("Complaint not found.")
        self.complaint=complaint
        return data

    def save(self):
        user=self.context["request"].user
        complaint=self.complaint
        if not complaint.response:
            complaint.response=self.validated_data["newMessage"]
            complaint.save()
        else:
            ComplaintMessage.objects.create(
                complaint=complaint,
                sender=user,
                message=self.validated_data["newMessage"]
            )
            
class ViewUsersNameSerializer(serializers.ModelSerializer):
    class Meta:
        model=CustomUser
        fields=['id','first_name','email']
from userapp.models import Feedback
class ViewSellerFeedbacksSerializer(serializers.ModelSerializer):
    user=ViewUsersNameSerializer(read_only=True)

    class Meta:
        model=Feedback
        fields='__all__'

class ProductSerializers2(serializers.ModelSerializer):
    class Meta:
        model=Product
        fields=['id','product_name']


class ProductItemSerializer(serializers.ModelSerializer):
    product=ProductSerializers2(read_only=True)

    class Meta:
        model=ProductItem
        fields=['id','product']

from userapp.models import OrderLine
class OrderLineDetailsSerializer(serializers.ModelSerializer):
    seller=ViewUsersNameSerializer(read_only=True)
    product_item=ProductItemSerializer(read_only=True)

    class Meta:
        model=OrderLine
        fields='__all__'

from common.models import Payment
class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model=Payment
        fields='__all__'



from common.models import ShopOrder
class ViewUserSerializer(serializers.ModelSerializer):
    class Meta:
        model=CustomUser
        fields=['id','first_name','email','phone_number']

from common.models import OrderStatus
class OrderStatusViewSerializer1(serializers.ModelSerializer):
    class Meta:
        model=OrderStatus
        fields=['id','status']


        

class AppliedCouponSerializer(serializers.ModelSerializer):
    class Meta:
        model=Coupon
        fields=['id','code']

from userapp.models import OrderLine
class ViewPendingOrdersSerializer(serializers.ModelSerializer):
    user=ViewUserSerializer(read_only=True)
    payment_method=PaymentMethodSerializer(read_only=True)
    order_lines=OrderLineDetailsSerializer(read_only=True,many=True)
    order_status=OrderStatusViewSerializer1(read_only=True)
    applied_coupon=AppliedCouponSerializer(read_only=True)

    class Meta:
        model=ShopOrder
        fields=['id','user','payment_method','order_lines','order_status','order_date','order_total','discount_amount','applied_coupon','final_total','free_shipping_applied']


from userapp.models import ReturnRefund
class FetchAllReturnRefundSerializer(serializers.ModelSerializer):
    class Meta:
        model=ReturnRefund
        fields='__all__'


from datetime import datetime
from rest_framework import serializers
from userapp.models import CustomUser, ReturnRefund
from notifications.notifiers import ReturnRefundNotifier

class HandleMarkReturnedSerializer(serializers.Serializer):
    resolution_notes = serializers.CharField()
    approved_refund_amount=serializers.IntegerField()
    status=serializers.CharField()
    def validate(self, data):
        user = self.context["request"].user
        if not CustomUser.objects.filter(id=user.id).exists():
            raise serializers.ValidationError("User does not exist.")
        return data

    def save(self):
        user = self.context["request"].user
        return_id = self.context["returnId"]
        resolution_notes = self.validated_data["resolution_notes"]
        approved_refund_amount = self.validated_data["approved_refund_amount"]
        status = self.validated_data["status"]
        try:
            obj = ReturnRefund.objects.get(id=return_id)
        except ReturnRefund.DoesNotExist:
            raise serializers.ValidationError("Invalid ReturnRefund ID.")
        obj.resolution_notes = resolution_notes
        obj.approved_refund_amount = approved_refund_amount
        obj.status = status
        obj.processed_date = datetime.now()
        obj.save()
        notifier = ReturnRefundNotifier(user=obj.requested_by, sender=user)
        if status=="rejected":
            notifier.return_rejected(order_id=obj.order.id)
        elif status=="approved":
            notifier.refund_initiated(order_id=obj.order.id,refund_amount=approved_refund_amount)
        elif status=="completed":
            notifier.refund_completed(order_id=obj.order.id,refund_amount=approved_refund_amount)

        return obj


from sellerapp.models import Notification

class ViewAllNotificationsSerializer(serializers.ModelSerializer):
    class Meta:
        model=Notification
        fields='__all__'


from common.models import SubCategory
class AddSubCategorySerializer(serializers.Serializer):
    category=serializers.CharField()
    subcategoryName=serializers.CharField(required=False, allow_blank=True)
    subdescription=serializers.CharField(required=False, allow_blank=True)


    def validate(self, data):
        user = self.context["request"].user

        # Check if the user exists
        if not CustomUser.objects.filter(id=user.id).exists():
            raise serializers.ValidationError("You don't have permission to add a category.")
        
        # Check if the main category exists
        print("CAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",data["category"])
        if not ProductCategory.objects.filter(category_name=data["category"]).exists():
            raise serializers.ValidationError("Main Category does not exist.")
        
        # Optional: Ensure subcategory is unique under the same category
        category = ProductCategory.objects.get(category_name=data["category"])
        if category and SubCategory.objects.filter(category=category, subcategory_name=data["subcategoryName"]).exists():
            raise serializers.ValidationError("Subcategory with this name already exists in the selected category.")
        return data
        
    def save(self):
        try:
            # Fetch the main category object
            obj = ProductCategory.objects.get(category_name=self.validated_data["category"])

            # Create a new subcategory
            category = SubCategory.objects.create(
                category=obj,
                subcategory_name=self.validated_data["subcategoryName"],
                subcategory_description=self.validated_data["subdescription"],
            )
            return category
        except ProductCategory.DoesNotExist:
            raise serializers.ValidationError("The specified category does not exist.")
        except Exception as e:
            raise serializers.ValidationError(f"Failed to create subcategory: {str(e)}")

from common.models import SubCategory,ProductCategory

class MainCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model=ProductCategory
        fields=['category_name']

class ViewSubCategorySerializer(serializers.ModelSerializer):
    category=MainCategorySerializer(read_only=True)

    class Meta:
        model=SubCategory
        fields='__all__'


class DeleteSubCategorySerializer(serializers.Serializer):
    def validate(self):
        cate_id = self.context["cate_id"]
        if not SubCategory.objects.filter(id=cate_id).exists():
            raise serializers.ValidationError({"category": "The category does not exist."})
        return {}
    
    def save(self):
        cate_id = self.context["cate_id"]
        category = SubCategory.objects.get(id=cate_id)
        category.delete()


class MainCategorySerializer1(serializers.ModelSerializer):
    class Meta:
        model=ProductCategory
        fields=['id','category_name']

class ViewSubCategorySerializer1(serializers.ModelSerializer):
    category=MainCategorySerializer1(read_only=True)

    class Meta:
        model=SubCategory
        fields='__all__'




class UpdateNewSubCategorySerializer(serializers.Serializer):
    parentCategory=serializers.CharField()
    category = serializers.CharField()
    description = serializers.CharField()
   
    def validate(self, data):
        cate_id = self.context["cate_id"]
        if not SubCategory.objects.filter(id=cate_id).exists():
            raise serializers.ValidationError({"category": "The category does not exist."})
        return data

    def save(self):
        cate_id = self.context["cate_id"]
        obj = SubCategory.objects.get(id=cate_id)
        res=ProductCategory.objects.get(category_name=self.validated_data["parentCategory"])
        obj.category=res
        obj.subcategory_name = self.validated_data["category"]
        obj.subcategory_description = self.validated_data["description"]
        obj.save()




from userapp.models import ReturnRefund
class ReturnRefundSerializer(serializers.ModelSerializer):
    class Meta:
        model=ReturnRefund
        fields=['id','status','approved_refund_amount']


class BillUserSerializer(serializers.ModelSerializer):
    class Meta:
        model=CustomUser
        fields=['id','first_name','last_name']


from userapp.models import OrderLine
class OrderLineSerializer(serializers.ModelSerializer):
    seller=BillUserSerializer(read_only=True)
    class Meta:
        model = OrderLine
        fields = ['seller']

class BillShopOrderSerializer(serializers.ModelSerializer):
    user = BillUserSerializer(read_only=True)
    returns = ReturnRefundSerializer(many=True, read_only=True)  
    order_lines=OrderLineSerializer(many=True, read_only=True)

    class Meta:
        model = ShopOrder
        fields = ['id','user', 'order_date', 'returns','order_lines']


class BillPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['platform_fee']


from userapp.models import Bill
class BillRevenueSerializer(serializers.ModelSerializer):
    order=BillShopOrderSerializer(read_only=True)
    payment=BillPaymentSerializer(read_only=True)
    
    class Meta:
        model=Bill
        fields=['id','invoice_number','payment_status','total_amount','order','payment']
    



from rest_framework import serializers


from rest_framework import serializers

class OrderlinesSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderLine
        fields = ['id', 'quantity']


class ShopOrdersSerializer(serializers.ModelSerializer):
    order_lines = OrderlinesSerializer(many=True)

    class Meta:
        model = ShopOrder
        fields = ['order_lines']


class SalesTrendsSerializer(serializers.ModelSerializer):
    category_sales = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    orders = serializers.SerializerMethodField()

    class Meta:
        model = Bill
        fields = ['id', 'bill_date', 'total_amount', 'category_sales', 'category_name', 'orders']

    def get_orders(self, obj):
        """
        Retrieve related orders from the Bill instance.
        Assumes a relationship between Bill and ShopOrder via an `order` field.
        """
        if hasattr(obj, 'order'):
            return ShopOrdersSerializer(obj.order, many=False).data
        return None

    def get_category_sales(self, obj):
        """
        Calculate the number of sales (total quantity sold) grouped by product category.
        """
        category_sales = {}
        if hasattr(obj, 'order'):
            order_lines = obj.order.order_lines.select_related(
                'product_item__product__category'
            )
            for order_line in order_lines:
                category_name = order_line.product_item.product.category.category_name
                category_sales[category_name] = (
                    category_sales.get(category_name, 0) + order_line.quantity
                )
        return category_sales

    def get_category_name(self, obj):
        """
        Get a list of unique category and product names from the order lines.
        """
        unique_names = {"categories": set(), "products": set()}
        if hasattr(obj, 'order'):
            order_lines = obj.order.order_lines.select_related(
                'product_item__product__category'
            )
            for order_line in order_lines:
                # Add category and product names to respective sets
                unique_names["categories"].add(order_line.product_item.product.category.category_name)
                unique_names["products"].add(order_line.product_item.product.product_name)
        return {
            "categories": list(unique_names["categories"]),
            "products": list(unique_names["products"]),
        }



from common.models import Seller
from rest_framework import serializers

class SellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seller
        fields = ['shop_name', 'rating', 'products_sold']

class TopSellerSerializer(serializers.Serializer):
    seller = SellerSerializer()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_orders = serializers.IntegerField()
    shop_name = serializers.CharField(source='seller.shop_name')