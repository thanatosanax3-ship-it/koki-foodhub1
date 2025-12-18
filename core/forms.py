
from django import forms
from .models import Product, InventoryItem, Sale

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "category", "price", "image", "size"]
        widgets = {
            "name": forms.TextInput(attrs={"class":"input", "placeholder":"Item name"}),
            "category": forms.TextInput(attrs={"class":"input", "placeholder":"Select category"}),
            "price": forms.NumberInput(attrs={"class":"input","step":"0.01"}),
            "image": forms.FileInput(attrs={"class":"input", "accept":"image/*"}),
            "size": forms.Select(attrs={"class":"input"}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make image field explicitly optional
        self.fields['image'].required = False
    
    def clean_image(self):
        """Validate image upload"""
        image = self.cleaned_data.get('image')
        if image:
            # Check file size (5MB limit)
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Image size must be less than 5MB.")
            # Check file extension
            allowed_extensions = ['jpg', 'jpeg', 'png', 'gif']
            file_extension = image.name.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                raise forms.ValidationError(f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}")
        return image

class InventoryForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ["product", "sku", "quantity", "reorder_point"]
        widgets = {
            "product": forms.Select(attrs={"class":"input"}),
            "sku": forms.TextInput(attrs={"class":"input"}),
            "quantity": forms.NumberInput(attrs={"class":"input"}),
            "reorder_point": forms.NumberInput(attrs={"class":"input"}),
        }

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ["product", "date", "units_sold", "revenue"]
        widgets = {
            "product": forms.Select(attrs={"class":"input"}),
            "date": forms.DateInput(attrs={"class":"input","type":"date"}),
            "units_sold": forms.NumberInput(attrs={"class":"input"}),
            "revenue": forms.NumberInput(attrs={"class":"input","step":"0.01"}),
        }
